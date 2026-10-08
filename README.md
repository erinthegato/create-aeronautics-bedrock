# Create: Aeronautics - Bedrock Port (scaffold)

Bedrock addon port scaffold for **Create: Aeronautics** - the bundled NeoForge 1.21.1
mod (v1.3.2) that ships **Simulated + Aeronautics + Offroad**.

> **Status: partial (assets + registry scaffold).**
> Textures, models, sounds, lang and the full block/item/entity registry are extracted
> and packaged into a valid, importable `.mcaddon`. Gameplay (physics contraptions,
> Flywheel rendering, Sable/Simulated machines) is **not** re-implemented - Bedrock's
> JSON addon system cannot run Java mod logic. Blocks/items here are non-functional
> placeholders carrying the original textures and names.

## What's in this repo
- `dist/create-aeronautics-bedrock.mcaddon` - importable addon (Behavior + Resource)
- `pack/create_aeronautics_bp` - behavior pack source (blocks, items, entities)
- `pack/create_aeronautics_rp` - resource pack source (textures, sounds, lang, atlases)
- `extracted/` - raw assets pulled straight from the jar (aeronautics / simulated / offroad)
- `mapping/registry.json` - Java registry name -> Bedrock identifier map
- `source/` - the original bundled jar (reference)
- `tools/` - extraction + build scripts
- `docs/` - mapping + porting notes

## Coverage
| Kind    | Count |
|---------|-------|
| Blocks  | 144 |
| Items   | 17 |
| Entities| 6 |
| Fluids  | 1 |

## Install (end user)
1. Download `dist/create-aeronautics-bedrock.mcaddon`.
2. Double-click it, or import via **Settings > Storage** in Minecraft Bedrock.
3. Activate **both** packs (behavior + resource) on your world.

## Rebuild from source
```bash
python tools/build_repo.py
```

## Credits
- Original mod: **Simulated Team** - *Create: Aeronautics / Simulated / Offroad*
- Create mod: the Create team
- Bedrock port scaffold: erinthegato

## License
MIT for the port scaffold (`LICENSE`). Original mod code/assets remain under their
upstream license - see the bundled `LICENSE.md` inside the jar.
