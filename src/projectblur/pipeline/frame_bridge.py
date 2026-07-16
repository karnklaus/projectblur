"""Versioned shared-memory transport for anonymized BGRA frames."""

from __future__ import annotations

from dataclasses import dataclass
import os
from multiprocessing import shared_memory
import struct
from threading import Lock
from time import monotonic_ns

import numpy as np
from numpy.typing import NDArray

MAGIC = b"PBLURF01"
PROTOCOL_VERSION = 1
BGRA32 = 1
HEADER = struct.Struct("<8sIIQIIIIQQ")
SEQUENCE_OFFSET = 16
SEQUENCE = struct.Struct("<Q")


class _WindowsNamedMapping:
    """Open an existing Windows mapping without requesting all-access rights."""

    def __init__(self, name: str):
        import _winapi
        import ctypes

        access = _winapi.FILE_MAP_READ | _winapi.FILE_MAP_WRITE
        self._winapi = _winapi
        self._handle = _winapi.OpenFileMapping(access, False, name)
        try:
            self._view = _winapi.MapViewOfFile(
                self._handle,
                access,
                0,
                0,
                0,
            )
        except BaseException:
            _winapi.CloseHandle(self._handle)
            raise
        self._size = _winapi.VirtualQuerySize(self._view)
        array_type = ctypes.c_ubyte * self._size
        self._array = array_type.from_address(self._view)
        self.buf = memoryview(self._array).cast("B")
        self.name = name

    def close(self) -> None:
        """Release the mapped view and its Windows handle."""
        if self._view:
            self.buf.release()
            self._winapi.UnmapViewOfFile(self._view)
            self._view = 0
        if self._handle:
            self._winapi.CloseHandle(self._handle)
            self._handle = 0


@dataclass(frozen=True)
class PublishedFrame:
    """A stable copy of the newest frame in the shared-memory transport."""

    pixels: NDArray[np.uint8]
    sequence: int
    timestamp_ns: int


class FramePublisher:
    """Publish latest-only BGRA frames for a native virtual-camera reader."""

    def __init__(
        self,
        *,
        max_width: int,
        max_height: int,
        name: str | None = None,
        create: bool = True,
    ):
        if max_width <= 0 or max_height <= 0:
            raise ValueError("maximum frame dimensions must be greater than zero")
        if not create and not name:
            raise ValueError("name is required when opening an existing mapping")
        self._capacity = max_width * max_height * 4
        if not create and os.name == "nt":
            assert name is not None
            self._memory = _WindowsNamedMapping(name)
        else:
            self._memory = shared_memory.SharedMemory(
                name=name,
                create=create,
                size=HEADER.size + self._capacity if create else 0,
            )
        self._lock = Lock()
        self._owns_mapping = create
        if create:
            self._sequence = 0
            HEADER.pack_into(
                self._memory.buf,
                0,
                MAGIC,
                HEADER.size,
                PROTOCOL_VERSION,
                self._sequence,
                0,
                0,
                0,
                BGRA32,
                0,
                0,
            )
        else:
            if len(self._memory.buf) < HEADER.size + self._capacity:
                self._memory.close()
                raise ValueError("existing mapping is smaller than the requested capacity")
            header = HEADER.unpack_from(self._memory.buf, 0)
            magic, header_size, version, sequence, _, _, _, pixel_format, _, _ = (
                header
            )
            if magic != MAGIC or header_size != HEADER.size:
                self._memory.close()
                raise RuntimeError("shared-memory frame header is invalid")
            if version != PROTOCOL_VERSION or pixel_format != BGRA32:
                self._memory.close()
                raise RuntimeError("shared-memory frame protocol is unsupported")
            self._sequence = sequence if sequence % 2 == 0 else sequence + 1

    @property
    def name(self) -> str:
        """Return the operating-system shared-memory name."""
        return self._memory.name

    def publish(
        self,
        frame: NDArray[np.uint8],
        *,
        timestamp_ns: int | None = None,
    ) -> int:
        """Atomically replace the latest frame and return its even sequence."""
        _validate_bgra_frame(frame)
        contiguous = np.ascontiguousarray(frame)
        height, width = contiguous.shape[:2]
        stride = width * 4
        payload = contiguous.view(np.uint8).reshape(-1)
        if payload.nbytes > self._capacity:
            raise ValueError("frame exceeds the shared-memory capacity")

        with self._lock:
            writing_sequence = self._sequence + 1
            completed_sequence = writing_sequence + 1
            HEADER.pack_into(
                self._memory.buf,
                0,
                MAGIC,
                HEADER.size,
                PROTOCOL_VERSION,
                writing_sequence,
                width,
                height,
                stride,
                BGRA32,
                monotonic_ns() if timestamp_ns is None else timestamp_ns,
                payload.nbytes,
            )
            self._memory.buf[HEADER.size : HEADER.size + payload.nbytes] = payload
            SEQUENCE.pack_into(self._memory.buf, SEQUENCE_OFFSET, completed_sequence)
            self._sequence = completed_sequence
            return completed_sequence

    def close(self) -> None:
        """Close this process's handle without removing the mapping."""
        self._memory.close()

    def unlink(self) -> None:
        """Remove the mapping name after all readers have closed it."""
        if not self._owns_mapping:
            raise RuntimeError("cannot unlink a mapping opened by another owner")
        self._memory.unlink()

    def __enter__(self) -> FramePublisher:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class FrameSubscriber:
    """Read stable latest-frame copies from a ProjectBlur frame mapping."""

    def __init__(self, name: str):
        self._memory = shared_memory.SharedMemory(name=name, create=False)

    def read_latest(self, *, attempts: int = 3) -> PublishedFrame | None:
        """Return a consistent frame, or ``None`` before the first publish."""
        if attempts <= 0:
            raise ValueError("attempts must be greater than zero")
        for _ in range(attempts):
            header = HEADER.unpack_from(self._memory.buf, 0)
            (
                magic,
                header_size,
                version,
                sequence_before,
                width,
                height,
                stride,
                pixel_format,
                timestamp_ns,
                payload_size,
            ) = header
            if magic != MAGIC or header_size != HEADER.size:
                raise RuntimeError("shared-memory frame header is invalid")
            if version != PROTOCOL_VERSION or pixel_format != BGRA32:
                raise RuntimeError("shared-memory frame protocol is unsupported")
            if sequence_before == 0:
                return None
            if sequence_before % 2:
                continue
            expected_size = stride * height
            if width <= 0 or height <= 0 or stride != width * 4:
                raise RuntimeError("shared-memory frame dimensions are invalid")
            if payload_size != expected_size:
                raise RuntimeError("shared-memory frame payload size is invalid")
            end = HEADER.size + payload_size
            if end > len(self._memory.buf):
                raise RuntimeError("shared-memory frame exceeds its mapping")
            payload = bytes(self._memory.buf[HEADER.size:end])
            sequence_after = SEQUENCE.unpack_from(
                self._memory.buf,
                SEQUENCE_OFFSET,
            )[0]
            if sequence_before == sequence_after and sequence_after % 2 == 0:
                pixels = np.frombuffer(payload, dtype=np.uint8).reshape(
                    height,
                    width,
                    4,
                )
                return PublishedFrame(
                    pixels=pixels,
                    sequence=sequence_after,
                    timestamp_ns=timestamp_ns,
                )
        return None

    def close(self) -> None:
        """Close this process's handle to the mapping."""
        self._memory.close()

    def __enter__(self) -> FrameSubscriber:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def _validate_bgra_frame(frame: NDArray[np.uint8]) -> None:
    if not isinstance(frame, np.ndarray):
        raise TypeError("frame must be a NumPy array")
    if frame.dtype != np.uint8:
        raise ValueError("frame must use uint8 pixels")
    if frame.size == 0 or frame.ndim != 3 or frame.shape[2] != 4:
        raise ValueError("frame must be a non-empty HxWx4 BGRA array")
