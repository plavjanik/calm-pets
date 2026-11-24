# Calm motion

A calm pet looks alive without demanding attention. Good built-in pets keep the feet planted
and the body almost still. The movement is in the face: blinks, eye direction, a slight
smile. Copy that.

## Recipe

1. **One held pose per state.** Each row is one pose with tiny changes, not a cycle of
   different poses. Changing state is the big event. Inside a state, only details change.
2. **Long holds, short accents.** Set per-frame durations: hold 2000–3000 ms, blink
   110 ms, and use 200–300 ms in-betweens for eased changes.
3. **Motion budget per frame.** Away from the face, aim for 1–2 screen pixels. The face may
   change more (eyelids, pupils, mouth).
4. **Breathing.** Use a local bulge of the chest or belly only. The head, tail, feet and
   outline stay fixed. Ease it in and out with half-step frames. Never scale the whole
   body.
5. **No added bob.** Apps may bob the pet already (Orca adds about 4 px). Whole-body motion
   is for jumping and running-left/right only.
6. **Ease.** Arrange frames as hold, ease, accent, ease, hold. The last frame of a row is a
   good place for the longest hold.

## Example timings

The green duck's idle uses 8 frames. In milliseconds:

```
2600 hold (eyes open) → 260 breathe in (half) → 700 breathe in (full) → 260 breathe out (half)
→ 2000 hold → 110 blink → 2600 hold → 900 settle
```

| State | Pose | Changes inside the pose | Timing |
|---|---|---|---|
| waiting | turns or tilts toward the viewer | blink, a small raised hand or head tilt | holds of 1.5–2.5 s |
| running | busy: typing, reading, paddling | small repeated detail (hands or eyes), body still | 200–400 ms per frame |
| review | content: closed-mouth smile, nod | blink, smile eases in | holds of 2–3 s |
| jumping | crouch, lift, peak, land, settle | whole body | about 120–200 ms per frame |
| failed | slump | eyes close slowly | long holds |

## Common mistakes

- Every row a busy 8-frame loop at 120 ms, which is what the app defaults lead to.
- A whole-body breath or bob, which reads as "heavy" or "jittery".
- Pose jumps between frames: a size change, a shifted base, or a redrawn face that
  differs slightly.
- Pixel-art crispness lost through a non-integer display scale (see `format.md`).
