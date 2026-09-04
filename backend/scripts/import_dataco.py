from pathlib import Path

import pandas as pd
from sqlalchemy import insert

from app.core.database import SessionLocal
from app.models import Shipment


# Project root
BASE_DIR = Path(__file__).resolve().parents[1]

# Processed DataCo dataset
DATA_FILE = BASE_DIR / "datasets" / "processed" / "dataco_features.csv"


def import_dataco_shipments():
    print(f"Reading dataset: {DATA_FILE}")

    # Only import fields that belong to the shipments table.
    columns = [
        "order_item_id",
        "order_id",
        "shipping_mode",
        "order_status",
        "customer_segment",
        "market",
        "order_region",
        "sales",
        "order_profit_per_order",
        "order_item_quantity",
        "days_for_shipment_scheduled",
        "latitude",
        "longitude",
    ]

    df = pd.read_csv(
        DATA_FILE,
        usecols=columns
    )

    print(f"Rows loaded: {len(df)}")

    # order_item_id is our source for the unique shipment reference.
    df = df.dropna(
        subset=["order_item_id"]
    )

    records = []

    for row in df.itertuples(index=False):
        records.append(
            {
                "shipment_reference": f"DC-{int(row.order_item_id)}",

                "order_id": (
                    str(int(row.order_id))
                    if pd.notna(row.order_id)
                    else None
                ),

                "shipping_mode": row.shipping_mode,

                "shipment_status": row.order_status,

                "customer_segment": row.customer_segment,

                "market": row.market,

                "order_region": row.order_region,

                "sales": row.sales,

                "profit_per_order": row.order_profit_per_order,

                "quantity": (
                    int(row.order_item_quantity)
                    if pd.notna(row.order_item_quantity)
                    else None
                ),

                "scheduled_shipping_days": (
                    int(row.days_for_shipment_scheduled)
                    if pd.notna(row.days_for_shipment_scheduled)
                    else None
                ),

                "current_latitude": row.latitude,

                "current_longitude": row.longitude,
            }
        )

    print(f"Records prepared: {len(records)}")

    db = SessionLocal()

    try:
        db.execute(
            insert(Shipment),
            records
        )

        db.commit()

        print(
            f"Successfully imported {len(records)} shipments."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_dataco_shipments()


# python -m scripts.import_dataco (from backend folder)
# psql -U postgres -d cargopulse_ai 