import subprocess, sys, glob, os
HERE=r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2"
BUILD=HERE+r"\build"
for f in glob.glob(BUILD+r"\all_*_labeled_v2.json")+glob.glob(BUILD+r"\*_landmarks_v2.json"):
    os.remove(f)
print("cleaned old json outputs")
steps=[
  ["build_skeleton.py"],
  ["build_muscles.py"],
  ["build_layer.py","CardioVascular41.glb","vessel"],
  ["build_layer.py","VisceralSystem100.glb","organ"],
  ["build_layer.py","NervousSystem100.glb","nerve:brain"],
  ["build_layer.py","LymphoidOrgans100.glb","lymph"],
  ["build_layer.py","Joints100.glb","connective"],
  ["merge_landmarks.py"],
  ["remap_szpilki.py"],
]
for s in steps:
    print(f"\n### {' '.join(s)}")
    r=subprocess.run([sys.executable]+[f"{HERE}\\{s[0]}"]+s[1:],capture_output=True,text=True)
    print(r.stdout[-1500:])
    if r.returncode!=0:
        print("STDERR:",r.stderr[-2000:]); sys.exit(1)
print("\n=== ALL BUILDS OK ===")
