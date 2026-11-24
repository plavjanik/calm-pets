#!/usr/bin/env python3
"""Render preview GIFs (one per row, real frame timing) and a contact-sheet PNG.

Outputs in --out: <id>-<row>-<bg>.gif, <id>-contact-<bg>.png and, with --states,
<id>-states-<bg>.gif (the chosen rows side by side, each looping on its own timing).
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

from petlib import ROW_NAMES, cell_size, crop_cell, load_meta, load_sheet

BGS = {"dark": (0x1e, 0x1f, 0x24), "light": (0xf4, 0xf4, 0xf0)}
TEXT = {"dark": (200, 200, 200), "light": (60, 60, 60)}


def font(size=12):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def flat(cell, bg, size):
    im = Image.new("RGBA", cell.size, bg + (255,))
    im.alpha_composite(cell)
    if im.size != size:
        im = im.convert("RGB").resize(size, Image.LANCZOS)
    return im.convert("RGB")


def to_pal(frames):
    return [f.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]


def save_gif(frames, durations, path):
    p = to_pal(frames)
    p[0].save(path, save_all=True, append_images=p[1:], duration=durations, loop=0, optimize=True, disposal=1)


def row_frames(sheet, meta, name, bg, size):
    a = meta["animations"][name]
    cw, ch = cell_size(meta)
    fr = [flat(crop_cell(sheet, a["row"], c, cw, ch), bg, size) for c in range(a["frames"])]
    return fr, list(a["frameDurationsMs"])


def states_gif(sheet, meta, rows, bgname, size, path, grid=50):
    bg = BGS[bgname]
    panels = [row_frames(sheet, meta, n, bg, size) for n in rows]
    totals = [sum(d) for _, d in panels]
    ends = []
    for _, d in panels:
        acc, e = 0, []
        for x in d:
            acc += x
            e.append(acc)
        ends.append(e)
    f, lab = font(14), TEXT[bgname]
    pad = 22
    out_frames, out_durs, last = [], [], None
    for t in range(0, max(totals), grid):
        idx = []
        for e, tot in zip(ends, totals):
            m = t % tot
            idx.append(next(i for i, v in enumerate(e) if m < v))
        if idx == last:
            out_durs[-1] += grid
            continue
        last = idx
        canvas = Image.new("RGB", (size[0] * len(rows), size[1] + pad), bg)
        d = ImageDraw.Draw(canvas)
        for i, (n, k) in enumerate(zip(rows, idx)):
            canvas.paste(panels[i][0][k], (i * size[0], 0))
            w = d.textlength(n, font=f)
            d.text((i * size[0] + (size[0] - w) / 2, size[1] + 4), n, fill=lab, font=f)
        out_frames.append(canvas)
        out_durs.append(grid)
    save_gif(out_frames, out_durs, path)


def contact(sheet, meta, bgname, max_w, path, grid=False):
    cw, ch = cell_size(meta)
    bg = BGS[bgname]
    label_w = 96
    cols = sheet.size[0] // cw
    scale = min(1.0, (max_w - label_w) / float(cols * cw))
    sz = (max(1, round(cw * scale)), max(1, round(ch * scale)))
    img = Image.new("RGB", (label_w + sz[0] * cols, sz[1] * len(ROW_NAMES)), bg)
    d = ImageDraw.Draw(img)
    f = font(12)
    for r, n in enumerate(ROW_NAMES):
        d.text((6, r * sz[1] + sz[1] // 2 - 6), n, fill=TEXT[bgname], font=f)
        for c in range(cols):
            cell = crop_cell(sheet, r, c, cw, ch)
            if cell.getchannel("A").getbbox() is None:
                continue
            img.paste(flat(cell, bg, sz), (label_w + c * sz[0], r * sz[1]))
    if grid:
        for r in range(len(ROW_NAMES)):
            for c in range(cols):
                x, y = label_w + c * sz[0], r * sz[1]
                d.rectangle((x, y, x + sz[0] - 1, y + sz[1] - 1), outline=(220, 40, 40))
    img.save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--bg", choices=["dark", "light", "both"], default="dark")
    ap.add_argument("--scale", type=float, help="GIF scale (default: cell becomes 192 px wide)")
    ap.add_argument("--contact-width", type=int, default=1200, help="max contact-sheet width in px")
    ap.add_argument("--states", help="comma-separated rows for a side-by-side states GIF")
    ap.add_argument("--grid", action="store_true", help="draw thin red cell borders on the contact sheet")
    a = ap.parse_args()

    meta = load_meta(a.bundle)
    sheet = load_sheet(a.bundle, meta)
    cw, ch = cell_size(meta)
    s = a.scale if a.scale else 192.0 / cw
    size = (round(cw * s), round(ch * s))
    os.makedirs(a.out, exist_ok=True)
    pid = meta["id"]
    for bgname in (["dark", "light"] if a.bg == "both" else [a.bg]):
        for n in ROW_NAMES:
            if n in meta["animations"]:
                fr, du = row_frames(sheet, meta, n, BGS[bgname], size)
                save_gif(fr, du, os.path.join(a.out, "%s-%s-%s.gif" % (pid, n, bgname)))
        contact(sheet, meta, bgname, a.contact_width, os.path.join(a.out, "%s-contact-%s.png" % (pid, bgname)), a.grid)
        if a.states:
            states_gif(sheet, meta, a.states.split(","), bgname, size,
                       os.path.join(a.out, "%s-states-%s.gif" % (pid, bgname)))
    print("previews written to " + a.out)


if __name__ == "__main__":
    main()
