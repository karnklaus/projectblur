# Third-party notices

## Microsoft Windows Camera sample

ProjectBlur's files under `media_source/` started from a selected subset of the
Microsoft Windows Camera `Samples/VirtualCamera/VirtualCameraMediaSource`
sample at commit `790ac218eba8b6995393e9cc9537dfd7730fdb83`:

- `pch.h` and `pch.cpp`
- `SimpleMediaSource.h` and `SimpleMediaSource.cpp`
- `SimpleMediaStream.h` and `SimpleMediaStream.cpp`
- `SimpleFrameGenerator.h` and `SimpleFrameGenerator.cpp`
- `VirtualCameraMediaSourceActivate.h` and
  `VirtualCameraMediaSourceActivate.cpp`
- `VirtualCameraMediaSource.h`
- `dllmain.cpp`
- `winrtCommon.cpp`

ProjectBlur changed identifiers, removed unrelated hardware/augmented-camera
paths, added the shared-memory reader, full-resolution BGRA conversion, frame
metadata, 720p/1080p media types, and high-resolution pacing. The entire
external repository was not copied into ProjectBlur.

Upstream: <https://github.com/microsoft/Windows-Camera>

License: MIT. The complete upstream license text is preserved in
`LICENSE.microsoft-windows-camera.txt`. Microsoft retains copyright in the
adapted sample code; those files are not represented as original ProjectBlur
code.
