# Windows 11 Media Foundation Virtual Camera Reference

## Status

- ProjectBlur status: Current synthetic native-output prototype; integrated
  capture, target-app compatibility, and release packaging pending
- Platform: Windows 11 build 22000 or newer
- Reviewed: 2026-07-16

## Primary Sources

- Microsoft `MFCreateVirtualCamera` API documentation:
  https://learn.microsoft.com/windows/win32/api/mfvirtualcamera/nf-mfvirtualcamera-mfcreatevirtualcamera
- Microsoft Windows Camera Virtual Camera sample:
  https://github.com/microsoft/Windows-Camera/tree/master/Samples/VirtualCamera
- Reference commit reviewed:
  `790ac218eba8b6995393e9cc9537dfd7730fdb83`

## Findings

`MFCreateVirtualCamera` registers a software camera backed by a custom Media
Foundation media source. The API supports current-user camera access and
requires Windows build 22000 or newer. Actual implementation showed that the
out-of-process Camera Frame Server cannot activate an HKCU-only COM source, so
ProjectBlur keeps camera access current-user scoped while registering its CLSID
machine-wide through an elevated installer (`DEC-008`). Microsoft publishes a
complete sample covering a media-source DLL, registration, removal, management,
and tests.

ProjectBlur did not copy the external repository into `src` or ship the sample
unchanged. A selected SimpleMediaSource subset was adapted under
`native/virtual_camera/media_source`; exact files, commit, changes, copyright,
and the MIT text are preserved beside it. ProjectBlur-owned transport and
conversion code reads anonymized BGRA frames instead of generating the sample's
synthetic frames or wrapping an unprocessed physical camera.

## License and Redistribution

The reviewed Microsoft repository declares the MIT License. Any source derived
from that sample must retain its copyright and license notice. Microsoft Visual
Studio Build Tools, the Windows SDK, C++/WinRT, and WIL are development inputs;
their licenses and redistribution terms must be reviewed again before packaging
release binaries. The adapted source and complete notice are documented in
`native/virtual_camera/THIRD_PARTY_NOTICES.md` and
`native/virtual_camera/LICENSE.microsoft-windows-camera.txt`.

## Remaining Validation

- Confirm clean removal on the development machine.
- Verify enumeration and streaming in Windows Camera, Zoom, Meet, and Teams.
- Repeat 720p/1080p measurements with authorized integrated webcam and screen
  ingestion plus CPU and RAM telemetry.
- Verify detector-error and stale-frame behavior in the integrated runtime.
- Define code-signing and installer requirements before distribution.
