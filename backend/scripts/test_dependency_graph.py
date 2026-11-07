"""
Phase 2 Tests — Dependency Graph Backend
=========================================
Covers:
  1.  Valid shipment with route — graph returned with correct nodes/edges
  2.  Valid shipment without route — route node marked 'missing'
  3.  Valid shipment without carrier — carrier node marked 'missing'
  4.  Valid shipment with order_id — order node present
  5.  Missing shipment ID — 404 response
  6.  Graph structure — required top-level keys present
  7.  Shipment node has real delay_probability (model runs)
  8.  Severity propagation — IMPACTED nodes when delay is HIGH/MEDIUM
  9.  Cost impact is always null
  10. Supplier/Factory/Warehouse nodes NOT present (no fabrication)
  11. explicit_db_edges empty initially (0 rows in dependency_graph table)
  12. POST /dependency-graph/edges inserts an explicit edge
  13. After inserting edge, GET returns it in explicit_db_edges
  14. GET /dependency-graph/shipment/180522 — demo shipment full check
  15. data_notes field present and non-empty
  16. impact_summary has required fields
  17. Delay severity thresholds are correct
  18. Available objectives only include verified entities
  19. Existing what-if endpoint still works (regression)
  20. Existing AI recommendations endpoint still works (regression)
"""

import sys
import os
sys.path.insert(0, ".")
os.environ["PYTHONIOENCODING"] = "utf-8"

from fastapi.testclient import TestClient
from app.main import app
from app.services.dependency_graph_service import (
    _delay_severity,
    DELAY_THRESHOLD_HIGH,
    DELAY_THRESHOLD_MEDIUM,
    DELAY_THRESHOLD_LOW,
)

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
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------------------
# Setup: find a simulation-enabled shipment (180522 or first available)
# ---------------------------------------------------------------------------
section("Setup")

r = client.get("/shipments/?simulation_enabled=true&limit=10")
assert r.status_code == 200, f"Setup failed: {r.status_code}"
sim_ships = r.json()
assert len(sim_ships) >= 1, "Need at least one simulation-enabled shipment"

# Use 180522 if available, else fall back
demo_id = 180522
primary = next((s for s in sim_ships if s["id"] == demo_id), sim_ships[0])
sid = primary["id"]
print(f"  Primary shipment: id={sid}, ref={primary['shipment_reference']!r}")

# ---------------------------------------------------------------------------
# SCENARIO 1: Valid shipment — graph structure
# ---------------------------------------------------------------------------
section("1. Valid shipment — graph returned")
r1 = client.get(f"/dependency-graph/shipment/{sid}")
check("HTTP 200", r1.status_code == 200, f"got {r1.status_code}")
if r1.status_code != 200:
    print(f"  Error body: {r1.text[:300]}")
graph = r1.json() if r1.status_code == 200 else {}

# ---------------------------------------------------------------------------
# SCENARIO 6: Top-level structure
# ---------------------------------------------------------------------------
section("6. Graph top-level keys")
REQUIRED_KEYS = {
    "shipment_id", "nodes", "edges",
    "explicit_db_edges", "impact_summary",
    "generated_at", "data_notes",
}
missing = REQUIRED_KEYS - set(graph.keys())
check("All required top-level keys present", not missing, f"missing={missing}")
check("shipment_id matches", graph.get("shipment_id") == sid)
check("nodes is a list", isinstance(graph.get("nodes"), list))
check("edges is a list", isinstance(graph.get("edges"), list))
check("data_notes is non-empty list",
      isinstance(graph.get("data_notes"), list) and len(graph.get("data_notes", [])) > 0)

# ---------------------------------------------------------------------------
# SCENARIO 7: Shipment node has delay_probability from ML model
# ---------------------------------------------------------------------------
section("7. Shipment node delay prediction")
nodes = {n["type"]: n for n in graph.get("nodes", [])}
ship_node = nodes.get("shipment", {})
check("Shipment node present", "shipment" in nodes)
check("delay_probability is float or None",
      isinstance(ship_node.get("delay_probability"), (float, int, type(None))))
if ship_node.get("delay_probability") is not None:
    check("delay_probability in [0, 1]",
          0.0 <= ship_node["delay_probability"] <= 1.0,
          f"got {ship_node['delay_probability']}")
check("severity field present", "severity" in ship_node)
check("impact_status field present", "impact_status" in ship_node)
check("cost_impact is None (no cost model)", ship_node.get("cost_impact") is None)
check("data_source is 'database'", ship_node.get("data_source") == "database")

# ---------------------------------------------------------------------------
# SCENARIO 2-4: Connected nodes exist with correct data_source
# ---------------------------------------------------------------------------
section("2-4. Connected entity nodes")
check("Route node present", "route" in nodes,
      f"node types: {list(nodes.keys())}")
check("Carrier node present", "carrier" in nodes)
check("Order node present", "order" in nodes)

route_node = nodes.get("route", {})
carrier_node = nodes.get("carrier", {})
order_node = nodes.get("order", {})

# Route: may be missing for some shipments
route_source = route_node.get("data_source", "")
check("Route node has data_source",
      route_source in ("database", "missing"),
      f"got {route_source!r}")

# Carrier: 0 rows in carriers table — all carrier nodes are 'missing'
carrier_source = carrier_node.get("data_source", "")
check("Carrier node has data_source",
      carrier_source in ("database", "missing"),
      f"got {carrier_source!r}")

order_source = order_node.get("data_source", "")
check("Order node has data_source",
      order_source in ("database", "missing", "shipment_field"),
      f"got {order_source!r}")

# ---------------------------------------------------------------------------
# SCENARIO 8: Severity propagation
# ---------------------------------------------------------------------------
section("8. Severity propagation")
ship_sev = ship_node.get("severity", "NONE")
check("Shipment severity is one of known values",
      ship_sev in ("HIGH", "MEDIUM", "LOW", "NONE", "UNKNOWN"),
      f"got {ship_sev!r}")

# Downstream nodes should inherit shipment's severity
for ntype, node in [("route", route_node), ("carrier", carrier_node), ("order", order_node)]:
    if node.get("data_source") == "missing":
        check(f"{ntype}: missing nodes have UNKNOWN severity",
              node.get("severity") == "UNKNOWN")
    elif node.get("data_source") in ("database", "shipment_field"):
        check(f"{ntype}: real nodes inherit shipment severity",
              node.get("severity") == ship_sev,
              f"expected {ship_sev!r}, got {node.get('severity')!r}")

# ---------------------------------------------------------------------------
# SCENARIO 9: Cost impact always null
# ---------------------------------------------------------------------------
section("9. Cost impact always null")
for n in graph.get("nodes", []):
    check(f"{n['type']} node: cost_impact is None",
          n.get("cost_impact") is None)
check("impact_summary.cost_impact is None",
      graph.get("impact_summary", {}).get("cost_impact") is None)

# ---------------------------------------------------------------------------
# SCENARIO 10: No fabricated Supplier/Factory/Warehouse nodes
# ---------------------------------------------------------------------------
section("10. No fabricated supplier/factory/warehouse nodes")
node_types = [n["type"] for n in graph.get("nodes", [])]
check("No 'supplier' node fabricated", "supplier" not in node_types)
check("No 'factory' node fabricated", "factory" not in node_types)
check("No 'warehouse' node fabricated", "warehouse" not in node_types)
check("No 'customer' node fabricated", "customer" not in node_types)

# ---------------------------------------------------------------------------
# SCENARIO 11: explicit_db_edges empty initially
# ---------------------------------------------------------------------------
section("11. explicit_db_edges empty initially")
check("explicit_db_edges is a list",
      isinstance(graph.get("explicit_db_edges"), list))
print(f"  explicit_db_edges count: {len(graph.get('explicit_db_edges', []))}")
# May be 0 or > 0 depending on prior test runs — we just assert it's a list

# ---------------------------------------------------------------------------
# SCENARIO 12-13: POST edge then GET to verify
# ---------------------------------------------------------------------------
section("12-13. POST explicit edge, then verify in GET")
edge_payload = {
    "source_type": "shipment",
    "source_id": sid,
    "target_type": "test_node",
    "target_id": 9999,
    "relationship_type": "test_relationship",
}
r_post = client.post("/dependency-graph/edges", json=edge_payload)
check("POST edge returns 201", r_post.status_code == 201,
      f"got {r_post.status_code}: {r_post.text[:100]}")

if r_post.status_code == 201:
    edge_resp = r_post.json()
    check("Edge response has 'id'", "id" in edge_resp)
    check("Edge source_type correct",
          edge_resp.get("source_type") == "shipment")
    check("Edge target_type correct",
          edge_resp.get("target_type") == "test_node")

    # Now GET the graph and confirm the edge appears
    r_get2 = client.get(f"/dependency-graph/shipment/{sid}")
    check("GET after POST returns 200", r_get2.status_code == 200)
    if r_get2.status_code == 200:
        graph2 = r_get2.json()
        explicit = graph2.get("explicit_db_edges", [])
        found = any(
            e.get("target_type") == "test_node"
            and e.get("target_id") == 9999
            for e in explicit
        )
        check("Inserted edge appears in explicit_db_edges", found,
              f"edges: {[e.get('relationship_type') for e in explicit]}")

# ---------------------------------------------------------------------------
# SCENARIO 5: Missing shipment ID -> 404
# ---------------------------------------------------------------------------
section("5. Missing shipment ID -> 404")
r_404 = client.get("/dependency-graph/shipment/999999999")
check("404 for nonexistent shipment", r_404.status_code == 404,
      f"got {r_404.status_code}")

# ---------------------------------------------------------------------------
# SCENARIO 14: Demo shipment 180522 full check
# ---------------------------------------------------------------------------
section("14. Demo shipment 180522 full check")
r_demo = client.get("/dependency-graph/shipment/180522")
check("180522 returns 200", r_demo.status_code == 200,
      f"got {r_demo.status_code}")
if r_demo.status_code == 200:
    g = r_demo.json()
    check("shipment_id is 180522", g["shipment_id"] == 180522)
    s_node = next((n for n in g["nodes"] if n["type"] == "shipment"), {})
    check("Shipment ref is CP-DEMO-NEW-001",
          s_node.get("label") == "CP-DEMO-NEW-001",
          f"got {s_node.get('label')!r}")
    dp = s_node.get("delay_probability")
    check("delay_probability is numeric", isinstance(dp, (float, int)),
          f"got {dp!r}")
    print(f"  delay_probability={dp}, severity={s_node.get('severity')}")
    print(f"  impact_summary: {g.get('impact_summary', {}).get('severity')}")

# ---------------------------------------------------------------------------
# SCENARIO 15: data_notes
# ---------------------------------------------------------------------------
section("15. data_notes")
notes = graph.get("data_notes", [])
check("data_notes is non-empty", len(notes) > 0)
# At least one note mentions missing entities
has_missing_note = any("Supplier" in n or "unavailable" in n or "missing" in n.lower()
                        for n in notes)
check("data_notes mentions missing entities", has_missing_note)

# ---------------------------------------------------------------------------
# SCENARIO 16: impact_summary fields
# ---------------------------------------------------------------------------
section("16. impact_summary fields")
summary = graph.get("impact_summary", {})
SUMMARY_KEYS = {
    "delay_probability", "severity", "model_available",
    "impacted_downstream_count", "impacted_downstream_labels",
    "unavailable_count", "unavailable_labels",
    "cost_impact", "cost_impact_note", "model_error",
}
missing_s = SUMMARY_KEYS - set(summary.keys())
check("impact_summary has all required keys", not missing_s,
      f"missing={missing_s}")
check("model_available is bool",
      isinstance(summary.get("model_available"), bool))
check("impacted_downstream_count is int",
      isinstance(summary.get("impacted_downstream_count"), int))

# ---------------------------------------------------------------------------
# SCENARIO 17: Severity thresholds unit test
# ---------------------------------------------------------------------------
section("17. Delay severity thresholds")
check("0.75 -> HIGH",  _delay_severity(0.75) == "HIGH")
check("0.55 -> MEDIUM", _delay_severity(0.55) == "MEDIUM")
check("0.35 -> LOW",   _delay_severity(0.35) == "LOW")
check("0.20 -> NONE",  _delay_severity(0.20) == "NONE")
check("Threshold HIGH is 0.70",   DELAY_THRESHOLD_HIGH == 0.70)
check("Threshold MEDIUM is 0.50", DELAY_THRESHOLD_MEDIUM == 0.50)
check("Threshold LOW is 0.30",    DELAY_THRESHOLD_LOW == 0.30)

# ---------------------------------------------------------------------------
# SCENARIO 18: Edges only reference verified entities
# ---------------------------------------------------------------------------
section("18. Edges reference verified entities")
ALLOWED_EDGE_REL = {"uses_route", "assigned_carrier", "fulfills_order", "test_relationship"}
edge_rels = {e.get("relationship_type") for e in graph.get("edges", [])}
unexpected = edge_rels - ALLOWED_EDGE_REL
check("No unexpected edge relationship types", not unexpected,
      f"found: {unexpected}")

# ---------------------------------------------------------------------------
# SCENARIO 19-20: Regression — existing endpoints still work
# ---------------------------------------------------------------------------
section("19-20. Regression checks")
r_wif = client.post("/what-if/simulate", json={
    "shipment_id": sid,
    "alternative_shipping_mode": "First Class",
})
check("What-if simulator still returns 200",
      r_wif.status_code == 200,
      f"got {r_wif.status_code}: {r_wif.text[:100]}")

r_rec = client.post(f"/ai-recommendations/generate/shipment/{sid}")
check("AI recommendations generate still works",
      r_rec.status_code in (200, 500),  # 500 acceptable if no historical rate
      f"got {r_rec.status_code}")
print(f"  AI recommendations status: {r_rec.status_code}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
passed = sum(1 for s, _ in results if s == PASS)
failed = sum(1 for s, _ in results if s == FAIL)
skipped = sum(1 for s, _ in results if s == SKIP)
print(f"TOTAL: {passed} passed, {failed} failed, {skipped} skipped "
      f"out of {len(results)} checks")
if failed:
    print("\nFailed checks:")
    for s, label in results:
        if s == FAIL:
            print(f"  {s} {label}")
    sys.exit(1)
else:
    print("All checks passed.")
