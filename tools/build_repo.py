#!/usr/bin/env python3
"""Build the create-aeronautics-bedrock repo: asset extraction, registry
mapping, Bedrock BP+RP generation, .mcaddon packaging."""
import zipfile, os, json, shutil, uuid, sys, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXTRACTED = os.path.join(ROOT, "_extracted")
REPO = os.path.join(ROOT, "create-aeronautics-bedrock")
NS_LIST = ["aeronautics", "simulated", "offroad"]
UUIDNS = uuid.UUID("a1b2c3d4-0000-4000-8000-c0ffee000001")
MIN_ENGINE = [1, 21, 0]
PACK_VERSION = [1, 0, 0]
MOD_VERSION = "1.3.2"

def du(key):
    return str(uuid.uuid5(UUIDNS, key))

def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

# ---------- dirs ----------
DIRS = {
    "src": os.path.join(REPO, "source"),
    "tools": os.path.join(REPO, "tools"),
    "ext": os.path.join(REPO, "extracted"),
    "map": os.path.join(REPO, "mapping"),
    "docs": os.path.join(REPO, "docs"),
    "bp": os.path.join(REPO, "pack", "create_aeronautics_bp"),
    "rp": os.path.join(REPO, "pack", "create_aeronautics_rp"),
    "dist": os.path.join(REPO, "dist"),
}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

# ---------- copy original jar + tools ----------
src_jar = os.path.join(ROOT, "create-aeronautics-bundled-1.21.1-1.3.2.jar")
copy(src_jar, os.path.join(DIRS["src"], os.path.basename(src_jar)))
for t in ["extract.py", "analyze.py", "map_registry.py", "build_repo.py"]:
    p = os.path.join(ROOT, "_tools", t)
    if os.path.exists(p):
        copy(p, os.path.join(DIRS["tools"], t))

# ---------- extract assets from nested jars ----------
jars = {ns: os.path.join(EXTRACTED, ns + ".jar") for ns in NS_LIST}
textures_by_ns = collections.defaultdict(list)   # ns -> [relpath under assets/<ns>/textures/]
sounds_by_ns = collections.defaultdict(list)
sound_defs = {}                                   # ns -> {event: [file relpath under sounds/]}
lang_by_ns = {}

for ns in NS_LIST:
    jz = zipfile.ZipFile(jars[ns])
    names = jz.namelist()
    for name in names:
        if name.endswith("/"):
            continue
        prefix = f"assets/{ns}/"
        if not name.startswith(prefix):
            continue
        rel = name[len(prefix):]
        if rel.startswith("textures/") and name.endswith(".png"):
            out = os.path.join(DIRS["ext"], ns, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(jz.read(name))
            textures_by_ns[ns].append(rel)
        elif rel.startswith("sounds/") and name.endswith(".ogg"):
            out = os.path.join(DIRS["ext"], ns, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(jz.read(name))
            sounds_by_ns[ns].append(rel)
        elif rel.startswith("lang/") and name.endswith(".json"):
            out = os.path.join(DIRS["ext"], ns, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as f:
                f.write(jz.read(name))
    # sounds.json -> sound definitions
    if f"assets/{ns}/sounds.json" in names:
        sj = json.loads(jz.read(f"assets/{ns}/sounds.json").decode("utf-8"))
        sound_defs[ns] = sj
        out = os.path.join(DIRS["ext"], ns, "sounds.json")
        w(out, json.dumps(sj, indent=2))
    # en_us lang
    lp = f"assets/{ns}/lang/en_us.json"
    if lp in names:
        lang_by_ns[ns] = json.loads(jz.read(lp).decode("utf-8"))

print("extracted:",
      {ns: (len(textures_by_ns[ns]), len(sounds_by_ns[ns])) for ns in NS_LIST})

# ---------- build registry mapping ----------
def parse_lang(ns):
    lang = lang_by_ns.get(ns, {})
    blocks, items, entities, fluids = {}, {}, {}, {}
    for k, v in lang.items():
        parts = k.split(".")
        if len(parts) < 3:
            continue
        if parts[0] == "block":
            blocks[parts[2]] = v
        elif parts[0] == "item":
            items[parts[2]] = v
        elif parts[0] == "entity":
            entities[parts[2]] = v
        elif parts[0] == "fluid":
            fluids[parts[2]] = v
    return blocks, items, entities, fluids

catalog = {}
tex_lookup = {}   # ns -> {basename_lower: best relpath under textures/}
for ns in NS_LIST:
    base = {}
    for rel in sorted(textures_by_ns[ns]):
        b = os.path.splitext(os.path.basename(rel))[0].lower()
        # prefer textures/block or textures/item
        score = 0
        if rel.startswith("textures/block/"):
            score = 3
        elif rel.startswith("textures/item/"):
            score = 2
        if b not in base or score > base[b][1]:
            base[b] = (rel, score)
    tex_lookup[ns] = {k: v[0] for k, v in base.items()}

mapping = {"source": {"mod": "Create: Aeronautics (bundled)", "loader": "NeoForge",
                      "mc": "1.21.1", "version": MOD_VERSION},
           "namespaces": {}}

def pick_texture(ns, name, kind):
    """Return RP atlas texture path (no extension) for a registry name, or None."""
    n = name.lower()
    rel = tex_lookup[ns].get(n)
    if rel is None:
        for k in sorted(tex_lookup[ns]):
            if n in k:
                rel = tex_lookup[ns][k]
                break
    if rel is None:
        pref = f"textures/{'item' if kind == 'item' else 'block'}/"
        for k in sorted(tex_lookup[ns]):
            if tex_lookup[ns][k].startswith(pref):
                rel = tex_lookup[ns][k]
                break
    if rel is None:
        return None
    return "textures/" + ns + "/" + rel[len("textures/"):-4]

# ---------- copy textures into RP ----------
for ns in NS_LIST:
    for rel in textures_by_ns[ns]:
        s = os.path.join(DIRS["ext"], ns, rel)
        d = os.path.join(DIRS["rp"], "textures", ns, rel[len("textures/"):])
        copy(s, d)

# ---------- copy sounds into RP (Bedrock resolves names under sounds/) ----------
for ns in NS_LIST:
    for rel in sounds_by_ns[ns]:
        s = os.path.join(DIRS["ext"], ns, rel)
        d = os.path.join(DIRS["rp"], "sounds", ns, rel[len("sounds/"):])
        copy(s, d)

print("copied textures/sounds into RP")

# ---------- semantics helpers ----------
EQUIP = ["goggles", "goggle", "staff", "diagram"]
def menu_cat_item(name):
    return "equipment" if any(e in name for e in EQUIP) else "items"

# ---------- generate BP + RP content ----------
terrain_data, item_data = {}, {}
lang_lines = []
stats = {"blocks": 0, "items": 0, "entities": 0}

for ns in NS_LIST:
    blocks, items, entities, fluids = parse_lang(ns)
    ns_map = {"blocks": {}, "items": {}, "entities": {}, "fluids": {}}

    # --- blocks ---
    for name in sorted(blocks):
        ident = f"{ns}:{name}"
        tex = pick_texture(ns, name, "block")
        key = f"{ns}_{name}"
        if tex:
            terrain_data[key] = {"textures": tex}
        comp = {
            "minecraft:material_instances": {
                "*": {"texture": key if tex else "missing", "render_method": "opaque"}},
            "minecraft:geometry": "minecraft:geometry.full_block",
            "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.0},
            "minecraft:destructible_by_explosion": {"explosion_resistance": 1.0},
            "minecraft:map_color": "#8a8a8a",
        }
        block = {"format_version": "1.21.0", "minecraft:block": {
            "description": {"identifier": ident,
                            "menu_category": {"category": "construction"}},
            "components": comp}}
        w(os.path.join(DIRS["bp"], "blocks", f"{ns}_{name}.json"),
          json.dumps(block, indent=2))
        ns_map["blocks"][name] = {"identifier": ident, "display": blocks[name],
                                  "texture": tex}
        stats["blocks"] += 1

    # --- items ---
    for name in sorted(items):
        if name in blocks:
            continue  # avoid identifier clash with block item form
        ident = f"{ns}:{name}"
        tex = pick_texture(ns, name, "item")
        key = f"{ns}_{name}"
        if tex:
            item_data[key] = {"textures": tex}
        item = {"format_version": "1.21.0", "minecraft:item": {
            "description": {"identifier": ident,
                            "menu_category": {"category": menu_cat_item(name)}},
            "components": {"minecraft:icon": {"texture": key if tex else "missing"},
                           "minecraft:max_stack_size": 64}}}
        w(os.path.join(DIRS["bp"], "items", f"{ns}_{name}.json"),
          json.dumps(item, indent=2))
        ns_map["items"][name] = {"identifier": ident, "display": items[name],
                                 "texture": tex}
        stats["items"] += 1

    # --- entities ---
    for name in sorted(entities):
        ident = f"{ns}:{name}"
        ent = {"format_version": "1.21.0", "minecraft:entity": {
            "description": {"identifier": ident, "is_spawnable": False,
                            "is_summonable": True, "is_experimental": False},
            "components": {
                "minecraft:physics": {},
                "minecraft:collision_box": {"width": 1.0, "height": 1.0},
                "minecraft:health": {"value": 20, "max": 20},
                "minecraft:pushable": {"is_pushable": False},
                "minecraft:movement": {"value": 0.0}}}}
        w(os.path.join(DIRS["bp"], "entities", f"{ns}_{name}.json"),
          json.dumps(ent, indent=2))
        ns_map["entities"][name] = {"identifier": ident, "display": entities[name]}
        stats["entities"] += 1

    # --- lang ---
    for name, disp in sorted(blocks.items()):
        lang_lines.append(f"tile.{ns}:{name}.name={disp}")
    for name, disp in sorted(items.items()):
        if name in blocks:
            continue
        lang_lines.append(f"item.{ns}:{name}.name={disp}")
    for name, disp in sorted(entities.items()):
        lang_lines.append(f"entity.{ns}:{name}.name={disp}")

    ns_map["fluids"] = fluids
    mapping["namespaces"][ns] = ns_map

print("generated registry:", stats)

# ---------- lang file ----------
w(os.path.join(DIRS["rp"], "texts", "en_US.lang"), "\n".join(lang_lines) + "\n")
w(os.path.join(DIRS["rp"], "texts", "languages.json"), json.dumps(["en_US"], indent=2))

# ---------- texture atlases ----------
w(os.path.join(DIRS["rp"], "textures", "terrain_texture.json"),
  json.dumps({"resource_pack_name": "create_aeronautics",
              "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4,
              "texture_data": terrain_data}, indent=2))
w(os.path.join(DIRS["rp"], "textures", "item_texture.json"),
  json.dumps({"resource_pack_name": "create_aeronautics",
              "texture_name": "atlas.items",
              "texture_data": item_data}, indent=2))

# ---------- sound definitions ----------
sdefs = {"format_version": "1.14.0", "sound_definitions": {}}
for ns in NS_LIST:
    for event, val in sorted(sound_defs.get(ns, {}).items()):
        raw = val.get("sounds", val) if isinstance(val, dict) else val
        names = []
        for s in raw:
            if isinstance(s, dict):
                s = s.get("name", "")
            s = s.split(":")[-1]
            names.append({"name": f"sounds/{ns}/{s}", "stream": False})
        if names:
            sdefs["sound_definitions"][f"{ns}.{event}"] = {
                "category": "neutral", "sounds": names}
w(os.path.join(DIRS["rp"], "sounds", "sound_definitions.json"),
  json.dumps(sdefs, indent=2))

# ---------- mapping json ----------
mapping["totals"] = stats
w(os.path.join(DIRS["map"], "registry.json"),
  json.dumps(mapping, indent=2, ensure_ascii=False))

# ---------- manifests ----------
bp_manifest = {
    "format_version": 2,
    "header": {
        "name": "Create Aeronautics [Behavior]",
        "description": f"Bedrock port scaffold of Create: Aeronautics (NeoForge 1.21.1 v{MOD_VERSION}).",
        "uuid": du("bp-header"), "version": PACK_VERSION,
        "min_engine_version": MIN_ENGINE},
    "modules": [{"type": "data", "uuid": du("bp-data"), "version": PACK_VERSION}],
    "metadata": {"authors": ["erinthegato", "Simulated Team (original)"], "license": "MIT"},
}
rp_manifest = {
    "format_version": 2,
    "header": {
        "name": "Create Aeronautics [Resources]",
        "description": f"Textures, sounds and lang extracted from Create: Aeronautics v{MOD_VERSION}.",
        "uuid": du("rp-header"), "version": PACK_VERSION,
        "min_engine_version": MIN_ENGINE},
    "modules": [{"type": "resources", "uuid": du("rp-resources"), "version": PACK_VERSION}],
    "metadata": {"authors": ["erinthegato", "Simulated Team (original)"], "license": "MIT"},
}
w(os.path.join(DIRS["bp"], "manifest.json"), json.dumps(bp_manifest, indent=2))
w(os.path.join(DIRS["rp"], "manifest.json"), json.dumps(rp_manifest, indent=2))
print("manifests written")

# ---------- package .mcaddon ----------
os.makedirs(DIRS["dist"], exist_ok=True)
mcaddon = os.path.join(DIRS["dist"], "create-aeronautics-bedrock.mcaddon")
if os.path.exists(mcaddon):
    os.remove(mcaddon)
with zipfile.ZipFile(mcaddon, "w", zipfile.ZIP_DEFLATED) as z:
    for pack_name, pack_dir in [("create_aeronautics_bp", DIRS["bp"]),
                                ("create_aeronautics_rp", DIRS["rp"])]:
        for base, _dirs, files in os.walk(pack_dir):
            for fn in files:
                full = os.path.join(base, fn)
                arc = os.path.join(pack_name, os.path.relpath(full, pack_dir))
                z.write(full, arc)
print("packaged:", mcaddon, os.path.getsize(mcaddon), "bytes")

# ---------- README ----------
README = f"""# Create: Aeronautics - Bedrock Port (scaffold)

Bedrock addon port scaffold for **Create: Aeronautics** - the bundled NeoForge 1.21.1
mod (v{MOD_VERSION}) that ships **Simulated + Aeronautics + Offroad**.

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
| Blocks  | {stats['blocks']} |
| Items   | {stats['items']} |
| Entities| {stats['entities']} |
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
"""
w(os.path.join(REPO, "README.md"), README)

# ---------- LICENSE (MIT) ----------
LICENSE = """MIT License

Copyright (c) 2026 erinthegato

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
w(os.path.join(REPO, "LICENSE"), LICENSE)

# ---------- .gitignore ----------
GITIGNORE = """# build / temp artifacts
build/
out/
*.pyc
__pycache__/
.DS_Store
Thumbs.db
*.tmp

# do NOT ignore the packaged deliverable
!dist/*.mcaddon
"""
w(os.path.join(REPO, ".gitignore"), GITIGNORE)
print("README / LICENSE / .gitignore written")

# ---------- docs ----------
MAPPING_MD = """# Registry Mapping (Java -> Bedrock)

`mapping/registry.json` is the machine-readable map. Each Bedrock identifier uses the
**same namespace + path** as the Java registry name.

| Java (NeoForge)              | Bedrock identifier            |
|------------------------------|-------------------------------|
| `aeronautics:wooden_propeller` | `aeronautics:wooden_propeller` |
| `simulated:altitude_sensor`    | `simulated:altitude_sensor`    |
| `offroad:wheel_mount`          | `offroad:wheel_mount`          |

## Texture resolution
- Block texture: `assets/<ns>/textures/block/<name>.png` -> atlas key `<ns>_<name>`.
- Item texture:  `assets/<ns>/textures/item/<name>.png`  -> atlas key `<ns>_<name>`.
- Fallback: first texture under `textures/block` (blocks) or `textures/item` (items).

## Languages
Java lang keys `block.<ns>.<name>` / `item.<ns>.<name>` / `entity.<ns>.<name>`
become Bedrock `tile.<ns>:<name>.name`, `item.<ns>:<name>.name`,
`entity.<ns>:<name>.name` in `texts/en_US.lang`.
"""
w(os.path.join(DIRS["docs"], "MAPPING.md"), MAPPING_MD)

NOTES = """# Porting Notes

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
"""
w(os.path.join(DIRS["docs"], "PORTING_NOTES.md"), NOTES)
print("docs written")





