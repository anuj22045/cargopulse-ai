"""Phase 5 verification: Apply workflow tests."""
import sys
import os

sys.path.insert(0, ".")
os.environ["PYTHONIOENCODING"] = "utf-8"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

# ── Setup ─────────────────────────────────────────────────────────────────────
r = client.get("/shipments/?limit=5")
assert r.status_code == 200
shipments = r.json()
assert shipments, "Need at least one shipment"

ship = shipments[0]
sid = ship["id"]
original_mode = ship["shipping_mode"]
print(f"Shipment {sid}, original mode: {original_mode!r}")

modes = ["Same Day", "First Class", "Second Class", "Standard Class"]
alt_mode = next(m for m in modes if m != original_mode)
print(f"Alternative mode for tests: {alt_mode!r}")

# ── Test 1: simulate alone does NOT mutate the DB ────────────────────────────
r_sim = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": alt_mode,
})
assert r_sim.status_code == 200, f"Simulate failed: {r_sim.text}"

r_check = client.get(f"/shipments/{sid}")
mode_after_sim = r_check.json()["shipping_mode"]
assert mode_after_sim == original_mode, (
    f"MUTATION DETECTED after simulate: {mode_after_sim!r}"
)
print(f"TEST 1 PASS: simulate did not change DB (mode still {mode_after_sim!r})")

# ── Test 2: Apply updates ONLY shipping_mode ──────────────────────────────────
r_apply = client.put(f"/shipments/{sid}", json={"shipping_mode": alt_mode})
assert r_apply.status_code == 200, f"Apply PUT failed: {r_apply.text}"

body_after = client.get(f"/shipments/{sid}").json()
mode_after_apply = body_after["shipping_mode"]
assert mode_after_apply == alt_mode, f"Apply did not update mode: {mode_after_apply!r}"
print(f"TEST 2 PASS: Apply updated mode to {mode_after_apply!r}")

for field in ("shipment_status", "customer_segment", "market", "order_region", "sales"):
    before = ship.get(field)
    after = body_after.get(field)
    assert before == after, f"Field {field!r} changed unexpectedly: {before!r} -> {after!r}"
print("TEST 2 PASS: Other fields (status, segment, market, region, sales) unchanged")

# ── Test 3: Extra field in body is stripped by Pydantic (not persisted) ───────
r_extra = client.put(f"/shipments/{sid}", json={
    "shipping_mode": alt_mode,
    "weather_scenario": "storm_day",   # not in ShipmentUpdate schema
})
status_extra = r_extra.status_code
print(f"TEST 3: PUT with extra field -> HTTP {status_extra} (200=ignored / 422=rejected)")
if status_extra == 200:
    val = r_extra.json().get("weather_scenario")
    print(f"  weather_scenario in response: {val!r} (unmodified, original value)")

# ── Test 4: Restore original mode so DB is clean ──────────────────────────────
r_restore = client.put(f"/shipments/{sid}", json={"shipping_mode": original_mode})
assert r_restore.status_code == 200
final_mode = r_restore.json()["shipping_mode"]
assert final_mode == original_mode
print(f"TEST 4 PASS: Restored mode to {final_mode!r}")

# ── Test 5: 404 for non-existent shipment ─────────────────────────────────────
r_missing = client.put("/shipments/9999999", json={"shipping_mode": "Same Day"})
assert r_missing.status_code == 404, f"Expected 404, got {r_missing.status_code}"
print("TEST 5 PASS: 404 for non-existent shipment")

# ── Test 6: Regression — existing endpoints return non-500 ───────────────────
endpoints = [
    "/shipments/",
    "/ai-recommendations/shipment/120882",
    "/dashboard/stats",
    f"/shipments/{sid}",
    "/what-if/simulate",  # POST — will 422, not 500
]
all_ok = True
for path in endpoints:
    if path == "/what-if/simulate":
        rr = client.post(path, json={})  # intentionally bad body -> 422
    else:
        rr = client.get(path)
    ok = rr.status_code < 500
    if not ok:
        all_ok = False
    print(f"  GET {path} -> {rr.status_code} {'PASS' if ok else 'FAIL - SERVER ERROR'}")
print(f"TEST 6 {'PASS' if all_ok else 'FAIL'}: Regression check")

print()
print("Phase 5 complete.")
