# DQM Dex & Fusion

A mobile-friendly Dragon Warrior Monsters / Dragon Quest Monsters game selector, monster encyclopedia, and game-specific breeding/synthesis interface.

## Status

Initial standalone scaffold. This is **not yet a complete port of Yanoverse Multi-Dex**. The original repository remains untouched. The interface includes game selectors, a Dex tab, and a Fusion tab. Monster records, verified recipes, and game logo images have not yet been imported.

## Data format

Add one JSON file per game at `data/<game-id>.json` with this shape:

```json
{
  "monsters": [
    {"id": "example", "number": 1, "name": "Example", "family": "Slime"}
  ],
  "recipes": [
    {"parent1": "example", "parent2": "another", "result": "offspring"}
  ]
}
```

Recipe data must be validated against the selected game's mechanics. The UI deliberately avoids inventing fusion outcomes.

## Next steps

- Port reusable Yanoverse layout, responsive styling, navigation and detail-page components while excluding franchise-specific data/assets.
- Replace text-based game selectors with properly sourced game-logo assets.
- Import verified monster databases and per-game breeding/synthesis rules.
- Validate each game's mechanics, including games where traditional breeding is not applicable.
- Add tests and configure GitHub Pages.

The Withered World is not listed because its announced release date is December 3, 2026.
