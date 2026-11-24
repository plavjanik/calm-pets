#!/usr/bin/env python3
"""Validate a .codex-pet bundle (pet.json + spritesheet) against the format rules.

Hard failures: schema, geometry, size limits, empty used cells, non-empty unused
cells, non-transparent sheet corners. Warnings: content touching the cell edge.
--codex additionally requires the 192x208 / 1536x1872 Codex contract.
Also: FAIL when >0.1% of alpha-0 pixels carry RGB (--fix --out DIR writes a
cleared copy of the bundle to DIR and validates that copy; the input is never
modified), baseline/size drift warnings, and a calm-motion report (INFO lines;
--motion prints every frame pair).
"""
import argparse
import json
import os
import shutil
import sys

from PIL import Image, ImageChops

from petlib import (COLS, DEFAULT_DURATIONS, ROW_NAMES, STD_CELL, clear_transparent_rgb,
                    crop_cell, save_webp, transparent_residue)

MAX_SHEET = 64 * 1024 * 1024
MAX_JSON = 64 * 1024
ALPHA_VISIBLE = 8
ALPHA_BBOX = 16
RESIDUE_MAX_FRAC = 0.001
BASELINE_TOL = 0.03
HEIGHT_TOL = 0.06
MOTION_EXEMPT = ("jumping", "running-left", "running-right")
CALM_ROWS = ("idle", "waiting", "review")
CALM_MAX_CHANGE = 12.0
MIN_IDLE_LOOP_MS = 3000
DIFF_THRESHOLD = 24


def validate(bundle, codex, motion=False, info=None):
    fails, warns = [], []
    if info is None:
        info = []
    pj = os.path.join(bundle, "pet.json")
    if not os.path.isfile(pj):
        return ["pet.json missing"], warns
    if os.path.getsize(pj) > MAX_JSON:
        fails.append("pet.json larger than 64 KB")
    try:
        with open(pj, encoding="utf-8") as f:
            meta = json.load(f)
    except Exception as e:
        return ["pet.json invalid JSON: %s" % e], warns

    for k in ("id", "displayName", "description", "spritesheetPath"):
        if not isinstance(meta.get(k), str) or not meta[k]:
            fails.append("missing or empty string key: " + k)
    for bad in ("frameWidth", "frameHeight", "columns"):
        if bad in meta:
            fails.append("forbidden key: " + bad)
    fps = meta.get("fps")
    if fps is not None and not (isinstance(fps, (int, float)) and 0 < fps <= 60):
        fails.append("fps must be in (0, 60]")

    cw, ch = STD_CELL
    fr = meta.get("frame")
    if fr is not None:
        try:
            cw, ch = int(fr["width"]), int(fr["height"])
        except Exception:
            fails.append("frame needs width and height")
        if not (0 < cw <= 1024 and 0 < ch <= 1024):
            fails.append("frame width/height must be 1..1024")

    sp = meta.get("spritesheetPath", "")
    root = os.path.realpath(bundle)
    sheet_path = os.path.realpath(os.path.join(bundle, sp))
    if not sheet_path.startswith(root + os.sep):
        fails.append("spritesheetPath escapes the bundle")
        return fails, warns
    if not os.path.isfile(sheet_path):
        fails.append("spritesheet not found: " + sp)
        return fails, warns
    if os.path.getsize(sheet_path) > MAX_SHEET:
        fails.append("spritesheet larger than 64 MB")

    anims = meta.get("animations")
    if not isinstance(anims, dict) or not anims:
        fails.append("animations missing")
        return fails, warns
    da = meta.get("defaultAnimation")
    if da is not None and da not in anims:
        fails.append("defaultAnimation %r not in animations" % da)
    for n in ROW_NAMES:
        if n not in anims:
            warns.append("animation %s not defined" % n)

    sheet = Image.open(sheet_path).convert("RGBA")
    W, H = sheet.size
    if W % cw or H % ch:
        fails.append("sheet %dx%d is not an exact multiple of the %dx%d frame" % (W, H, cw, ch))
        return fails, warns
    cols, nrows = W // cw, H // ch
    if codex and ((cw, ch) != STD_CELL or (W, H) != (1536, 1872)):
        fails.append("--codex needs 192x208 cells and a 1536x1872 sheet (got %dx%d cells, %dx%d)" % (cw, ch, W, H))
    if cols != COLS or nrows != len(ROW_NAMES):
        warns.append("sheet grid is %dx%d, expected %dx%d" % (cols, nrows, COLS, len(ROW_NAMES)))

    for x, y in ((0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)):
        if sheet.getpixel((x, y))[3] != 0:
            fails.append("sheet corner (%d,%d) is not transparent" % (x, y))

    resid, transp = transparent_residue(sheet)
    if resid and resid > RESIDUE_MAX_FRAC * transp:
        fails.append("%d of %d transparent pixels (%.2f%%) have non-zero RGB (run --fix)"
                     % (resid, transp, 100.0 * resid / transp))
    elif resid:
        warns.append("%d transparent pixels have non-zero RGB (below the 0.1%% limit)" % resid)

    used = {}
    rows_seen = set()
    for n, a in anims.items():
        try:
            row, nf, d = a["row"], a["frames"], a["frameDurationsMs"]
        except KeyError as e:
            fails.append("%s: missing key %s" % (n, e))
            continue
        if not (isinstance(row, int) and 0 <= row < nrows):
            fails.append("%s: row %r outside sheet" % (n, row))
            continue
        if row in rows_seen:
            fails.append("%s: row %d used twice" % (n, row))
        rows_seen.add(row)
        if not (isinstance(nf, int) and 1 <= nf <= cols):
            fails.append("%s: frames must be 1..%d" % (n, cols))
            continue
        if not isinstance(d, list) or len(d) != nf:
            fails.append("%s: frameDurationsMs length must equal frames (%d)" % (n, nf))
        elif any((not isinstance(x, int)) or isinstance(x, bool) or x <= 0 or x > 60000 for x in d):
            fails.append("%s: durations must be positive ints <= 60000" % n)
        used[row] = (n, nf)

    for r in range(nrows):
        n, nf = used.get(r, (None, 0))
        for c in range(cols):
            cell = crop_cell(sheet, r, c, cw, ch)
            alpha = cell.getchannel("A")
            if c < nf:
                bbox = alpha.point(lambda v: 255 if v >= ALPHA_VISIBLE else 0).getbbox()
                if bbox is None:
                    fails.append("%s frame %d has no visible pixels" % (n, c))
                elif bbox[0] == 0 or bbox[1] == 0 or bbox[2] == cw or bbox[3] == ch:
                    warns.append("%s frame %d touches the cell edge (clipping risk)" % (n, c))
            elif alpha.getbbox() is not None:
                fails.append("unused cell row %d col %d is not fully transparent" % (r, c))
    analyse(sheet, anims, cw, ch, cols, nrows, used, warns, info, motion)
    return fails, warns


def thresh_bbox(alpha, t):
    return alpha.point(lambda v: 255 if v > t else 0).getbbox()


def row_durations(name, anims):
    d = anims.get(name, {}).get("frameDurationsMs")
    if isinstance(d, list) and d and all(isinstance(x, (int, float)) for x in d):
        return d
    return DEFAULT_DURATIONS.get(name)


def analyse(sheet, anims, cw, ch, cols, nrows, used, warns, info, motion):
    boxes, pre = {}, {}
    for r, (n, nf) in sorted(used.items()):
        for c in range(min(nf, cols)):
            cell = crop_cell(sheet, r, c, cw, ch)
            bb = thresh_bbox(cell.getchannel("A"), ALPHA_BBOX)
            if bb is None:
                continue
            boxes[(n, c)] = bb
            pre[(n, c)] = cell.convert("RGBa")

    def drift(label, a, b):
        dbase = abs(a[3] - b[3])
        dh = abs((a[3] - a[1]) - (b[3] - b[1]))
        if dbase > BASELINE_TOL * ch:
            warns.append("%s: baseline differs by %d px (%.1f%% of cell height)" % (label, dbase, 100.0 * dbase / ch))
        if dh > HEIGHT_TOL * ch:
            warns.append("%s: bbox height differs by %d px (%.1f%% of cell height)" % (label, dh, 100.0 * dh / ch))

    ref = boxes.get(("idle", 0))
    for r, (n, nf) in sorted(used.items()):
        if n in MOTION_EXEMPT or (n, 0) not in boxes:
            continue
        for c in range(1, nf):
            if (n, c) in boxes:
                drift("%s frame %d vs frame 0" % (n, c), boxes[(n, c)], boxes[(n, 0)])
        if ref and n != "idle":
            drift("%s frame 0 vs idle frame 0" % n, boxes[(n, 0)], ref)

    for r, (n, nf) in sorted(used.items()):
        frames = [c for c in range(min(nf, cols)) if (n, c) in pre]
        dur = row_durations(n, anims)
        total = sum(dur) if dur else None
        if len(frames) < 2:
            msg = "%s: single frame, no motion" % n
            (warns if n == "idle" else info).append(msg)
            continue
        changes = []
        for i, c in enumerate(frames):
            c2 = frames[(i + 1) % len(frames)]
            changes.append((c, c2, pair_change(pre[(n, c)], pre[(n, c2)])))
        vals = [v for _, _, v in changes]
        mx, mean = max(vals), sum(vals) / len(vals)
        loop = "%d ms" % total if total is not None else "n/a"
        info.append("%s: motion max %.1f%% mean %.1f%%, loop %s" % (n, mx, mean, loop))
        if motion:
            for c, c2, v in changes:
                info.append("    %s %d->%d: %.1f%%" % (n, c, c2, v))
        if mx == 0:
            (warns if n == "idle" else info).append("%s: no motion (all frames identical)" % n)
        if n in CALM_ROWS and mx > CALM_MAX_CHANGE:
            warns.append("%s: busy for a calm state (frame pair changes up to %.1f%% of the silhouette, limit %d%%)"
                         % (n, mx, CALM_MAX_CHANGE))
        if n == "idle" and total is not None and total < MIN_IDLE_LOOP_MS:
            warns.append("idle: fast idle loop (%d ms, want >= %d ms)" % (total, MIN_IDLE_LOOP_MS))


def pair_change(a, b):
    """Percent of the larger silhouette whose premultiplied RGBA differs by > DIFF_THRESHOLD."""
    d = ImageChops.difference(a, b).split()
    m = ImageChops.lighter(ImageChops.lighter(d[0], d[1]), ImageChops.lighter(d[2], d[3]))
    m = m.point(lambda v: 255 if v > DIFF_THRESHOLD else 0)
    aa = a.split()[3].point(lambda v: 255 if v > ALPHA_BBOX else 0)
    ab = b.split()[3].point(lambda v: 255 if v > ALPHA_BBOX else 0)
    union = ImageChops.lighter(aa, ab)
    changed = ImageChops.multiply(m, union).histogram()[255]
    area = max(aa.histogram()[255], ab.histogram()[255], 1)
    return 100.0 * changed / area


def fix_sheet(bundle, out):
    """Copy pet.json and the sheet from bundle into the new directory out, clearing sheet RGB there."""
    with open(os.path.join(bundle, "pet.json"), encoding="utf-8") as f:
        meta = json.load(f)
    sp = meta["spritesheetPath"]
    src = os.path.realpath(os.path.join(bundle, sp))
    if not src.startswith(os.path.realpath(bundle) + os.sep):
        print("FAIL  spritesheetPath escapes the bundle")
        sys.exit(1)
    shutil.copyfile(os.path.join(bundle, "pet.json"), os.path.join(out, "pet.json"))
    dst = os.path.join(out, sp)
    if not os.path.realpath(dst).startswith(os.path.realpath(out) + os.sep):
        print("FAIL  spritesheetPath escapes the output directory")
        sys.exit(1)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    img = Image.open(dst).convert("RGBA")
    n, _ = transparent_residue(img)
    if n:
        save_webp(clear_transparent_rgb(img), dst)
    print("fixed: cleared RGB on %d transparent pixel(s) in %s" % (n, dst))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="bundle directory (never modified)")
    ap.add_argument("--codex", action="store_true", help="require the 192x208 Codex contract")
    ap.add_argument("--motion", action="store_true", help="print every frame-pair change, not just per-row summary")
    ap.add_argument("--fix", action="store_true",
                    help="clear RGB of alpha-0 pixels: write a copy of pet.json and the cleared sheet to --out, "
                         "then validate that copy (requires --out; the input bundle is not touched)")
    ap.add_argument("--out", metavar="DIR",
                    help="with --fix: new directory to create for the fixed copy (must not exist; never overwritten)")
    a = ap.parse_args()
    if a.fix and not a.out:
        ap.error("--fix requires --out DIR (the input bundle is never modified)")
    if a.out and not a.fix:
        ap.error("--out is only valid with --fix")
    target = a.bundle
    if a.fix:
        if os.path.lexists(a.out):
            ap.error("--out %s already exists; refusing to overwrite" % a.out)
        os.makedirs(a.out)
        fix_sheet(a.bundle, a.out)
        target = a.out
    info = []
    fails, warns = validate(target, a.codex, a.motion, info)
    for i in info:
        print("INFO  " + i if not i.startswith("    ") else i)
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    print("%s: %s (%d failure(s), %d warning(s))" % (
        "FAIL" if fails else "PASS", target, len(fails), len(warns)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
