"""Minimal async client for the CCEI BRiO WiL controller (no HA imports)."""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5.0
FIRST_READ_TIMEOUT = 3.0   # wait this long for the device to start replying
IDLE_READ_TIMEOUT = 0.5    # then stop once it has been quiet this long

POWER_OFF = 0
POWER_ON = 2


class BrioError(Exception):
    """Communication or parsing error."""


@dataclass
class BrioStatus:
    """Decoded controller state."""

    power_state: int          # 0 = off, 2 = on (other values seen as transitional)
    mode: int | None          # colour / sequence id
    speed: int | None         # 0..2
    level: int | None         # 0..3 (brightness)

    @property
    def is_on(self) -> bool:
        return self.power_state != POWER_OFF


def parse_status(text: str) -> BrioStatus:
    """Decode the status string using the same offsets as the Node-RED flow."""
    if len(text) < 72:
        raise BrioError(f"Status response too short ({len(text)} chars)")
    try:
        power = int(text[33:34])
    except ValueError as err:
        raise BrioError("Cannot decode power state") from err

    def _hex(chunk: str) -> int | None:
        try:
            return int(chunk, 16)
        except ValueError:
            return None

    mode = _hex(text[64:66])
    speed_raw = _hex(text[70:71])
    level_raw = _hex(text[71:72])

    speed = speed_raw - 4 if speed_raw is not None else None
    level = level_raw // 4 if level_raw is not None and level_raw % 4 == 0 else None
    if speed is not None and not 0 <= speed <= 2:
        speed = None
    if level is not None and not 0 <= level <= 3:
        level = None
    return BrioStatus(power_state=power, mode=mode, speed=speed, level=level)


class BrioClient:
    """Talks to the controller; one connection at a time."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._lock = asyncio.Lock()

    async def _exchange(self, payload: str | None) -> str:
        """Open a connection, optionally send payload, return whatever comes back."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), CONNECT_TIMEOUT
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise BrioError(f"Cannot connect to {self._host}:{self._port}: {err}") from err

        data = b""
        try:
            if payload:
                writer.write(payload.encode())
                await writer.drain()
            timeout = FIRST_READ_TIMEOUT
            while True:
                try:
                    chunk = await asyncio.wait_for(reader.read(1024), timeout)
                except asyncio.TimeoutError:
                    break
                if not chunk:
                    break
                data += chunk
                timeout = IDLE_READ_TIMEOUT
        except OSError as err:
            raise BrioError(f"Communication error: {err}") from err
        finally:
            writer.close()
            with contextlib.suppress(OSError, asyncio.TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), 2)
        text = data.decode("utf-8", errors="ignore")
        _LOGGER.debug("TX %r RX %r", payload, text)
        return text

    async def async_get_status(self) -> BrioStatus:
        async with self._lock:
            return parse_status(await self._exchange(None))

    async def _send(self, key: str, value: int) -> None:
        await self._exchange(json.dumps({key: value}, separators=(",", ":")))

    async def async_set_mode(self, mode: int) -> None:
        async with self._lock:
            await self._send("prcn", mode)

    async def async_set_level(self, level: int) -> None:
        async with self._lock:
            await self._send("plum", level)

    async def async_set_speed(self, speed: int) -> None:
        async with self._lock:
            await self._send("pspd", speed)

    async def async_set_power(self, on: bool) -> None:
        """The device only has a toggle command, so read state first."""
        async with self._lock:
            status = parse_status(await self._exchange(None))
            if on and status.power_state == POWER_OFF:
                await self._send("sprj", 1)
            elif not on and status.power_state == POWER_ON:
                await self._send("sprj", 0)
