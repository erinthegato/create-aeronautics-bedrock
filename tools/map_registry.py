import json, os, re, collections

OUT = os.path.abspath("_extracted")
NS = ["aeronautics", "simulated", "offroad"]

registry = {}
for ns in NS:
    with open(os.path.join(OUT, f"lang_{ns}_en_us.json"), encoding="utf-8") as f:
        lang = json.load(f)
    blocks, items, entities, fluids, others = {}, {}, {}, {}, {}
    for k, v in lang.items():
        parts = k.split(".")
        if k.startswith("block.") and len(parts) >= 3:
            blocks[parts[2]] = v
        elif k.startswith("item.") and len(parts) >= 3:
            items[parts[2]] = v
        elif k.startswith("entity.") and len(parts) >= 3:
            entities[parts[2]] = v
        elif k.startswith("fluid.") and len(parts) >= 3:
            fluids[parts[2]] = v
    registry[ns] = {
        "blocks": blocks,
        "items": items,
        "entities": entities,
        "fluids": fluids,
    }
    print(f"\n===== {ns} =====")
    print(f"BLOCKS ({len(blocks)}): {sorted(blocks)}")
    print(f"ITEMS ({len(items)}): {sorted(items)}")
    print(f"ENTITIES ({len(entities)}): {entities}")
    print(f"FLUIDS ({len(fluids)}): {fluids}")

with open(os.path.join(OUT, "_registry.json"), "w", encoding="utf-8") as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)

tot_b = sum(len(r["blocks"]) for r in registry.values())
tot_i = sum(len(r["items"]) for r in registry.values())
tot_e = sum(len(r["entities"]) for r in registry.values())
print(f"\nTOTALS: blocks={tot_b} items={tot_i} entities={tot_e}")
