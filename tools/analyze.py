import zipfile, os, json, collections, re

ROOT = os.path.abspath(".")
OUT = os.path.join(ROOT, "_extracted")
NS = ["aeronautics", "simulated", "offroad"]

report = {}

for ns in NS:
    jz = zipfile.ZipFile(os.path.join(OUT, ns + ".jar"))
    n = jz.namelist()

    # blockstates
    bs = sorted(x.split("/")[-1][:-5] for x in n
                if x.startswith(f"assets/{ns}/blockstates/") and x.endswith(".json"))
    # item models
    im = sorted(x.split("/")[-1][:-5] for x in n
                if x.startswith(f"assets/{ns}/models/item/") and x.endswith(".json"))
    # block models
    bm = sorted(x.split("/")[-1][:-5] for x in n
                if x.startswith(f"assets/{ns}/models/block/") and x.endswith(".json"))
    # sounds
    snd = [x for x in n if x.startswith(f"assets/{ns}/sounds/") and x.endswith(".ogg")]
    # lang
    langs = [x for x in n if re.match(rf"assets/{ns}/lang/.*\.json$", x)]
    # data folders
    data_sub = collections.Counter()
    for x in n:
        p = x.split("/")
        if len(p) > 3 and p[0] == "data" and p[1] == ns:
            data_sub[p[2]] += 1
    # textures
    tex = [x for x in n if x.startswith(f"assets/{ns}/textures/") and x.endswith(".png")]

    report[ns] = {
        "blockstates": bs,
        "item_models": im,
        "sounds": snd,
        "langs": langs,
        "data_sub": dict(data_sub),
        "textures_count": len(tex),
    }

    print(f"\n############### {ns} ###############")
    print(f"blockstates({len(bs)}):", bs)
    print(f"item_models({len(im)}):", im)
    print(f"sounds({len(snd)}):", len(snd))
    print(f"langs:", langs)
    print(f"data subfolders:", dict(data_sub))
    print(f"textures:", len(tex))

# dump lang contents
def read_lang(jar, path):
    jz = zipfile.ZipFile(jar)
    return json.loads(jz.read(path).decode("utf-8"))

for ns in NS:
    jarp = os.path.join(OUT, ns + ".jar")
    for p in report[ns]["langs"]:
        if p.endswith("en_us.json"):
            data = read_lang(jarp, p)
            print(f"\n===== {ns} en_us ({len(data)} keys) =====")
            # categories
            cats = collections.Counter()
            for k in data:
                cats[k.split(".")[0]] += 1
            print("key prefixes:", dict(cats.most_common(20)))
            with open(os.path.join(OUT, f"lang_{ns}_en_us.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

with open(os.path.join(OUT, "_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("\nOK")
