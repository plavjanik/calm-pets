"""Shared helpers for the calm-pet-designer scripts (format constants, bundle IO)."""
import json
import os
import sys

from PIL import Image, ImageChops

COLS = 8
ROW_NAMES = ["idle", "running-right", "running-left", "waving", "jumping",
             "failed", "waiting", "running", "review"]
STD_CELL = (192, 208)
MAX_WEBP_BYTES = 6 * 1024 * 1024


def die(msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(1)


def load_meta(bundle):
    path = os.path.join(bundle, "pet.json")
    if not os.path.isfile(path):
        die("no pet.json in " + bundle)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cell_size(meta):
    fr = meta.get("frame")
    if fr:
        return int(fr["width"]), int(fr["height"])
    return STD_CELL


def load_sheet(bundle, meta):
    p = os.path.join(bundle, meta.get("spritesheetPath", "spritesheet.webp"))
    if not os.path.isfile(p):
        die("spritesheet not found: " + p)
    return Image.open(p).convert("RGBA")


def crop_cell(sheet, row, col, w, h):
    return sheet.crop((col * w, row * h, (col + 1) * w, (row + 1) * h))


DEFAULT_DURATIONS = {
    "idle": [1680, 660, 660, 840, 840, 1920],
    "running-right": [120] * 7 + [220], "running-left": [120] * 7 + [220],
    "waving": [140] * 3 + [280], "jumping": [140] * 4 + [280],
    "failed": [140] * 7 + [240], "waiting": [150] * 5 + [260],
    "running": [120] * 5 + [220], "review": [150] * 5 + [280],
}


def _transparent_residue_mask(img):
    """L mask (255 where alpha is 0 but some RGB channel is non-zero)."""
    r, g, b, a = img.split()
    rgb_max = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v else 0)
    return ImageChops.multiply(rgb_max, a.point(lambda v: 255 if v == 0 else 0))


def transparent_residue(img):
    """(pixels with alpha 0 and non-zero RGB, total alpha-0 pixels)."""
    img = img.convert("RGBA")
    return _transparent_residue_mask(img).histogram()[255], img.getchannel("A").histogram()[0]


def clear_transparent_rgb(img):
    """Zero RGB where alpha is 0 (renderers that scale otherwise show colour fringes)."""
    img = img.convert("RGBA")
    mask = _transparent_residue_mask(img)
    if mask.getbbox() is not None:
        img = img.copy()
        img.paste((0, 0, 0, 0), mask=mask)
    return img


def save_webp(img, path):
    """Lossless first; fall back to near-lossless-quality lossy (alpha kept) if too big."""
    img.save(path, "WEBP", lossless=True, exact=True, method=6)
    if os.path.getsize(path) > MAX_WEBP_BYTES:
        img.save(path, "WEBP", lossless=False, quality=94, exact=True, method=6)
        print("note: lossless sheet exceeded 6 MB, saved lossy q94")


def write_pet_json(out_dir, meta_id, name, desc, cell, durations_by_row, fps=8):
    anims = {}
    for i, n in enumerate(ROW_NAMES):
        d = durations_by_row[n]
        anims[n] = {"row": i, "frames": len(d), "frameDurationsMs": list(d)}
    meta = {"id": meta_id, "displayName": name, "description": desc,
            "spritesheetPath": "spritesheet.webp"}
    if tuple(cell) != STD_CELL:
        meta["frame"] = {"width": cell[0], "height": cell[1]}
    meta.update({"fps": fps, "defaultAnimation": "idle", "animations": anims})
    with open(os.path.join(out_dir, "pet.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def durations_by_row(meta):
    return {n: meta["animations"][n]["frameDurationsMs"] for n in ROW_NAMES}
