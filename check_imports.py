#!/usr/bin/env python3
"""Fail if the built DLL statically imports anything Windows 7 cannot resolve.

CRT apisets (api-ms-win-crt-*) pass: they are satisfied by the UCRT
(KB2999226 / VC++ redist) on Windows 7. Everything else in the api-ms-win-* /
ext-ms-win-* namespaces, and the known Win8+ symbols below, fails the build.
"""

import sys

import lief

WIN8_PLUS = {
    "GetHostNameW",
    "GetCurrentThreadStackLimits",
    "RtlAddGrowableFunctionTable",
    "RtlDeleteGrowableFunctionTable",
    "PathAllocCanonicalize",
    "PathCchCombineEx",
    "PathCchRemoveFileSpec",
    "WaitOnAddress",
    "WakeByAddressSingle",
}


def main(path: str) -> int:
    pe = lief.PE.parse(path)
    if pe is None:
        print(f"cannot parse {path}", file=sys.stderr)
        return 2
    bad = []
    for imp in pe.imports:
        lib = (imp.name or "").lower()
        crt = lib.startswith("api-ms-win-crt-")
        os_apiset = not crt and (
            lib.startswith("api-ms-win-") or lib.startswith("ext-ms-win-")
        )
        for entry in imp.entries:
            if entry.is_ordinal:
                continue
            sym = entry.name or ""
            if sym in WIN8_PLUS or os_apiset:
                bad.append(f"{lib}!{sym}")
    for lib in sorted({(i.name or "").lower() for i in pe.imports}):
        print("import:", lib)
    if bad:
        print("FAIL: Win7-unresolvable imports remain:")
        for b in sorted(bad):
            print(" ", b)
        return 1
    print("OK: no Win8+ static imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
