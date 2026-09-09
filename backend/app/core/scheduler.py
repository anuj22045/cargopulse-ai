"""
Simulation Scheduler

Runs the shipment simulation automatically at a fixed interval.
It finds active shipments and advances their simulation state
by one simulation tick.
"""

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.models.shipment import Shipment
from app.simulation.shipment_simulator import simulate_shipment
from app.api.websocket import manager


SIMULATION_INTERVAL_SECONDS = 30
SIMULATION_TICK_MINUTES = 30
SIMULATION_BATCH_SIZE = 50


scheduler = BackgroundScheduler()


def run_simulation_tick():
    """
    Run one simulation tick for active shipments.
    """

    db = SessionLocal()

    try:
        shipments = (
            db.query(Shipment)
            .filter(
                Shipment.simulation_enabled.is_(True),
                (
                    Shipment.distance_remaining_km.is_(None)
                    | (Shipment.distance_remaining_km > 0)
                )
            )
            .limit(SIMULATION_BATCH_SIZE)
            .all()
        )

        if not shipments:
            print("No active shipments found")
            return

        print(
            f"Simulation tick started: "
            f"{len(shipments)} shipments"
        )

        for shipment in shipments:
            elapsed_minutes = (
                shipment.simulation_elapsed_minutes
                + SIMULATION_TICK_MINUTES
            )

            simulation_result = simulate_shipment(
                db=db,
                shipment=shipment,
                scenario="normal_day",
                operational_scenario="normal_day",
                elapsed_minutes=elapsed_minutes,
                tick_minutes=SIMULATION_TICK_MINUTES,
            )
            manager.broadcast_from_sync(
                shipment.id,
                {
                    "type":"shipment_update",
                    **simulation_result,
                }
            )

        print("Simulation tick completed")

    except Exception as error:
        db.rollback()
        print(
            f"Simulation tick failed: {error}"
        )

    finally:
        db.close()


def start_scheduler():
    """
    Start the APScheduler background scheduler.
    """

    if scheduler.running:
        return

    scheduler.add_job(
        run_simulation_tick,
        "interval",
        seconds=SIMULATION_INTERVAL_SECONDS,
        id="shipment_simulation",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()

    print(
        "Simulation scheduler started "
        f"(every {SIMULATION_INTERVAL_SECONDS} seconds)"
    )


def stop_scheduler():
    """
    Stop the APScheduler background scheduler.
    """

    if not scheduler.running:
        return

    scheduler.shutdown()

    print("Simulation scheduler stopped")