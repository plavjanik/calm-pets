# The `.codex-pet` bundle

A bundle is a plain folder:

```
my-pet/
  pet.json
  spritesheet.webp
```

## Sprite sheet

- A grid of **8 columns x 9 rows** of equal cells, with a transparent background and no
  gutters, labels or grid lines.
- Standard (Codex) cell: **192x208**, sheet 1536x1872.
- HD cell used for Orca: **384x416**, sheet 3072x3744, declared with
  `"frame": {"width": 384, "height": 416}`.
- PNG or WebP. Lossless WebP keeps soft alpha edges and is small (about 0.3–1.5 MB HD).
- Cells to the right of a row's last frame must be fully transparent.

| Row | Name | Usual frames | What it should show |
|---|---|---|---|
| 0 | idle | 6 (up to 8) | calm breathing and blinking; frame 0 must work as a still |
| 1 | running-right | 8 | moving right (drag to the right in Orca) |
| 2 | running-left | 8 | moving left; mirror row 1 only if the design is symmetric |
| 3 | waving | 4 | greeting gesture |
| 4 | jumping | 5 | anticipation, lift, peak, landing, settle |
| 5 | failed | 8 | readable but not noisy, such as a slump or a sad face |
| 6 | waiting | 6 | "needs you": looks at the viewer, a small raised gesture |
| 7 | running | 6 | busy working in place, such as typing or reading |
| 8 | review | 6 | done: content, satisfied, inspecting |

## pet.json

```json
{
  "id": "green-duck",
  "displayName": "Green Duck",
  "description": "A classic rubber duck in mainframe-terminal green.",
  "spritesheetPath": "spritesheet.webp",
  "frame": { "width": 384, "height": 416 },
  "fps": 8,
  "defaultAnimation": "idle",
  "animations": {
    "idle": { "row": 0, "frames": 8,
              "frameDurationsMs": [2600, 260, 700, 260, 2000, 110, 2600, 900] }
  }
}
```

- The Codex contract requires `id`, `displayName`, `description` and `spritesheetPath`.
- Optional keys that Orca reads, taken from its import code:
  - `frame {width, height}`: each at most 1024.
  - `fps`: at most 60.
  - `defaultAnimation`.
  - `animations{name: {row, frames, frameDurationsMs}}`: each duration is a positive
    integer of at most 60000, and there is one duration per frame.
- There is **no** `frameWidth`, `frameHeight` or `columns` key. Columns are sheet width /
  frame width, and the sheet must be an exact multiple of the frame.
- Limits: pet.json at most 64 KB, sheet file at most 64 MB, no symlinks, and
  `spritesheetPath` must stay inside the bundle.
- Without `animations`, Orca uses its default timings. Hold frames last longest. Idle
  defaults are 1680, 660, 660, 840, 840 and 1920 ms.
- Codex documents only the fixed 192x208 layout. Whether it honours custom `frame` and
  per-frame durations is not verified. Give Codex the standard bundle.

## Which states the apps actually play

Orca, read from its overlay code:

| State | When Orca plays it |
|---|---|
| `waiting` | Any agent is blocked or waiting. This has the highest priority. |
| `running` | Otherwise, while any agent is working. |
| `review` | Otherwise, when any agent is done. |
| `idle` | When none of the above applies. |
| `jumping` | On hover. |
| `running-left` / `running-right` | While the pet is dragged. |

Orca never plays `waving` or `failed`, but fill those rows anyway, because the import
checks every row and Codex may use them.

Codex uses the same 9 rows for its own agent states. Community "v2" sheets with extra rows
(`spriteVersionNumber: 2`) are not part of what Orca accepts. Stick to 9 rows.
