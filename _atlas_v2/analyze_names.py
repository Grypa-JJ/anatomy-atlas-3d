import trimesh, json, re, collections, sys, io

SRC = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\src"
OUT = r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"

def analyze(fname):
    path = f"{SRC}\\{fname}"
    scene = trimesh.load(path)
    geoms = list(scene.geometry.keys())
    # scene graph: node -> (transform, geometry_name)
    node_geo = {}
    for node in scene.graph.nodes_geometry:
        tf, gname = scene.graph[node]
        node_geo.setdefault(gname, []).append(node)

    suffixes = collections.Counter()
    for g in geoms:
        m = re.search(r'(\.[A-Za-z0-9_]+)+$', g)
        if m:
            # collect each trailing .token
            for tok in re.findall(r'\.[A-Za-z0-9_]+', m.group(0)):
                suffixes[tok] += 1
        else:
            suffixes['<none>'] += 1

    report = {
        "file": fname,
        "n_geometries": len(geoms),
        "n_graph_nodes": len(scene.graph.nodes_geometry),
        "suffix_counts": suffixes.most_common(),
        "sample_names": geoms[:80],
        "all_names_sorted": sorted(geoms),
    }
    with io.open(f"{OUT}\\names_{fname}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    # short console-safe summary
    print(fname, "geoms=", len(geoms), "nodes=", len(scene.graph.nodes_geometry))
    print("  suffixes:", suffixes.most_common(25))

for fn in ("SkeletalSystem100.glb", "MuscularSystem100.glb"):
    analyze(fn)
