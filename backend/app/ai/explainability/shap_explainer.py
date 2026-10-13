from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap


# --------------------------------------------------
# Model artifacts
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1] / "ml" / "models"

MODEL_PATH = BASE_DIR / "delay_xgboost_model.joblib"
PREPROCESSOR_PATH = BASE_DIR / "delay_preprocessor.joblib"
BACKGROUND_PATH = BASE_DIR / "delay_shap_background.joblib"


FEATURES = [
    "order_hour",
    "order_day_of_week",
    "order_month",
    "is_weekend",
    "days_for_shipment_scheduled",
    "shipping_mode",
    "market",
    "order_region",
    "customer_segment",
    "sales",
    "order_profit_per_order",
    "order_item_quantity",
    "shipping_mode_delay_rate",
]

CATEGORICAL_FEATURES = [
    "shipping_mode",
    "market",
    "order_region",
    "customer_segment",
]


# --------------------------------------------------
# Load existing trained artifacts
# --------------------------------------------------

model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)
background = joblib.load(BACKGROUND_PATH)


def _to_dense(data) -> np.ndarray:
    """Convert sparse or dense transformed features to NumPy."""
    if hasattr(data, "toarray"):
        data = data.toarray()

    return np.asarray(data, dtype=np.float64)


background = _to_dense(background)

if background.ndim != 2 or background.shape[0] == 0:
    raise ValueError("SHAP background data must be a non-empty 2D array.")

if background.shape[1] != model.n_features_in_:
    raise ValueError(
        "SHAP background feature count does not match the model: "
        f"{background.shape[1]} vs {model.n_features_in_}."
    )


# Probability-space SHAP values are expressed as changes in
# predicted probability relative to the background expectation.
explainer = shap.TreeExplainer(
    model,
    feature_perturbation="tree_path_dependent",
)


# --------------------------------------------------
# Map encoded features back to original input columns
# --------------------------------------------------

TRANSFORMED_FEATURES = list(preprocessor.get_feature_names_out())


def _get_original_feature(transformed_name: str) -> str:
    """Map a transformed column to its original input feature."""

    if transformed_name.startswith("num__"):
        original_name = transformed_name[len("num__"):]

        if original_name in FEATURES:
            return original_name

    elif transformed_name.startswith("cat__"):
        encoded_name = transformed_name[len("cat__"):]

        # Longest-prefix matching avoids ambiguity if feature
        # names share prefixes.
        matches = [
            feature
            for feature in CATEGORICAL_FEATURES
            if encoded_name.startswith(f"{feature}_")
        ]

        if matches:
            return max(matches, key=len)

    raise ValueError(
        f"Cannot map transformed feature to an input feature: "
        f"{transformed_name}"
    )


FEATURE_GROUPS = {
    feature: [
        index
        for index, transformed_name in enumerate(TRANSFORMED_FEATURES)
        if _get_original_feature(transformed_name) == feature
    ]
    for feature in FEATURES
}


if any(not indices for indices in FEATURE_GROUPS.values()):
    raise ValueError(
        "At least one original feature has no matching transformed columns."
    )


# --------------------------------------------------
# Explain one shipment's delay-risk prediction
# --------------------------------------------------

def explain(features: dict) -> dict:
    """
    Explain one shipment's delay-risk prediction.

    Each feature contribution is measured in raw model-margin
    space, not probability space.

    Positive contributions push the model output toward
    higher delay risk; negative contributions push it toward
    lower delay risk.

    The contributions sum with the SHAP baseline to reconstruct
    the model's raw output, within numerical precision.
    """

    missing_features = [
        feature for feature in FEATURES
        if feature not in features
    ]

    if missing_features:
        raise ValueError(
            f"Missing required features: {missing_features}"
        )

    input_data = pd.DataFrame(
        [[features[feature] for feature in FEATURES]],
        columns=FEATURES,
    )

    processed = _to_dense(preprocessor.transform(input_data))

    if processed.shape[1] != model.n_features_in_:
        raise ValueError(
            "Preprocessor output does not match the model's expected "
            f"feature count: {processed.shape[1]} vs "
            f"{model.n_features_in_}."
        )

    shap_result = explainer(processed)
    shap_values = np.asarray(shap_result.values)

    # Handle common SHAP output shapes for classifiers.
    if shap_values.ndim == 3:
        if shap_values.shape[0] != 1:
            raise ValueError("Expected SHAP values for one shipment.")

        if shap_values.shape[-1] == 2:
            # Binary classifier: explain the positive (delay) class.
            values = shap_values[0, :, 1]
        else:
            raise ValueError(
                f"Unexpected classifier SHAP output shape: "
                f"{shap_values.shape}"
            )

    elif shap_values.ndim == 2 and shap_values.shape[0] == 1:
        values = shap_values[0]

    else:
        raise ValueError(
            f"Unexpected SHAP output shape: {shap_values.shape}"
        )

    if len(values) != len(TRANSFORMED_FEATURES):
        raise ValueError(
            "SHAP values and transformed feature names have different lengths."
        )

    # Sum one-hot contributions so each original feature has
    # one signed contribution.
    contributions = {}

    for feature, indices in FEATURE_GROUPS.items():
        contributions[feature] = float(np.sum(values[indices]))

    feature_importances = []

    for feature, value in contributions.items():
        if value > 1e-8:
            impact = "increases risk"
        elif value < -1e-8:
            impact = "decreases risk"
        else:
            impact = "little or no impact"

        feature_importances.append({
            "feature": feature,
            "value": round(value, 6),
            "impact": impact,
        })

    feature_importances.sort(
        key=lambda item: abs(item["value"]),
        reverse=True,
    )

    return {
        "feature_importances": feature_importances
    }