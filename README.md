# flutter-win7-engine

Builds a Windows 7-compatible `flutter_windows.dll` for **Flutter 3.44.9**
by patching the engine's third-party sources and rebuilding. The same DLL
runs unchanged on Windows 10/11: every patch resolves the missing API
dynamically and only falls back on Windows 7, so there is no separate Win7
artifact.

Stock Flutter ≥3.13 cannot start on Windows 7 because the engine statically
imports nine Win8+ symbols. Each was traced to its caller through the
official build's PDB:

| Symbol(s) | Caller | Fix |
|---|---|---|
| `GetCurrentThreadStackLimits` | `dart::OSThread::GetCurrentStackBounds` | restore the TEB + `VirtualQuery` implementation (pre [dart f94c325b]) |
| `GetHostNameW` | `dart::bin::Platform::LocalHostname` | restore ANSI `gethostname()` (pre [dart 35c6cc62]) |
| `RtlAddGrowableFunctionTable`, `RtlDeleteGrowableFunctionTable` | Dart unwinding records | restore the ntdll `GetProcAddress` shim removed in [dart 34213ba6]; on Win7 registration is skipped, Dart's original Win7 behavior |
| `PathAllocCanonicalize`, `PathCchCombineEx`, `PathCchRemoveFileSpec` | `runtime/bin/file_win.cc` (3 call sites) | resolve from KernelBase at runtime, string-handling fallback on Win7 — the two years of long-path/symlink fixes stay in place |
| `WaitOnAddress`, `WakeByAddressSingle` | ANGLE `SimpleMutex` (not Dart) | define ANGLE's own `ANGLE_WINDOWS_NO_FUTEX` escape hatch → `std::mutex` (SRWLock, Vista+) |

[dart f94c325b]: https://github.com/dart-lang/sdk/commit/f94c325bd1b1277c248c83e140a99f124d0a41f2
[dart 35c6cc62]: https://github.com/dart-lang/sdk/commit/35c6cc6234034c58a6af366048d43c4a16358f8f
[dart 34213ba6]: https://github.com/dart-lang/sdk/commit/34213ba60578e46fc2455c5a56b09d9efabc532b

The patches apply against the exact revisions Flutter 3.44.9's DEPS pins
(Dart `d684a576`, ANGLE `84027aca`).

## Building

Run the `build` workflow (manual dispatch). It checks out the engine source
via gclient, applies the patches, builds
`flutter/shell/platform/windows:flutter_windows` with the runner's VS
toolchain, verifies the produced DLL carries no Win8+ static import
(`check_imports.py`), and uploads the DLL + PDB as an artifact.

To use the result, overwrite
`<flutter-sdk>/bin/cache/artifacts/engine/windows-x64-release/flutter_windows.dll`
after `flutter precache` and build your app normally.

Note that the DLL is only one piece of running a Flutter app on Windows 7:
your installer's floor and whatever your own native code imports are yours
to handle.
