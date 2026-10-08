# Porting Notes

## Approach
1. `tools/extract.py` - pulls the 3 nested mods out of the bundled jar.
2. `tools/analyze.py` / `tools/map_registry.py` - read blockstates, item models,
   `sounds.json` and `en_us.json` to build the registry.
3. `tools/build_repo.py` - copies assets, emits Bedrock BP+RP JSON, packages the `.mcaddon`.

## Tooling reality check
`ModMorpher` and `Portkit` **are not real, available tools**. There is no general-purpose
automated Java-mod -> Bedrock-addon translator. This port was produced with a custom
Python pipeline (in `tools/`) - not those tools.

## What is NOT ported (and why)
- **Physics / contraptions** (Sable, Simulated assemblies, gyroscopic bearings) - these are
  custom Java systems with serverside simulation. Bedrock addons cannot run them.
- **Flywheel / custom rendering** - Bedrock's renderer is not moddable to that degree.
- **Recipes, loot tables, advancements, worldgen** - Java data-driven JSON formats differ
  from Bedrock's; not translated here.

## What IS ported
- All textures + sounds (copied verbatim).
- Block/item/entity identifiers, display names (lang) and creative menu categories.
- Blocks render as full-block placeholders textured with the original art.

## Next steps for a real port
- Re-implement logic with the Bedrock **Scripting API** (`@minecraft/server`).
- Build custom geometry (`.geo.json`) from the Java `.bbmodel`/`.obj` files.
- Translate recipes to Bedrock `recipes/*.json` and loot to `loot_tables/`.
