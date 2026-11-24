# Installing and sharing pets

## Orca

[Orca](https://orca.dev) by stablyai runs several coding agents side by side
([source](https://github.com/stablyai/orca)). Its pet overlay is an experimental feature.

1. Turn on Settings → Experimental → **Pet**.
2. In the status bar, open the Pet menu → **Import .codex-pet bundle…** and choose the
   bundle *folder*.
3. Quit and restart Orca completely, because a reload is not enough.
4. For an HD bundle (384x416 cells), set Pet menu → Size to **208**, or 104. This gives an
   exact half scale, which looks crisp. The default size of 180 scales unevenly and looks
   jagged.

Orca copies imported bundles into its own data folder, so the original can be moved
afterwards. Orca has no CLI command for pets. To re-import an updated bundle, import it
again and restart.

## Codex

Codex loads pets from its pets folder, `${CODEX_HOME:-$HOME/.codex}/pets/`. Installing
there changes the user's app setup, so:
- don't do it on your own: show the user the command and let them run it, or run it only
  after they explicitly say yes;
- never overwrite or delete an existing pet folder. If the folder already exists, stop and
  ask, or ask for a new `id`.

```sh
dest="${CODEX_HOME:-$HOME/.codex}/pets/green-duck"
[ -e "$dest" ] && echo "already installed: $dest" || { mkdir -p "$(dirname "$dest")" && cp -R green-duck "$dest"; }
```

Then pick the pet in Settings → Appearance → Pets, or with `/pet`.

## Sharing

- Commit the bundles unzipped, one folder each, so people can import them straight from a
  clone.
- Attach a ZIP of each folder to a GitHub release for people who don't use git.
- Show each pet in the README with a still image and an animated GIF made with
  `preview_pet.py`.
- State a licence for the artwork separately from the code.
