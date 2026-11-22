#!/usr/bin/env python3
"""Verificación independiente (zbar, C) de las etiquetas QR de SILBOM.

Exige que cada PNG contenga exactamente un QR cuyo texto sea su identificador
de máquina, sin URL ni datos adicionales. Requiere libzbar0 y Pillow.
Uso: python3 scripts/qr/verificar_qr_zbar.py docs/qr
"""
import ctypes
import ctypes.util
import re
import sys
from pathlib import Path

from PIL import Image

EXPECTED = ["EQ-COM-03", "EQ-ENV-01", "EQ-EXT-02"]
PATTERN = re.compile(r"^EQ-[A-Z]{2,4}-[0-9]{2}$")
ZBAR_QRCODE = 64
ZBAR_CFG_ENABLE = 0


def load_zbar():
    name = ctypes.util.find_library("zbar") or "libzbar.so.0"
    lib = ctypes.CDLL(name)
    lib.zbar_image_scanner_create.restype = ctypes.c_void_p
    lib.zbar_image_create.restype = ctypes.c_void_p
    lib.zbar_image_first_symbol.restype = ctypes.c_void_p
    lib.zbar_symbol_next.restype = ctypes.c_void_p
    lib.zbar_symbol_get_data.restype = ctypes.c_char_p
    lib.zbar_symbol_get_data_length.restype = ctypes.c_uint
    for fn in ("zbar_image_scanner_set_config", "zbar_scan_image", "zbar_image_set_format",
               "zbar_image_set_size", "zbar_image_set_data", "zbar_symbol_get_type",
               "zbar_image_first_symbol", "zbar_symbol_next", "zbar_symbol_get_data",
               "zbar_symbol_get_data_length", "zbar_image_destroy", "zbar_image_scanner_destroy"):
        getattr(lib, fn).argtypes = None
    return lib


def decode(lib, path):
    gray = Image.open(path).convert("L")
    width, height = gray.size
    raw = gray.tobytes()
    buf = ctypes.create_string_buffer(raw, len(raw))
    scanner = ctypes.c_void_p(lib.zbar_image_scanner_create())
    lib.zbar_image_scanner_set_config(scanner, 0, ZBAR_CFG_ENABLE, 0)          # desactiva todo
    lib.zbar_image_scanner_set_config(scanner, ZBAR_QRCODE, ZBAR_CFG_ENABLE, 1)  # solo QR
    image = ctypes.c_void_p(lib.zbar_image_create())
    lib.zbar_image_set_format(image, ctypes.c_ulong(0x30303859))  # fourcc 'Y800'
    lib.zbar_image_set_size(image, ctypes.c_uint(width), ctypes.c_uint(height))
    lib.zbar_image_set_data(image, buf, ctypes.c_ulong(len(raw)), None)
    lib.zbar_scan_image(scanner, image)
    found = []
    symbol = lib.zbar_image_first_symbol(image)
    while symbol:
        symbol = ctypes.c_void_p(symbol)
        length = lib.zbar_symbol_get_data_length(symbol)
        data = ctypes.string_at(lib.zbar_symbol_get_data(symbol), length)
        found.append((lib.zbar_symbol_get_type(symbol), data))
        symbol = lib.zbar_symbol_next(symbol)
    lib.zbar_image_destroy(image)
    lib.zbar_image_scanner_destroy(scanner)
    return found


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/qr")
    lib = load_zbar()
    for code in EXPECTED:
        path = folder / f"QR-{code}.png"
        found = decode(lib, path)
        assert len(found) == 1, f"{path}: se esperaba 1 QR, zbar encontró {len(found)}"
        kind, data = found[0]
        assert kind == ZBAR_QRCODE, f"{path}: símbolo no QR ({kind})"
        assert data == code.encode("ascii"), f"{path}: contiene {data!r}"
        assert PATTERN.fullmatch(data.decode("ascii")) and b"://" not in data
        print(f"zbar: {path.name} -> {data.decode()!r} OK ({len(data)} bytes, sin URL)")


if __name__ == "__main__":
    main()
