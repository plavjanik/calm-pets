#!/usr/bin/env python3
"""Downscale an HD bundle (e.g. 384x416 cells) to a standard 192x208 Codex bundle."""
import argparse
import os

from PIL import Image

from petlib import COLS, ROW_NAMES, STD_CELL, clear_transparent_rgb, crop_cell, cell_size, die, durations_by_row, load_meta, load_sheet, save_webp, write_pet_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("hd_bundle")
    ap.add_argument("--out", required=True, help="output bundle directory")
    ap.add_argument("--id", help="id for the new bundle (default: keep)")
    a = ap.parse_args()

    meta = load_meta(a.hd_bundle)
    cw, ch = cell_size(meta)
    sheet = load_sheet(a.hd_bundle, meta)
    if sheet.size != (cw * COLS, ch * len(ROW_NAMES)):
        die("unexpected sheet size %s" % (sheet.size,))
    out = Image.new("RGBA", (STD_CELL[0] * COLS, STD_CELL[1] * len(ROW_NAMES)), (0, 0, 0, 0))
    for r in range(len(ROW_NAMES)):
        for c in range(COLS):
            cell = crop_cell(sheet, r, c, cw, ch)
            if cell.getchannel("A").getbbox() is None:
                continue
            small = cell.convert("RGBa").resize(STD_CELL, Image.LANCZOS).convert("RGBA")
            out.paste(small, (c * STD_CELL[0], r * STD_CELL[1]))
    os.makedirs(a.out, exist_ok=True)
    save_webp(clear_transparent_rgb(out), os.path.join(a.out, "spritesheet.webp"))
    write_pet_json(a.out, a.id or meta["id"], meta["displayName"], meta.get("description", ""),
                   STD_CELL, durations_by_row(meta), meta.get("fps", 8))
    print("wrote standard bundle to " + a.out)


if __name__ == "__main__":
    main()
