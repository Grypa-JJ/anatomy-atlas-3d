import pathlib
p = pathlib.Path(r"C:\Users\Jakub\Desktop\Prod\projekt w budowie\_atlas_v2\build_full\atlas_pilot_v3.html")
s = p.read_text(encoding="utf-8")

# ---- 1. CSS + tooltip ----
if "#lm-tooltip" not in s:
    s = s.replace("</style>", """
  #lm-tooltip {
    position: fixed; z-index: 40; pointer-events: none; display: none;
    background: rgba(20,22,28,0.97); color: #f2f3f5; border: 1.5px solid #e0952e;
    border-radius: 7px; padding: 5px 11px; font: 600 13.5px/1.3 system-ui, sans-serif;
    box-shadow: 0 6px 22px rgba(0,0,0,0.55); max-width: 280px;
    transform: translate(-50%, calc(-100% - 16px)); white-space: nowrap;
  }
  #lm-tooltip .en { color: #97a0ad; font-size: 11px; font-weight: 400; display:block; white-space:normal; }
</style>""", 1)
    s = s.replace('<div id="label-box"', '<div id="lm-tooltip"></div>\n<div id="label-box"', 1)

# ---- 2. give every non-foramen landmark a camera-facing sprite (visual) ----
# keep the tiny sphere as the raycast/click target (engine logic unchanged).
old = """            } else {
                mesh = new THREE.Mesh(
                    new THREE.SphereGeometry(lm.approx ? 3 : 4, 16, 16),
                    new THREE.MeshBasicMaterial({ color, transparent: isApprox, opacity })
                );
                mesh.position.set(lm.pos[0], lm.pos[1], lm.pos[2]);
            }"""
new = """            } else {
                // niewidzialna mala kula = cel raycasta/kliku (logika silnika bez zmian)
                mesh = new THREE.Mesh(
                    new THREE.SphereGeometry(6, 8, 8),
                    new THREE.MeshBasicMaterial({ visible: false })
                );
                mesh.position.set(lm.pos[0], lm.pos[1], lm.pos[2]);
                // widoczny element: sprite 2D zawsze zwrocony do kamery
                const spr = new THREE.Sprite(lmDotMat(color, isApprox, false));
                spr.scale.setScalar(9);
                spr.userData.isLmDot = true;
                mesh.add(spr);
                mesh.userData.dot = spr;
            }"""
assert old in s
s = s.replace(old, new, 1)

helper = """
    // ===== punkty orientacyjne: sprite 2D (kolko) + kolo na hover =====
    const _lmTex = {};
    function _lmTexture(hex, ring) {
        const k = hex + (ring ? "R" : "");
        if (_lmTex[k]) return _lmTex[k];
        const S = 64, cv = document.createElement("canvas"); cv.width = cv.height = S;
        const g = cv.getContext("2d"), col = "#" + hex.toString(16).padStart(6, "0");
        if (ring) { g.strokeStyle = "#ffe066"; g.lineWidth = 6;
            g.beginPath(); g.arc(S/2, S/2, 26, 0, 7); g.stroke(); }
        g.fillStyle = col; g.beginPath(); g.arc(S/2, S/2, ring ? 13 : 16, 0, 7); g.fill();
        g.strokeStyle = "rgba(0,0,0,.5)"; g.lineWidth = 2.5;
        g.beginPath(); g.arc(S/2, S/2, ring ? 13 : 16, 0, 7); g.stroke();
        const t = new THREE.CanvasTexture(cv); _lmTex[k] = t; return t;
    }
    function lmDotMat(hex, approx, ring) {
        return new THREE.SpriteMaterial({ map: _lmTexture(hex, ring), transparent: true,
            opacity: approx ? 0.6 : 1, depthWrite: false, sizeAttenuation: true });
    }
"""
s = s.replace("        allLandmarks = rawLandmarks.filter(lm => !GENERIC_TOUCH_RE.test(lm.pl));",
              helper + "\n        allLandmarks = rawLandmarks.filter(lm => !GENERIC_TOUCH_RE.test(lm.pl));", 1)

# ---- 3. hover tooltip + ring ----
hover = """
// ===== hover na punkcie -> nazwa w ramce + zakreslenie kolem =====
(function () {
    const tip = document.getElementById("lm-tooltip");
    let hovered = null, _last = 0;
    const _r = new THREE.Raycaster(), _p = new THREE.Vector2();
    function setRing(mesh, on) {
        const spr = mesh && mesh.userData && mesh.userData.dot;
        if (!spr) return;
        const l = mesh.userData.landmark;
        spr.material = lmDotMat(on ? 0xffe066
            : (l.approx ? LANDMARK_APPROX_COLOR : LANDMARK_COLOR), l.approx, on);
        spr.scale.setScalar(on ? 12 : 9);
    }
    window.addEventListener("pointermove", (e) => {
        const now = performance.now(); if (now - _last < 25) return; _last = now;
        _p.x = (e.clientX / window.innerWidth) * 2 - 1;
        _p.y = -(e.clientY / window.innerHeight) * 2 + 1;
        _r.setFromCamera(_p, camera);
        const hits = _r.intersectObjects(landmarkMeshes, false).filter(h => h.object.visible);
        const hit = hits[0] ? hits[0].object : null;
        if (hit === hovered) {
            if (hit) { tip.style.left = e.clientX + "px"; tip.style.top = e.clientY + "px"; }
            return;
        }
        if (hovered && hovered !== selectedMesh) setRing(hovered, false);
        hovered = hit;
        if (hit) {
            if (hit !== selectedMesh) setRing(hit, true);
            const l = hit.userData.landmark;
            tip.innerHTML = l.pl + (l.en ? '<span class="en">' + l.en + "</span>" : "");
            tip.style.left = e.clientX + "px"; tip.style.top = e.clientY + "px";
            tip.style.display = "block";
            document.body.style.cursor = "pointer";
        } else {
            tip.style.display = "none";
            document.body.style.cursor = "";
        }
    });
})();
"""
s = s.replace("function animate() {", hover + "\nfunction animate() {", 1)

# ---- 4. sidebar list click: ring the dot + fly camera to the point + label ----
old_click = """                const sphere = landmarkMeshes.find(s => s.userData.landmark === lm);
                if (sphere) {
                    resetSelection();
                    sphere.material.color.setHex(LANDMARK_HIGHLIGHT);
                    selectedMesh = sphere;
                }"""
new_click = """                const sphere = landmarkMeshes.find(s => s.userData.landmark === lm);
                if (sphere) {
                    resetSelection();
                    selectedMesh = sphere;
                    lmRingSelected(sphere);
                    document.getElementById("lbl-pl-text").textContent = lm.pl;
                    document.getElementById("lbl-en").textContent = lm.en;
                    document.getElementById("lbl-id").textContent = "ID: " + lm.boneId + " (punkt)";
                    const w = document.getElementById("lbl-approx-warn"); if (w) w.style.display = lm.approx ? "block" : "none";
                    const lb = document.getElementById("label-box"); if (lb) lb.style.display = "block";
                }"""
assert old_click in s, "sidebar click block not found"
s = s.replace(old_click, new_click, 1)

# helpers used above + in the 3D click handler
lm_util = """
function lmRingSelected(mesh) {
    const spr = mesh && mesh.userData && mesh.userData.dot;
    if (!spr) return;
    spr.material = lmDotMat(0xffe066, false, true);
    spr.scale.setScalar(13);
}
function lmUnring(mesh) {
    const spr = mesh && mesh.userData && mesh.userData.dot;
    if (!spr) return;
    const l = mesh.userData.landmark;
    spr.material = lmDotMat(l.approx ? LANDMARK_APPROX_COLOR : LANDMARK_COLOR, l.approx, false);
    spr.scale.setScalar(9);
}
function lmFlyTo(mesh) {
    const p = new THREE.Vector3(); mesh.getWorldPosition(p);
    const dir = camera.position.clone().sub(controls.target).normalize();
    const dist = Math.max(70, camera.position.distanceTo(controls.target) * 0.55);
    controls.target.copy(p);
    camera.position.copy(p).addScaledVector(dir, dist);
    controls.update();
}
"""
s = s.replace("function animate() {", lm_util + "\nfunction animate() {", 1)

# 3D click on a landmark: also ring + fly (mesh material is now invisible)
s = s.replace(
    "        const mesh = landmarkHits[0].object;\n        mesh.material.color.setHex(LANDMARK_HIGHLIGHT);\n        selectedMesh = mesh;",
    "        const mesh = landmarkHits[0].object;\n        selectedMesh = mesh;\n        lmRingSelected(mesh);", 1)

# resetSelection must un-ring the previously selected dot
s = s.replace("function resetSelection() {",
    "function resetSelection() {\n    if (selectedMesh && selectedMesh.userData && selectedMesh.userData.dot) lmUnring(selectedMesh);", 1)

p.write_text(s, encoding="utf-8")
print("patched. sprite refs:", s.count("lmDotMat"), " tooltip:", "#lm-tooltip" in s, " flyto:", "lmFlyTo" in s)
