---
name: calm-pet-designer
description: Design, build, validate and package calm animated desktop pets in the `.codex-pet` bundle format (pet.json + spritesheet.webp) used by OpenAI Codex pets and the Orca app's pet overlay. Covers choosing a look from still options, calm low-distraction motion with held poses and per-frame timing, crisp HD bundles for Orca, standard 192x208 bundles for Codex, smooth 3D toy, blocky voxel and likeness-based avatar styles, and install steps. Use when the user wants to make, fix, restyle or package a Codex pet, an Orca pet, a desktop pet or companion, a sprite-sheet mascot, or a pet/avatar of themselves, or says a pet "moves too much", "looks jagged/pixelated" or "is distracting".
license: MIT
compatibility: Scripts need Python 3.9+ and Pillow. Art can come from any tool (Blender, Blockbench, a pixel editor, an image model such as gpt-image or ComfyUI); none is required by the skill itself.
metadata:
  version: "1.0.0"
  homepage: "https://github.com/plavjanik/calm-pets"
---

# Calm pet designer

A desktop pet sits on screen all day, next to the user's work. The most common failure is
not ugliness but **distraction**: too much motion, jagged scaling, a pet that keeps
changing shape. This skill builds pets that read clearly at small sizes and move calmly.

Read before building:
- `references/format.md`: the bundle contract (rows, frames, pet.json, Codex and Orca limits).
- `references/calm-motion.md`: the motion recipe and example timings.
- `references/styles.md`: production tracks (smooth 3D toy, blocky voxel, likeness avatar, generated cartoon).
- `references/install.md`: installing in Codex and Orca, and sharing.

Scripts (Python 3.9+, Pillow only), in `scripts/`:

| Script | Use |
|---|---|
| `pack_pet.py --frames DIR --spec spec.json --out BUNDLE` | frames `DIR/<row>/NN.png` + timings → `pet.json` + `spritesheet.webp` (`--from-sheet PNG` packs an existing sheet) |
| `validate_pet.py BUNDLE [--codex] [--motion] [--fix]` | checks the contract, colour residue in transparent pixels, baseline and size drift, and how busy each state is (`--motion` gives the full report); `--codex` also requires 192x208 cells; `--fix --out NEW_DIR` writes a copy with the residue cleared and never changes the input |
| `make_standard.py HD_BUNDLE --out STD_BUNDLE` | turns a 384x416 HD bundle into a standard 192x208 bundle |
| `preview_pet.py BUNDLE --out DIR` | one GIF per row with the real timings + contact sheets on dark and light |

## Workflow

Follow these steps in order. Each step ends with something the user can look at.

1. **Brief.** Ask, preferably as multiple-choice questions, which app(s) the pet is for
   (Codex, Orca, both), what character it is, which style (see `references/styles.md`),
   and how lively it may be. Default to "calm". For a pet of a real person, also ask:
   - how close the likeness should be (a realistic bust, a 3D toy figure, or a blocky chibi);
   - whether the photo may leave the machine (a local model versus a cloud service);
   - whether the result may ever be published.
   Pets of real people should stay private by default.
2. **Still options first.** Before animating anything, make 2–4 still options of the idle
   pose. Put them on one sheet, each shown on a dark and a light background at full and
   half size. Let the user pick. Changing a still costs minutes; changing an animated
   bundle costs much more.
3. **Lock the design.** Write down what never changes: silhouette, palette, face, props
   and which side they are on, outline weight, proportions. Every frame is derived from the
   picked still (or the 3D model behind it), never from a text prompt alone.
4. **Plan the states.** For each of the 9 rows, decide on one *held pose* and the few
   small changes inside it (see `references/calm-motion.md`). Make `waiting` clearly
   different from `running`, because in Orca `waiting` means "the agent needs you".
5. **Render frames** at the HD cell size, 384x416, with soft (anti-aliased) edges unless the
   style is deliberately pixel art. Keep the feet or base on the same line in every
   frame. Leave a margin of at least 8 px so nothing touches the cell edge.
6. **Pack** with `pack_pet.py` and set per-frame durations: long holds, short blinks.
7. **Validate** with `validate_pet.py`, then make the standard bundle with
   `make_standard.py` and validate it with `--codex`.
8. **Review by eye.** Run `preview_pet.py` and look at every GIF and both contact sheets
   yourself before showing the user. Check the items under *Review checklist*, fix what
   fails, and state the remaining weak points honestly.
9. **Try it in the app**: the user imports it (`references/install.md`) and reports
   back. Never install into an app's pet folder or overwrite an installed pet without the
   user's explicit yes. Note what they say and apply it to the next pet.

## Review checklist

- Same character in every frame: shape, palette, face, size. A pose that looks like a
  related but different pet fails, even if the validator passes.
- Readable at 60 px and over both a dark and a light background (silhouette test: fill
  it black, is it still recognisable?).
- Idle frame 0 is a good still on its own. Reduced-motion settings may show only that frame.
- Nothing moves that does not need to: feet, base and outline stay fixed during idle.
- No shadows, floor ovals, glows, motion lines, text, speech bubbles or detached effects.
  An effect is allowed only if it touches the body and is opaque. Unused cells are fully
  transparent, and transparent pixels carry no leftover colour (`validate_pet.py` checks
  this).
- Running left and right: mirror running-right frame by frame, and only if the design is
  symmetric (no one-sided markings, props or text). Then check in the app that dragging
  left really plays running-left.
- The validator's motion report shows no "busy" warning for idle, waiting or review. If
  one appears, reduce the change between those frames, or lengthen the holds.
- Transitions between frames are small. Any jump bigger than a few pixels reads as a
  twitch on a pet that is otherwise still.
- For likeness avatars, ask the person whether every pose still looks like them. Image
  models drift to a different person easily (see `references/styles.md`).

## Rules learned from real trials

- **Motion budget.** A first pet with 4–8 frame loops in every row was "too much, it is
  disturbing" next to a calm built-in pet. What fixed it: held poses, 2–3 s holds, a
  110 ms blink, and motion only in the face.
- **Breathing.** Scaling the whole body moves the whole outline and feels heavy. Breathe
  with a local chest bulge only, about 1 screen pixel, eased with half-step frames.
- **Jagged look.** Orca draws sprite sheets with `image-rendering: pixelated`, so any
  non-integer scale looks rasterised. Ship a 384x416 HD bundle and tell Orca users to set
  Pet size 208 (or 104). For Codex, ship the standard 192x208 bundle.
- **The app adds its own motion.** Orca bobs every pet by about 4 px in CSS, and a bundle
  cannot turn that off. Don't add a whole-body bob on top of it.
- **Re-import needs a restart.** After re-importing in Orca, fully quit and restart the
  app before judging a change.
