# Combine every per-layer *_landmarks_v2.json into one bone_landmarks_v2.json
# (the engine loads only that file; boneId -> owner object of ANY kind, and
#  landmarkShouldBeVisible keys visibility off that owner's layer checkbox).
import json, io, os
BUILD=r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build"

SRC = {
  "skeleton_landmarks_v2.json": "boneId",
  "muscle_landmarks_v2.json":   "muscleId",
  "organs_landmarks_v2.json":   "ownerId",
  "nerves_landmarks_v2.json":   "ownerId",
  "brain_landmarks_v2.json":    "ownerId",
  "lymph_landmarks_v2.json":    "ownerId",
}
out=[]
for fn,key in SRC.items():
    p=os.path.join(BUILD,fn)
    if not os.path.exists(p):
        print("skip (missing):",fn); continue
    data=json.load(open(p,encoding="utf-8"))
    for d in data:
        rec={"boneId":d[key],"pl":d.get("pl",d.get("en","")),"en":d.get("en",""),
             "pos":d["pos"],"approx":d.get("approx",False)}
        for extra in ("dist_mm","route","kind"):
            if extra in d: rec[extra]=d[extra]
        out.append(rec)
    print(f"  {fn}: +{len(data)}")
json.dump(out, io.open(os.path.join(BUILD,"bone_landmarks_v2.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"total combined landmarks: {len(out)}")
