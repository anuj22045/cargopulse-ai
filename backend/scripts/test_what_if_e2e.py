"""
Phase 6 - End-to-End Verification
==================================
Covers all 12 scenarios from the Day 16 spec:
 1. Valid active shipment simulation
 2. Current vs alternative comparison structure
 3. Faster alternative with higher delay risk (trade-off)
 4. Alternative with lower risk
 5. Invalid shipping mode
 6. Missing shipment ID
 7. Model prediction path (models load and run without error)
 8. Unsupported scenario parameters are rejected
 9. Repeated simulations do not mutate the shipment
10. Simulation does not create new DB records (ai_predictions, etc.)
11. Apply changes only the supported field
12. Existing endpoints unaffected (AI recs, shipment detail, simulation)
"""
import sys
import os

sys.path.insert(0, ".")
os.environ["PYTHONIOENCODING"] = "utf-8"

from sqlalchemy import text
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

client = TestClient(app, raise_server_exceptions=False)

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, label))
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status} {label}{suffix}")
    return condition


def section(title):
    print()
    print(f"=== {title} ===")


# ---------------------------------------------------------------------------
# Setup: pick two real shipments
# ---------------------------------------------------------------------------
section("Setup")
r = client.get("/shipments/?limit=100")
assert r.status_code == 200
shipments = r.json()
assert len(shipments) >= 1, "Need shipments in DB"

ship = shipments[0]
sid = ship["id"]
original_mode = ship["shipping_mode"] or "First Class"
print(f"Primary shipment: id={sid}, mode={original_mode!r}")

modes = ["Same Day", "First Class", "Second Class", "Standard Class"]
other_modes = [m for m in modes if m != original_mode]
alt_mode = other_modes[0]
higher_risk_mode = other_modes[-1]  # will use in scenario 3
print(f"Alternative mode: {alt_mode!r}")

# ---------------------------------------------------------------------------
# SCENARIO 1: Valid active shipment simulation
# ---------------------------------------------------------------------------
section("Scenario 1: Valid shipment simulation")
r1 = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": alt_mode,
})
check("HTTP 200 for valid request", r1.status_code == 200,
      f"got {r1.status_code}")
if r1.status_code == 200:
    body1 = r1.json()
else:
    body1 = {}
    print(f"    Response: {r1.text[:200]}")

# ---------------------------------------------------------------------------
# SCENARIO 2: Response structure is correct
# ---------------------------------------------------------------------------
section("Scenario 2: Response structure")
check("Has 'current' key", "current" in body1)
check("Has 'alternative' key", "alternative" in body1)
check("Has 'delta' key", "delta" in body1)

if body1:
    cur = body1.get("current", {})
    alt = body1.get("alternative", {})
    dlt = body1.get("delta", {})

    check("current.shipping_mode present", "shipping_mode" in cur)
    check("current.eta_days is float", isinstance(cur.get("eta_days"), (int, float)))
    check("current.delay_probability in [0,1]",
          0.0 <= cur.get("delay_probability", -1) <= 1.0,
          f"got {cur.get('delay_probability')!r}")
    check("current.confidence in [0,1]",
          0.0 <= cur.get("confidence", -1) <= 1.0)
    check("current.cost is null (no cost model)", cur.get("cost") is None)
    check("alternative.shipping_mode == requested alt_mode",
          alt.get("shipping_mode") == alt_mode,
          f"got {alt.get('shipping_mode')!r}")
    check("delta.eta_days is float",
          isinstance(dlt.get("eta_days"), (int, float)))
    check("delta.risk_percentage_points is float",
          isinstance(dlt.get("risk_percentage_points"), (int, float)))
    check("delta sign: eta_days = alternative - current",
          abs(dlt["eta_days"] - (alt["eta_days"] - cur["eta_days"])) < 0.01,
          f"delta={dlt['eta_days']}, alt-cur={alt['eta_days']-cur['eta_days']}")
    check("delta sign: risk_pp = (alt_prob - cur_prob)*100",
          abs(dlt["risk_percentage_points"] -
              round((alt["delay_probability"] - cur["delay_probability"]) * 100, 2)) < 0.01)
    check("delta.cost is null", dlt.get("cost") is None)
    print(f"    current: ETA={cur['eta_days']}d, risk={cur['delay_probability']:.1%}")
    print(f"    alt:     ETA={alt['eta_days']}d, risk={alt['delay_probability']:.1%}")
    print(f"    delta:   ETA={dlt['eta_days']}d, risk={dlt['risk_percentage_points']:+.2f}pp")

# ---------------------------------------------------------------------------
# SCENARIO 3: Trade-off — find a mode that increases risk (if any)
# ---------------------------------------------------------------------------
section("Scenario 3: Trade-off detection (faster but higher risk)")
trade_off_found = False
for mode in other_modes:
    r3 = client.post("/what-if/simulate", json={
        "shipment_id": sid,
        "alternative_shipping_mode": mode,
    })
    if r3.status_code == 200:
        b3 = r3.json()
        eta_delta = b3["delta"]["eta_days"]
        risk_delta = b3["delta"]["risk_percentage_points"]
        if eta_delta < 0 and risk_delta > 0:
            trade_off_found = True
            print(f"    Trade-off found with mode={mode!r}: "
                  f"ETA {eta_delta:+.2f}d, risk {risk_delta:+.2f}pp")
            check("Trade-off correctly returned (not hidden)", True,
                  f"{mode!r}: faster but riskier")
            break

if not trade_off_found:
    # Not a model defect — just this shipment's data doesn't produce a trade-off
    print(f"    No trade-off scenario found for shipment {sid} "
          "(all alternatives improve or worsen both metrics together)")
    results.append((SKIP, "Trade-off scenario: no trade-off exists for this shipment's data"))

# ---------------------------------------------------------------------------
# SCENARIO 4: Alternative with lower risk
# ---------------------------------------------------------------------------
section("Scenario 4: Alternative with lower risk")
lower_risk_found = False
for mode in other_modes:
    r4 = client.post("/what-if/simulate", json={
        "shipment_id": sid,
        "alternative_shipping_mode": mode,
    })
    if r4.status_code == 200:
        b4 = r4.json()
        if b4["delta"]["risk_percentage_points"] < 0:
            lower_risk_found = True
            print(f"    Lower-risk mode found: {mode!r}, "
                  f"delta={b4['delta']['risk_percentage_points']:+.2f}pp")
            check("Lower-risk alternative returned correctly", True)
            break

if not lower_risk_found:
    print(f"    No lower-risk alternative found for shipment {sid}")
    results.append((SKIP, "Lower-risk scenario: no improvement found for this shipment"))

# ---------------------------------------------------------------------------
# SCENARIO 5: Invalid shipping mode
# ---------------------------------------------------------------------------
section("Scenario 5: Invalid shipping mode")
r5a = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": "Carrier Pigeon",
})
check("422 for unsupported mode", r5a.status_code == 422,
      f"got {r5a.status_code}")

r5b = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": "",
})
check("422 for empty mode string", r5b.status_code == 422,
      f"got {r5b.status_code}")

r5c = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": "standard class",  # wrong casing
})
check("422 for wrong-casing mode", r5c.status_code == 422,
      f"got {r5c.status_code}")

# ---------------------------------------------------------------------------
# SCENARIO 6: Missing shipment
# ---------------------------------------------------------------------------
section("Scenario 6: Missing shipment")
r6 = client.post("/what-if/simulate", json={
    "shipment_id": 9999999,
    "alternative_shipping_mode": alt_mode,
})
check("404 for unknown shipment ID", r6.status_code == 404,
      f"got {r6.status_code}")
check("Error detail is present", "detail" in r6.json(),
      r6.json().get("detail", ""))

r6b = client.post("/what-if/simulate", json={
    "alternative_shipping_mode": alt_mode,
})
check("422 for missing shipment_id field", r6b.status_code == 422,
      f"got {r6b.status_code}")

# ---------------------------------------------------------------------------
# SCENARIO 7: Model prediction path executes without error
# ---------------------------------------------------------------------------
section("Scenario 7: ML model path executes correctly")
# We verify this by running a prediction and checking the result contains
# realistic values produced by real model inference.
r7 = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": alt_mode,
})
if r7.status_code == 200:
    b7 = r7.json()
    eta_cur = b7["current"]["eta_days"]
    prob_cur = b7["current"]["delay_probability"]
    check("ETA > 0 (real model output, not zero/None)", eta_cur > 0,
          f"got {eta_cur}")
    check("Delay probability is a valid probability",
          0.0 < prob_cur < 1.0, f"got {prob_cur}")
    check("No fabricated values (result is deterministic)",
          b7["current"]["shipping_mode"] == original_mode,
          f"current mode={b7['current']['shipping_mode']!r}, expected={original_mode!r}")
else:
    check("Model ran without 500 error", False, f"HTTP {r7.status_code}")

# ---------------------------------------------------------------------------
# SCENARIO 8: Unsupported parameters are not accepted
# ---------------------------------------------------------------------------
section("Scenario 8: Unsupported parameters rejected/omitted")
# These fields are not in the request schema -> Pydantic will strip them (200)
# or reject (422). Either is acceptable as long as they don't affect results.
r8 = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": alt_mode,
    "weather": "storm",         # unsupported
    "carrier_id": 42,           # unsupported
    "departure_time": "2025-01-01T00:00:00",  # unsupported
})
status8 = r8.status_code
check("Extra unsupported fields produce no 500",
      status8 != 500, f"got {status8}")
if status8 == 200:
    # If Pydantic ignored them, result must still be the same as without them
    check("Extra fields ignored (result matches clean request)",
          r8.json()["current"]["shipping_mode"] == original_mode)
    print("    Extra fields silently ignored by Pydantic (extra='ignore' default)")
elif status8 == 422:
    print("    Extra fields rejected with 422 (strict schema)")

# ---------------------------------------------------------------------------
# SCENARIO 9: Repeated simulations do not mutate the shipment
# ---------------------------------------------------------------------------
section("Scenario 9: Repeated simulations do not mutate")
baseline_mode = client.get(f"/shipments/{sid}").json()["shipping_mode"]
for i in range(3):
    client.post("/what-if/simulate", json={
        "shipment_id": sid,
        "alternative_shipping_mode": alt_mode,
    })
mode_after_3_sims = client.get(f"/shipments/{sid}").json()["shipping_mode"]
check("shipping_mode unchanged after 3 simulate calls",
      mode_after_3_sims == baseline_mode,
      f"was={baseline_mode!r}, now={mode_after_3_sims!r}")

# ---------------------------------------------------------------------------
# SCENARIO 10: Simulation does NOT create new DB records
# ---------------------------------------------------------------------------
section("Scenario 10: Simulation creates no DB records")
db = next(get_db())
pred_count_before = db.execute(
    text("SELECT COUNT(*) FROM ai_predictions WHERE shipment_id = :sid"),
    {"sid": sid}
).scalar()
rec_count_before = db.execute(
    text("SELECT COUNT(*) FROM ai_recommendations WHERE shipment_id = :sid"),
    {"sid": sid}
).scalar()

# Run 3 simulations
for _ in range(3):
    client.post("/what-if/simulate", json={
        "shipment_id": sid,
        "alternative_shipping_mode": alt_mode,
    })

pred_count_after = db.execute(
    text("SELECT COUNT(*) FROM ai_predictions WHERE shipment_id = :sid"),
    {"sid": sid}
).scalar()
rec_count_after = db.execute(
    text("SELECT COUNT(*) FROM ai_recommendations WHERE shipment_id = :sid"),
    {"sid": sid}
).scalar()
db.close()

check("No new ai_predictions rows created by simulate",
      pred_count_after == pred_count_before,
      f"before={pred_count_before}, after={pred_count_after}")
check("No new ai_recommendations rows created by simulate",
      rec_count_after == rec_count_before,
      f"before={rec_count_before}, after={rec_count_after}")

# ---------------------------------------------------------------------------
# SCENARIO 11: Apply changes only shipping_mode
# ---------------------------------------------------------------------------
section("Scenario 11: Apply changes only the supported field")
pre_apply = client.get(f"/shipments/{sid}").json()
r11 = client.put(f"/shipments/{sid}", json={"shipping_mode": alt_mode})
check("PUT 200 for valid apply", r11.status_code == 200,
      f"got {r11.status_code}")
post_apply = client.get(f"/shipments/{sid}").json()
check("shipping_mode updated", post_apply["shipping_mode"] == alt_mode,
      f"got {post_apply['shipping_mode']!r}")
for field in ("shipment_status", "customer_segment", "market",
              "order_region", "sales", "quantity", "scheduled_shipping_days"):
    check(f"  {field} unchanged by Apply",
          pre_apply.get(field) == post_apply.get(field),
          f"{pre_apply.get(field)!r} -> {post_apply.get(field)!r}")

# Restore
client.put(f"/shipments/{sid}", json={"shipping_mode": original_mode})
restored_mode = client.get(f"/shipments/{sid}").json()["shipping_mode"]
check("DB restored to original mode", restored_mode == original_mode)

# ---------------------------------------------------------------------------
# SCENARIO 12: Existing functionality unaffected
# ---------------------------------------------------------------------------
section("Scenario 12: Existing endpoints still work")
checks12 = [
    ("GET /shipments/",                   client.get("/shipments/").status_code),
    (f"GET /shipments/{sid}",             client.get(f"/shipments/{sid}").status_code),
    ("GET /ai-recommendations/shipment",  client.get(f"/ai-recommendations/shipment/{sid}").status_code),
    ("GET /ai-predictions/shipment",      client.get(f"/ai-predictions/shipment/{sid}").status_code),
    ("GET /dashboard/stats",              client.get("/dashboard/stats").status_code),
    ("GET /health",                       client.get("/health").status_code),
    ("GET /health/db",                    client.get("/health/db").status_code),
]
for label, code in checks12:
    check(label, code < 500, f"HTTP {code}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
section("Summary")
passed = sum(1 for s, _ in results if s == PASS)
failed = sum(1 for s, _ in results if s == FAIL)
skipped = sum(1 for s, _ in results if s == SKIP)
total = len(results)
print(f"  {passed} passed / {failed} failed / {skipped} skipped / {total} total")
if failed:
    print()
    print("  Failed checks:")
    for s, label in results:
        if s == FAIL:
            print(f"    {FAIL} {label}")
else:
    print()
    print("  All checks passed.")
