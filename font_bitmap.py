#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import re
import sys
import importlib

def question(text, default, type=int):
    while True:
        try:
            return type(input(f"{text} [{default}]: ").strip() or default)
            break
        except Exception as e:
            print(e)

def utf8_to_uint16(utf8_data):  # or python ord function
    utf8_bytes = utf8_data if utf8_bytes_string.isinstance(bytes) else str(utf8_data)[:1].encode('utf-8')
    qtd_bytes = (1 if utf8_bytes[0] & 0x80 == 0x00 else
                 2 if utf8_bytes[0] & 0xE0 == 0xC0 else
                 3 if utf8_bytes[0] & 0xF0 == 0xE0 else
                 4 if utf8_bytes[0] & 0xF8 == 0xF0 else
                 0)
    assert qtd_bytes > 1, Exception("UTF-8 bytes error!")
    if qtd_bytes == 1:
        return utf8_bytes[0] & 0x7F
    elif qtd_bytes == 2:
        return ((utf8_bytes[0] & 0x1F) << 6) | (utf8_bytes[1] & 0x3F)
    elif qtd_bytes == 3:
        return ((utf8_bytes[0] & 0x0F) << 12) | ((utf8_bytes[1] & 0x3F) << 6) | (utf8_bytes[2] & 0x3F)
    elif qtd_bytes == 4:
        CP = ((utf8_bytes[0] & 0x07) << 18) | ((utf8_bytes[1] & 0x3F) << 12) | ((utf8_bytes[2] & 0x3F) << 6) | (utf8_bytes[3] & 0x3F)
        CP -= 0x10000
        highSurrogate = 0xD800 + ((CP >> 10) & 0x3FF)
        lowSurrogate = 0xDC00 + (CP & 0x3FF)
        return (highSurrogate << 16) | lowSurrogate

default = "Orbitron_Medium_20.h" if len(sys.argv) == 1 else sys.argv[1]
file_path = question("File path", default, str)
with open(file_path, encoding="utf-8") as fd:
    h_font = fd.read()

py_font = h_font.replace("//", "#").replace("};", "]", 1)
py_font = re.sub(r".*{\n", "bitmaps = [\n", py_font)
py_font = re.sub(r".*Glyphs\[\].*", "glyphs = {", py_font)
py_font = re.sub(r".*(GFXfont|GFXglyph).*", "", py_font)
py_font = re.sub(r"[\t ]+\{([^}\n]+)\}[, /#]+('[^\n]*')", r"    \2: [\1],  # ", py_font).replace("'''", '"\'"').replace("'\\'", "'\\\\'")

with open("font.py", "w", encoding="utf-8") as fd:
    fd.write(py_font)

font = importlib.import_module("font")

try:
    font.glyphs
except AttributeError:
    print("No font map of glyphs found, enter fixed values for all itens")
    width = question("Width", 8)
    height = question("Height", 5)
    first_char = question("First character code", 0)
    code_page = question("Codepage", "CP437", str)
    size_bytes = (width * height + 7) // 8
    font.glyphs = {(first_char + i).to_bytes().decode(code_page):
                        (size_bytes * i, width, height, 0, 0, 0)
                   for i in range(len(font.bitmaps) // size_bytes)}

show_symbol = input("Symbol to show [Enter for all]: ").strip()[:1]

_hex = lambda i: hex(i).upper().replace('X', 'x')

i = -1
for c, (offset, width, height, xAdvance, xOffset, yOffset) in font.glyphs.items():
    i += 1
    next_offset = offset + (width * height + 7) // 8
    if show_symbol and c != show_symbol:
        continue
    bits = font.bitmaps[offset:next_offset]
    bits_str = "".join(f"{b:08b}" for b in bits)[:width * height]
    info = {"offset": offset, "width": width, "height": height,
            "xAdvance": xAdvance, "xOffset": xOffset, "yOffset": yOffset}
    print("_" * 100)
    print(f"{info}")
    print("-" * 100)
    print(f"{code_page}: {repr(c)} {i} {_hex(i)}  ===>  unicode: {ord(c)} - {_hex(ord(c))}\n")
    bits_matrix = [bits_str[i * width:(i + 1) * width] for i in range(height)]
    for line in bits_matrix:
        print(line.replace("0", " ").replace("1", "█"), line)

print("\n\n______ Create a symbol ______")

symbol_bits = []
while (bits_line := input("Bits line: ")):
    symbol_bits.append(bits_line.replace(" ", "0").replace("█", "1"))

if not symbol_bits:
    sys.exit(0)

width = question("Width", max(map(len, symbol_bits)))
symbol_bits = [(bits + "0" * width)[:width] for bits in symbol_bits]

height = question("Height", len(symbol_bits))
if height > len(symbol_bits):
    symbol_bits.extend(["0" * width] * h - len(symbol_bits))

xAdvance = question("xAdvance", width + 2)
xOffset = question("xOffset", 1)
yOffset = question("yOffset", -height)
symbol_utf8 = question("symbol (utf-8 char)", "×", str)
symbol_unicode = ord(symbol_utf8)
symbol_hex = hex(symbol_unicode).upper().replace('X', 'x')

print("_" * 100, end="\n\n")

bits_sequence = ("".join(symbol_bits) + "0" * 7)[:(width * height + 7) // 8 * 8]
hex_list = [hex(int(bits_sequence[i * 8: (i + 1) * 8], 2)).upper().replace("X", "x")
            for i in range(len(bits_sequence) // 8)]
bitmap_line = f"{','.join(hex_list)}, // '{symbol_utf8}'"
print("Bitmaps line (added at the end of bitmaps):")
print(f"\t{bitmap_line}")

glyph_line = (f"{{ {len(font.bitmaps):5d},{width:4d},{height:4d},{xAdvance:4d},"
              f"{xOffset:5d},{yOffset:5d} }}, // '{symbol_utf8}' {symbol_hex}")
print(f"\nGlyphs line (added at {symbol_hex} - {symbol_unicode} position):")
print(f"\t{glyph_line}")

print("_" * 100, end="\n\n")

h_font = h_font.strip().split('\n')
new_h_font = []

while h_font:
    line = h_font.pop(0)
    if line.strip() != '};':
        new_h_font.append(line)
    else:
        break

if new_h_font[-1].rstrip()[-1] != "," and not re.match(r".*,\s*//", new_h_font[-1]):
    new_h_font[-1] = re.sub(r"^(.+,\s*0x[A-Fa-f\d]{1,2})(.*)", r"\1,\2", new_h_font[-1])

indentation = re.sub(r"^(\s*).*$", r"\1", new_h_font[-1])
new_h_font.append(f"{indentation}{bitmap_line}")
new_h_font.append(line)

while h_font:
    line = h_font.pop(0)
    if line.lstrip()[:1] != '{':
        new_h_font.append(line)
    else:
        break

glyphs = [line]
while h_font:
    line = h_font.pop(0)
    if line.lstrip()[:1] == '{':
        glyphs.append(line)
    else:
        break

if glyphs[-1].rstrip()[-1] != "," and not re.match(r".*,\s*//", glyphs[-1]):
    glyphs[-1] = re.sub(r"^(\s*\{[ \d,-]+\})(.*)", r"\1,\2", glyphs[-1])

glyph_placeholder = re.sub("'.*'.*", "''", re.sub(r"0(?=0)", " ", re.sub(r"\d", "0", glyphs[0])))
indentation = re.sub(r"^(\s*).*$", r"\1", glyphs[0])
_declaration, _first, _last, _yAdvance = "\n".join(h_font).rsplit(",", 3)
first = int(_first.strip(), 16 if _first.strip()[:2] == "0x" else 10)
if first > symbol_unicode:
    for i in range(first - symbol_unicode - 1):
        glyphs.insert(0, glyph_placeholder)
    glyphs.insert(0, f"{indentation}{glyph_line}")
    first = symbol_hex
    last = _last.strip()
elif symbol_unicode > len(glyphs) + first - 1:
    for i in range(symbol_unicode - len(glyphs) - first):
        glyphs.append(glyph_placeholder)
    glyphs.append(f"{indentation}{glyph_line}")
    first = _first.strip()
    last = symbol_hex
else:
    glyphs[symbol_unicode - first] = f"{indentation}{glyph_line}"
    first = _first.strip()
    last = _last.strip()

lf = '\n'
new_h_font = (f"{lf.join(new_h_font)}\n{lf.join(glyphs)}\n{line}\n"
              f"{', '.join((_declaration, first, last, _yAdvance.lstrip(' ')))}\n")

# print(new_h_font)

with open(file_path, "w", encoding="utf-8") as fd:
    fd.write(new_h_font)
