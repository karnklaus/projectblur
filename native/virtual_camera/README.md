# ProjectBlur Windows virtual camera

This directory contains ProjectBlur's Windows 11 x64 Media Foundation virtual
camera prototype. It is a user-mode software camera, not a kernel driver. The
source reads the newest full-resolution BGRA frame from a per-user global named
mapping and exposes 1280x720 or 1920x1080 output as NV12 or RGB32 at 30 FPS.

The Media Foundation base source is a selectively adapted subset of Microsoft's
Windows Camera sample. See `THIRD_PARTY_NOTICES.md` and
`LICENSE.microsoft-windows-camera.txt`.

## Build and install

Requirements: Windows 11 build 22000 or newer, Visual Studio 2022 Build Tools
with Desktop development with C++, Windows SDK 10.0.26100, and NuGet CLI.

```powershell
.\scripts\build_virtual_camera.ps1
Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList @(
  '-NoProfile', '-ExecutionPolicy', 'Bypass',
  '-File', (Resolve-Path '.\scripts\install_virtual_camera.ps1').Path
)
```

The installer copies the native binaries to
`C:\Program Files\ProjectBlur\VirtualCamera`, registers only ProjectBlur's COM
CLSID, and registers `ProjectBlur Camera (Windows Virtual Camera)` for the
current user. It briefly restarts the Windows Camera Frame Server when replacing
an in-use DLL.

Remove the camera from an elevated PowerShell session:

```powershell
.\scripts\remove_virtual_camera.ps1
```

The installed DLL is currently unsigned. Compatibility must be verified per
target application before any release claim. The browser preview does not yet
publish its anonymized canvas into this camera; the Python frame bridge and
benchmark are the implemented producer paths.
