# Dragon Quest Monsters Dex & Fusion

A responsive, game-specific monster encyclopedia and breeding/synthesis tool.

## Supported game selectors (12)

1. Dragon Warrior Monsters (GBC)
2. Dragon Warrior Monsters 2 — Cobi's Journey / Tara's Adventure (GBC, combined)
3. Dragon Quest Monsters 1+2 (PS1; separate DQM1 and DQM2 modes)
4. Caravan Heart (GBA)
5. Joker (DS)
6. Joker 2 (DS)
7. Joker 2 Professional (DS)
8. Terry's Wonderland 3D (3DS)
9. Iru & Luca's Marvelous Mysterious Key (3DS)
10. Joker 3 (3DS)
11. Joker 3 Professional (3DS)
12. The Dark Prince (Switch / PC)

Mobile-only releases and mobile-only remakes are excluded.

## Current implementation

- Responsive game selection and Dex / Fusion tabs
- Search by monster name, number or family
- Two-parent breeding/synthesis result lookup, order-independent
- Game-specific JSON loading and optional PS1 DQM1/DQM2 mode filtering
- Empty states rather than fabricated monster data or recipes

**Not complete:** Verified monster datasets, real logo art, detailed monster profiles, game-specific mechanics, source Yanoverse visual component migration, and browser testing remain outstanding. The original Yanoverse repository has not been changed.

## Data schema

Place JSON at `data/<game-id>.json`, e.g. `data/dwm2.json`:

```json
{
  "monsters": [
    {"id":"slime","number":1,"name":"Slime","family":"Slime"}
  ],
  "recipes": [
    {"parent1":"monster-id-1","parent2":"monster-id-2","result":"result-monster-id"}
  ]
}
```

For the PS1 collection, entries may use `"mode":"DQM1"` or `"mode":"DQM2"`. Unmarked entries are shared between both modes. IDs must be stable and unique within each game; recipe parent/result IDs must resolve to monster IDs. Add only researched, verified recipes.

## Development

This is a static HTML/CSS/JavaScript application. Open `index.html` via a local web server or enable GitHub Pages for the repository's root. JSON requests require HTTP serving, not a `file://` URL.

## Planned work

1. Bring over reusable visual patterns from Yanoverse without modifying the source.
2. Source and install legitimate game logos, replacing text-only selectors.
3. Implement normalized per-game monster data and validated fusion rules.
4. Add monster details, search/filter enhancements, and unit/browser tests.
5. Deploy and test on GitHub Pages.
