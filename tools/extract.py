import zipfile, os, collections, json, io

ROOT = os.path.abspath(".")
JAR = os.path.join(ROOT, "create-aeronautics-bundled-1.21.1-1.3.2.jar")
OUT = os.path.join(ROOT, "_extracted")
os.makedirs(OUT, exist_ok=True)

inner = {
    "aeronautics": "META-INF/jarjar/dev.eriksonn.aeronautics.aeronautics-neoforge-1.21.1-1.3.2.jar",
    "offroad": "META-INF/jarjar/dev.ryanhcode.offroad.offroad-neoforge-1.21.1-1.3.2.jar",
    "simulated": "META-INF/jarjar/dev.simulated_team.simulated.simulated-neoforge-1.21.1-1.3.2.jar",
}

z = zipfile.ZipFile(JAR)
for name, path in inner.items():
    data = z.read(path)
    dest = os.path.join(OUT, name + ".jar")
    with open(dest, "wb") as f:
        f.write(data)
    print(f"wrote {dest} ({len(data)} bytes)")

# Now analyze each nested jar
summary = {}
for name in inner:
    p = os.path.join(OUT, name + ".jar")
    jz = zipfile.ZipFile(p)
    n = jz.namelist()
    ext = collections.Counter()
    for x in n:
        if x.endswith("/"):
            continue
        ext[os.path.splitext(x)[1].lower()] += 1
    namespaces = collections.Counter()
    for x in n:
        parts = x.split("/")
        if len(parts) > 1 and parts[0] in ("assets", "data"):
            namespaces[parts[0] + "/" + parts[1]] += 1
    summary[name] = {
        "total": len(n),
        "ext": ext.most_common(20),
        "namespaces": namespaces.most_common(30),
    }
    print(f"\n########## {name}.jar  (entries={len(n)}) ##########")
    print("ext:", dict(ext))
    print("namespaces:")
    for k, v in namespaces.most_common(30):
        print(f"   {v:6d}  {k}")

with open(os.path.join(OUT, "_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=str)
print("\nDone.")
