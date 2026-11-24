#!/usr/bin/env python3
"""Pack per-row frame PNGs (or one full sheet PNG) plus a spec into a .codex-pet bundle.

Spec JSON: {"id","displayName","description","cell":[w,h],"fps":8,
            "rows":{"idle":{"durations":[...]}, ... all 9 rows}}
Frames layout: DIR/<row-name>/NN.png, each exactly cell size, RGBA.
"""
import argparse
import json
import os

from PIL import Image

from petlib import COLS, ROW_NAMES, clear_transparent_rgb, crop_cell, die, save_webp, write_pet_json


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--frames", help="directory with <row-name>/NN.png frames")
    src.add_argument("--from-sheet", help="full sheet PNG (cell*8 x cell*9) instead of frames")
    ap.add_argument("--spec", required=True, help="spec JSON")
    ap.add_argument("--out", required=True, help="output bundle directory")
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    cw, ch = spec["cell"]
    rows = spec["rows"]
    missing = [n for n in ROW_NAMES if n not in rows]
    if missing:
        die("spec is missing rows: " + ", ".join(missing))
    durs = {n: rows[n]["durations"] for n in ROW_NAMES}
    for n, d in durs.items():
        if not 1 <= len(d) <= COLS:
            die("row %s: need 1-%d durations, got %d" % (n, COLS, len(d)))
        if any((not isinstance(x, int)) or x <= 0 or x > 60000 for x in d):
            die("row %s: durations must be positive ints <= 60000" % n)

    sheet = Image.new("RGBA", (cw * COLS, ch * len(ROW_NAMES)), (0, 0, 0, 0))
    if a.from_sheet:
        src_img = Image.open(a.from_sheet).convert("RGBA")
        if src_img.size != sheet.size:
            die("sheet is %s, expected %s" % (src_img.size, sheet.size))
        for r, n in enumerate(ROW_NAMES):
            for c in range(len(durs[n])):
                sheet.paste(crop_cell(src_img, r, c, cw, ch), (c * cw, r * ch))
    else:
        for r, n in enumerate(ROW_NAMES):
            d = os.path.join(a.frames, n)
            if not os.path.isdir(d):
                die("missing frame directory " + d)
            files = sorted(x for x in os.listdir(d) if x.lower().endswith(".png"))
            if len(files) != len(durs[n]):
                die("row %s: %d frames but %d durations" % (n, len(files), len(durs[n])))
            for c, fn in enumerate(files):
                im = Image.open(os.path.join(d, fn)).convert("RGBA")
                if im.size != (cw, ch):
                    die("%s/%s is %s, expected %s" % (n, fn, im.size, (cw, ch)))
                sheet.paste(im, (c * cw, r * ch))

    os.makedirs(a.out, exist_ok=True)
    save_webp(clear_transparent_rgb(sheet), os.path.join(a.out, "spritesheet.webp"))
    write_pet_json(a.out, spec["id"], spec["displayName"], spec.get("description", ""),
                   (cw, ch), durs, spec.get("fps", 8))
    print("wrote bundle to " + a.out)


if __name__ == "__main__":
    main()
