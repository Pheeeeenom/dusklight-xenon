"""
xbox_prompts.py <disc image> [output]: draws Xbox 360 button prompts over the GameCube ones and writes them as
src/dusk/xbox_prompts_data.inc, which src/dusk/xbox_prompts.cpp patches into the game's textures as they load.

Each entry keys an original texture on XXH64 of its image data, as the GameCube lays it out in blocks, with its size and
format, and holds new image data of the same size and format. The art is greyscale where the original is, as the
layouts tint it, except X and Y's bases: their art is coloured, in RGBA8, the patch points the texture at it, and
src/dusk/xbox_prompts.cpp turns the layouts' grey tints of them white, so they show as drawn. The face buttons take the
Xbox 360 controller's colours: A green, B red, X blue, Y amber; A's and X's (GameCube B's) are tints, set there. Prompts follow the Xbox 360 default map (extern/aurora/lib/dolphin/pad/pad.cpp,
g_defaultButtonsXBox360): GameCube B shows X, X shows B, Z shows RB, R shows RT, L LT, Start the 360's Start arrow, the
C-stick the right stick. Letters use res/FiraSansCondensed-Bold.ttf, which Dusklight ships.

Requires pillow.
"""

import os
import struct
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "res", "FiraSansCondensed-Bold.ttf")
SUPERSAMPLE = 4

# GX formats: (block width, block height, bits a texel).
I4, IA4, IA8, RGBA8 = 0, 2, 3, 6
BLOCKS = {0: (8, 8, 4), 1: (8, 4, 8), 2: (8, 4, 8), 3: (4, 4, 16), 4: (4, 4, 16), 5: (4, 4, 16), 6: (4, 4, 32),
          8: (8, 8, 4), 9: (8, 4, 8), 14: (8, 8, 4)}


def disc_files(disc):
    """The disc's files by path, from its FST (offset and size at 0x424)."""
    disc.seek(0x424)
    fst_offset, fst_size = struct.unpack(">II", disc.read(8))
    disc.seek(fst_offset)
    fst = disc.read(fst_size)
    count = struct.unpack_from(">I", fst, 8)[0]
    names = fst[count * 12:]
    files = {}

    def name_at(i):
        offset = struct.unpack_from(">I", fst, i * 12)[0] & 0xFFFFFF
        return names[offset:names.index(b"\0", offset)].decode("ascii", "replace")

    def walk(first, end, prefix):
        i = first
        while i < end:
            flags_name, a, b = struct.unpack_from(">III", fst, i * 12)
            if flags_name >> 24:
                walk(i + 1, b, prefix + name_at(i) + "/")
                i = b
            else:
                files[prefix + name_at(i)] = (a, b)
                i += 1

    walk(1, count, "")
    return files


def yaz0(data):
    if data[:4] != b"Yaz0":
        return data
    size = struct.unpack_from(">I", data, 4)[0]
    out = bytearray()
    i = 16
    while len(out) < size:
        code = data[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if code & (0x80 >> bit):
                out.append(data[i])
                i += 1
            else:
                b1, b2 = data[i], data[i + 1]
                i += 2
                distance = ((b1 & 0xF) << 8 | b2) + 1
                length = b1 >> 4
                if length == 0:
                    length = data[i] + 0x12
                    i += 1
                else:
                    length += 2
                for _ in range(length):
                    out.append(out[-distance])
    return bytes(out)


def rarc_files(data):
    """An archive's files by name, each decompressed."""
    data_offset = struct.unpack_from(">I", data, 0xC)[0] + 0x20
    _, _, entry_count, entry_offset, _, string_offset = struct.unpack_from(">IIIIII", data, 0x20)
    strings = 0x20 + string_offset
    files = {}
    for e in range(entry_count):
        _index, _hash, kind_name, offset, size = struct.unpack_from(">HHIII", data, 0x20 + entry_offset + e * 0x14)
        name_offset = kind_name & 0xFFFFFF
        name = data[strings + name_offset:data.index(b"\0", strings + name_offset)].decode("shift_jis", "replace")
        if kind_name >> 24 & 0x02 or name in (".", ".."):
            continue
        files[name] = yaz0(data[data_offset + offset:data_offset + offset + size])
    return files


M64 = (1 << 64) - 1
P1, P2, P3, P4, P5 = (0x9E3779B185EBCA87, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0x85EBCA77C2B2AE63,
                      0x27D4EB2F165667C5)


def rotl(x, r):
    return ((x << r) | (x >> (64 - r))) & M64


def xxh64(data, seed=0):
    """XXH64 as its reference specifies it, so the C++ side's XXH64 of the same bytes matches."""
    n = len(data)
    i = 0
    if n >= 32:
        v = [(seed + P1 + P2) & M64, (seed + P2) & M64, seed & M64, (seed - P1) & M64]
        while i + 32 <= n:
            for k in range(4):
                lane = struct.unpack_from("<Q", data, i + 8 * k)[0]
                v[k] = (rotl((v[k] + lane * P2) & M64, 31) * P1) & M64
            i += 32
        h = (rotl(v[0], 1) + rotl(v[1], 7) + rotl(v[2], 12) + rotl(v[3], 18)) & M64
        for k in range(4):
            h = ((h ^ (rotl((v[k] * P2) & M64, 31) * P1 & M64)) * P1 + P4) & M64
    else:
        h = (seed + P5) & M64
    h = (h + n) & M64
    while i + 8 <= n:
        lane = struct.unpack_from("<Q", data, i)[0]
        h ^= rotl((lane * P2) & M64, 31) * P1 & M64
        h = (rotl(h, 27) * P1 + P4) & M64
        i += 8
    if i + 4 <= n:
        h ^= (struct.unpack_from("<I", data, i)[0] * P1) & M64
        h = (rotl(h, 23) * P2 + P3) & M64
        i += 4
    while i < n:
        h ^= (data[i] * P5) & M64
        h = (rotl(h, 11) * P1) & M64
        i += 1
    h ^= h >> 33
    h = (h * P2) & M64
    h ^= h >> 29
    h = (h * P3) & M64
    h ^= h >> 32
    return h


def image_size(fmt, width, height):
    bw, bh, bits = BLOCKS[fmt]
    return -(-width // bw) * bw * -(-height // bh) * bh * bits // 8


def timg(bti):
    """A BTI's format, size and top level's image data."""
    fmt, _alpha, width, height = struct.unpack_from(">BBHH", bti, 0)
    offset = struct.unpack_from(">I", bti, 0x1C)[0]
    return fmt, width, height, bti[offset:offset + image_size(fmt, width, height)]


def encode(fmt, intensity, alpha):
    """L images of the texture's size into GX's blocks: I4 (alpha unused), IA4 or IA8."""
    width, height = intensity.size
    bw, bh, _ = BLOCKS[fmt]
    ip, ap = intensity.load(), alpha.load()
    out = bytearray()
    nibble = None

    def texel(x, y):
        return (ip[x, y], ap[x, y]) if x < width and y < height else (0, 0)

    for by in range(0, height, bh):
        for bx in range(0, width, bw):
            for y in range(by, by + bh):
                for x in range(bx, bx + bw):
                    i, a = texel(x, y)
                    if fmt == I4:
                        value = (i * 15 + 127) // 255
                        if nibble is None:
                            nibble = value
                        else:
                            out.append(nibble << 4 | value)
                            nibble = None
                    elif fmt == IA4:
                        out.append(((a * 15 + 127) // 255) << 4 | (i * 15 + 127) // 255)
                    else:
                        out += bytes((a, i))
    return bytes(out)


def encode_rgba8(img):
    """An RGBA image into GX's RGBA8: each 4x4 block's alpha and red pairs, then its green and blue pairs."""
    width, height = img.size
    pixels = img.load()
    out = bytearray()
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            block = [pixels[x, y] if x < width and y < height else (0, 0, 0, 0)
                     for y in range(by, by + 4) for x in range(bx, bx + 4)]
            out += bytes(c for r, g, b, a in block for c in (a, r))
            out += bytes(c for r, g, b, a in block for c in (g, b))
    return bytes(out)


def canvas(size):
    w, h = size
    return Image.new("L", (w * SUPERSAMPLE, h * SUPERSAMPLE), 0)


def shrink(img, size):
    return img.resize(size, Image.LANCZOS)


def letters(size, text, fill=0.94):
    """White letters on black filling the texture, stretched to it, as the GameCube's tall condensed ones are."""
    w, h = size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE
    font = ImageFont.truetype(FONT, 512)
    box = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=font)
    glyph = Image.new("L", (box[2] - box[0] + 16, box[3] - box[1] + 16), 0)
    ImageDraw.Draw(glyph).text((8 - box[0], 8 - box[1]), text, font=font, fill=255)
    gw, gh = int(w * fill), int(h * fill)
    img = Image.new("L", (w, h), 0)
    img.paste(glyph.resize((gw, gh), Image.LANCZOS), ((w - gw) // 2, (h - gh) // 2))
    mask = shrink(img, size)
    return mask, mask


def face_button(colour):
    """A 360 face button: a disc in its colour in a thin dark rim, in the proportions of the GameCube's A and B base
    (tt_zelda_button_ab_maru: the rim the outer tenth of a disc nearly the texture's width), as wide as the texture
    allows, drawn as it shows."""
    def art(size):
        side = min(size) * SUPERSAMPLE
        disc = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        r = side * 0.475
        c = side / 2
        d = ImageDraw.Draw(disc)
        d.ellipse((c - r, c - r, c + r, c + r), fill=(0, 0, 0, 255))
        d.ellipse((c - r * 0.89, c - r * 0.89, c + r * 0.89, c + r * 0.89), fill=colour + (255,))
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        img.paste(shrink(disc, (min(size), min(size))), ((size[0] - min(size)) // 2, (size[1] - min(size)) // 2))
        return img
    return art


def bumper_shape(size):
    """RB: a rounded bar wider than tall, light in a dark rim."""
    shade, cover = canvas(size), canvas(size)
    w, h = shade.size
    box = (w * 0.04, h * 0.30, w * 0.96, h * 0.70)
    ImageDraw.Draw(cover).rounded_rectangle(box, radius=h * 0.18, fill=255)
    d = ImageDraw.Draw(shade)
    d.rounded_rectangle(box, radius=h * 0.18, fill=60)
    inner = (box[0] + h * 0.04, box[1] + h * 0.04, box[2] - h * 0.04, box[3] - h * 0.04)
    d.rounded_rectangle(inner, radius=h * 0.14, fill=225)
    return shrink(shade, size), shrink(cover, size)


def start_arrow(size):
    """The 360's Start: a right-pointing triangle."""
    img = canvas(size)
    w, h = img.size
    ImageDraw.Draw(img).polygon([(w * 0.18, h * 0.22), (w * 0.86, h * 0.5), (w * 0.18, h * 0.78)], fill=255)
    mask = shrink(img, size)
    return mask, mask


def stick(size, letter):
    """A thumbstick seen from above, with its letter, light enough for the layout's tint."""
    shade, cover = canvas(size), canvas(size)
    w, h = shade.size
    r = min(w, h) * 0.47
    cx, cy = w / 2, h / 2
    ImageDraw.Draw(cover).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    d = ImageDraw.Draw(shade)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=40)
    d.ellipse((cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86), fill=200)
    d.ellipse((cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62), fill=150)
    font = ImageFont.truetype(FONT, int(r))
    box = d.textbbox((0, 0), letter, font=font)
    d.text((cx - (box[0] + box[2]) / 2, cy - (box[1] + box[3]) / 2), letter, font=font, fill=255)
    return shrink(shade, size), shrink(cover, size)


# The Xbox 360 controller's B and Y; its A and X are src/dusk/xbox_prompts.cpp's tints.
B_RED = (225, 40, 40)
Y_AMBER = (250, 175, 0)

# (archive, texture, its art): the HUD's prompts. A texture shared with other archives matches there too.
PROMPTS = [
    ("res/Layout/button.arc", "tt_zelda_button_b_text.bti", lambda s: letters(s, "X")),
    ("res/Layout/button.arc", "tt_zelda_button_x_text.bti", lambda s: letters(s, "B")),
    ("res/Layout/button.arc", "tt_zelda_button_x_base.bti", face_button(B_RED)),
    ("res/Layout/button.arc", "tt_zelda_button_y_base.bti", face_button(Y_AMBER)),
    ("res/Layout/button.arc", "im_zelda_button_z_base.bti", bumper_shape),
    ("res/Layout/button.arc", "im_zelda_button_z_text.bti", lambda s: letters(s, "RB")),
    ("res/Layout/button.arc", "im__zelda_button_r_text.bti", lambda s: letters(s, "RT")),
    ("res/Layout/button.arc", "tt_start_00.bti", start_arrow),
    ("res/Layout/button.arc", "c_stick_anim_otah.10.bti", lambda s: stick(s, "R")),
]


def main():
    disc_path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "src", "dusk", "xbox_prompts_data.inc")
    archives = {}
    entries = []
    with open(disc_path, "rb") as disc:
        files = disc_files(disc)
        for archive, texture, art in PROMPTS:
            if archive not in archives:
                offset, size = files[archive]
                disc.seek(offset)
                archives[archive] = rarc_files(yaz0(disc.read(size)))
            fmt, width, height, data = timg(archives[archive][texture])
            drawn = art((width, height))
            if isinstance(drawn, Image.Image):
                new_fmt, replacement = RGBA8, encode_rgba8(drawn)
            else:
                new_fmt, replacement = fmt, encode(fmt, *drawn)
            assert len(replacement) == image_size(new_fmt, width, height), texture
            entries.append((texture, xxh64(data), len(data), width, height, fmt, new_fmt, replacement))
    with open(output, "w", newline="\n") as out:
        out.write("// Generated by tools/xbox_prompts.py from the GameCube disc; don't edit.\n")
        for n, (texture, *_, replacement) in enumerate(entries):
            out.write("alignas(32) static const u8 kPrompt%d[] = {  // %s\n" % (n, texture))
            for i in range(0, len(replacement), 24):
                out.write("    " + " ".join("0x%02X," % b for b in replacement[i:i + 24]) + "\n")
            out.write("};\n")
        out.write("static const Prompt kPrompts[] = {\n")
        for n, (texture, digest, size, width, height, fmt, new_fmt, _) in enumerate(entries):
            out.write("    {0x%016XULL, %d, %d, %d, %d, %d, kPrompt%d},  // %s\n"
                      % (digest, size, width, height, fmt, new_fmt, n, texture))
        out.write("};\n")
    print("%d prompts to %s" % (len(entries), output))


if __name__ == "__main__":
    main()
