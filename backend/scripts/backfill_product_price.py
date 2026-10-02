from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.core.database import SessionLocal


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    BASE_DIR
    / "datasets"
    / "processed"
    / "dataco_features.csv"
)


def backfill_product_price():
    print(f"Reading dataset: {DATA_FILE}")

    df = pd.read_csv(
        DATA_FILE,
        usecols=[
            "order_item_id",
            "product_price",
        ]
    )

    df = df.dropna(
        subset=["order_item_id", "product_price"]
    )

    records = [
        {
            "shipment_reference": f"DC-{int(row.order_item_id)}",
            "product_price": float(row.product_price),
        }
        for row in df.itertuples(index=False)
    ]

    print(f"Prices prepared: {len(records)}")

    db = SessionLocal()

    try:
        db.execute(
            text("""
                UPDATE shipments
                SET product_price = :product_price
                WHERE shipment_reference = :shipment_reference
            """),
            records
        )

        db.commit()

        print(
            f"Successfully updated {len(records)} shipment prices."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_product_price()