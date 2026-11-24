# Production tracks

Choose by style and by the tools available. Every track ends the same way: frames at
384x416, then `pack_pet.py`, `validate_pet.py`, `make_standard.py` and `preview_pet.py`.

## A. Smooth 3D toy (procedural 3D, for example Blender)

Best for simple mascots such as a rubber duck. You get perfect consistency between
frames for free.

- Model with a few primitives: ellipsoid body, sphere head, cone or flattened sphere beak.
  A glossy toy material and a soft key light plus a rim light.
- An orthographic camera facing front (or a slight 3/4 view). The camera, lights and
  ground line stay the same in all frames.
- Pose with transforms only. For breathing, use a shape key or a lattice that bulges the
  chest. Blinks come from scaling the eyelid objects.
- Render with a transparent background (film transparent) at 384x416, or at 768x832
  downscaled for cleaner edges.
- Headless runs work well: `blender -b --python render.py -- args`. Blender's bundled
  Python may lack Pillow, so do the image post-processing outside Blender.

## B. Blocky voxel ("block-game" look, original character)

Hard edges and flat colour suit the format. Make your own character, and don't copy
another game's characters or textures.

- Build from axis-aligned boxes whose sizes are whole texels. Hand-paint small pixel
  textures (8–16 colours per part, 2–3 shades per colour). Use nearest-neighbour
  texture sampling.
- Shade from the face direction, not from lights. For example, top faces get 1.0,
  left-facing 0.8 and right-facing 0.6. This keeps every frame consistent.
- Keep one texel size across the whole sprite, and avoid mixed pixel sizes.
- Animate the rigid way, with no squash and stretch: rotate limbs around pivots, turn or
  tilt the head, blink by changing 1 texel, and move props (a laptop for `running`).
- A face made of very few texels turns grumpy easily. Raise the brows by one texel, and
  keep stubble or beard texels out of the face (they read as dirt).

## C. Likeness avatar of a real person (image model + inpainting)

Use this only with the person's consent and their own photo.

- Start from one good, front-facing, neutral image of the person. Make a cut-out base on
  a flat key colour.
- **Change small regions with inpainting, not whole frames with generation.** Blinks,
  eye direction and a closed-mouth smile come from inpainting through a soft (feathered)
  mask. The new region is composited back, so everything else stays pixel-identical.
- Small whole-head motion such as a tilt of 4–6° can come from plain image transforms,
  with no model involved.
- Known drift, observed in trials:
  - Changing the eyebrows, open smiles that show teeth, and generating new walking poses
    all produced "a different, younger person" or wrong beard colours.
  - When a pose drifts, fall back to the base pose with a small lean and bob.
- Show every pose to the person and ask if it still looks like them.
- Privacy:
  - A local image model keeps the photo on the machine. Some cloud pet skills require a
    public URL of the photo.
  - Keep source photos, realistic bundles and screenshots of them out of public
    repositories unless the person explicitly agrees.
  - For a public demo, generate an invented person first. The `demo-dana` pet in this
    repo was made that way, from one text-to-image portrait.

A stylised version of the same person, such as a "3D toy" or chibi figurine generated
from the photo, often drifts less and reads better at 60 px than a realistic one.

## D. Generated cartoon with an image model

For a cartoon pet created from a text concept, OpenAI's `hatch-pet` skill
(`openai/skills`, Apache-2.0) is a complete pipeline:
- a base image;
- one row strip per state on a chroma-key background;
- deterministic slicing into frames;
- QA.

Use it for generation, then apply `calm-motion.md` to the timings, and use this skill's
`make_standard.py` and `preview_pet.py` for HD output and review.

Tips that apply to any generation:
- Attach the base image to every request.
- Generate on flat `#FF00FF` and keep magenta out of the pet.
- Slice with code, not by eye.
- Regenerate only the rows that failed.
