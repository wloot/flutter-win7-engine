#!/usr/bin/env python3
"""Stamp the DLL's PE version floor to 6.1 (Windows 7) and fix the checksum.

Informational only: a real-machine A/B (2026-08-30, same DLL restamped
10.0 loaded fine on Win7) proved the loader checks version stamps on
EXEs, never on DLLs. The 6.1 stamp stays because it is free and makes
the artifact's self-described floor match what it actually supports -
not because any loader reads it.
"""

import struct
import sys

import pefile


def main(path: str) -> int:
    data = bytearray(open(path, 'rb').read())
    pe_off = struct.unpack_from('<I', data, 0x3c)[0]
    opt = pe_off + 24
    if struct.unpack_from('<H', data, opt)[0] != 0x20b:
        print('not a PE32+ image', file=sys.stderr)
        return 2
    # MajorOSVersion@40, MinorOSVersion@42, MajorSubsystemVersion@48,
    # MinorSubsystemVersion@50, CheckSum@64.
    for off, val in [(40, 6), (42, 1), (48, 6), (50, 1)]:
        struct.pack_into('<H', data, opt + off, val)
    open(path, 'wb').write(data)

    pe = pefile.PE(path)
    checksum = pe.generate_checksum()
    pe.close()
    struct.pack_into('<I', data, opt + 64, checksum)
    open(path, 'wb').write(data)

    v = pefile.PE(path)
    oh = v.OPTIONAL_HEADER
    ok = (oh.MajorOperatingSystemVersion, oh.MinorOperatingSystemVersion,
          oh.MajorSubsystemVersion, oh.MinorSubsystemVersion) == (6, 1, 6, 1) \
        and oh.CheckSum == v.generate_checksum()
    v.close()
    print('stamped 6.1, checksum %#x, verified %s' % (checksum, ok))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1]))
