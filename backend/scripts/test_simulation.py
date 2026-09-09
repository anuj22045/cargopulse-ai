from app.core.database import SessionLocal
from app.models.shipment import Shipment
from app.simulation.shipment_simulator import simulate_shipment


db = SessionLocal()

try:
    shipment = db.query(Shipment).filter(
        Shipment.id == 1
    ).first()

    if not shipment:
        print("Shipment not found")
    else:
        simulate_shipment(
            db=db,
            shipment=shipment,
            scenario="normal_day",
            operational_scenario="normal_day",
            elapsed_minutes=30,
            tick_minutes=30,
        )

        print("Simulation tick completed successfully")

finally:
    db.close()