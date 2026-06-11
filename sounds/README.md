# Local sound library

Drop `.mp3` / `.wav` files here to browse and search them in the app under
**Explore → Local**.

## Layout

```
sounds/
├── Memes/
│   ├── airhorn.mp3
│   └── bruh.mp3
├── Games/
│   └── coin.mp3
└── loose.mp3        # files in the root show under "Uncategorized"
```

- **Top-level subfolders are categories** (collapsible/toggleable in the UI).
- Files placed directly in `sounds/` are grouped under **Uncategorized**.
- Nested deeper than one level are grouped by their **top-level** folder.

## Notes

- This folder is bind-mounted **read-only** into the backend container at
  `/sounds` (`BYTEBLASTER_LOCAL_SOUNDS_DIR`). Nothing is ever written back here.
- The audio files themselves are git-ignored; only this README and `.gitkeep`
  are tracked.
- "Add to soundboard" **copies** a file into the regular sound storage; the
  original stays here untouched.
