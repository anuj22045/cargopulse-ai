import os
import pandas as pd
from sqlalchemy import update

from app.core.database import SessionLocal
from app.models.shipment import Shipment


CSV_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "datasets",
    "processed",
    "dataco_features.csv"
)
BATCH_SIZE = 5000


def main():
    print("Loading DataCo dataset...")

    df = pd.read_csv(CSV_PATH)

    required_columns = [
        "order_item_id",
        "order_hour",
        "order_day_of_week",
        "order_month",
        "is_weekend",
        "order_item_profit_ratio",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in dataset: {missing_columns}"
        )

    df = df[required_columns].copy()

    df["shipment_reference"] = (
        "DC-" + df["order_item_id"].astype(str)
    )

    db = SessionLocal()

    try:
        total = len(df)
        updated = 0

        for start in range(0, total, BATCH_SIZE):
            batch = df.iloc[start:start + BATCH_SIZE]

            for row in batch.itertuples(index=False):
                stmt = (
                    update(Shipment)
                    .where(
                        Shipment.shipment_reference
                        == row.shipment_reference
                    )
                    .values(
                        order_hour=row.order_hour,
                        order_day_of_week=row.order_day_of_week,
                        order_month=row.order_month,
                        is_weekend=row.is_weekend,
                        order_item_profit_ratio=row.order_item_profit_ratio,
                    )
                )

                result = db.execute(stmt)

                if result.rowcount > 0:
                    updated += result.rowcount

            db.commit()

            print(
                f"Processed {min(start + BATCH_SIZE, total):,}"
                f"/{total:,} rows | Updated: {updated:,}"
            )

        print("\nBackfill completed successfully.")
        print(f"Total dataset rows: {total:,}")
        print(f"Total shipments updated: {updated:,}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()