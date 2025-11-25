import pandas as pd
from joblib import load
from sqlalchemy import text
import os

from db import engine

# === Model ===
BASE_DIR = os.path.dirname(__file__)  # folder where ml_model.py lives
MODEL_PATH = os.path.join(BASE_DIR, "models", "isolation_forest_sitepro.joblib")

iso_model = load(MODEL_PATH)

# The features the Isolation Forest was trained on
FEATURE_COLS = ["Frequency", "OutputCurrent", "OutputVoltage", "Pressure"]

# === Sensor mapping (from your notebook) ===
SENSOR_TO_FEATURE = {
    31487: "Pressure(psi)",
    31488: "Flowrate(gal/min)",
    31489: "Conductivity",
    31538: "Flowrate(gal/min)",
    40353: "Flowrate(gal/min)",
    40355: "Frequency(Hz)",
    42648: "Pressure(psi)",
}
SENSOR_IDS = list(SENSOR_TO_FEATURE.keys())

# Convenience: the exact column name we want for conductivity
CONDUCTIVITY_COL = "Conductivity_31489"


# --------------------------------------------------
# 1) Pump logs
# --------------------------------------------------
def fetch_pump_logs(limit: int = 50000) -> pd.DataFrame:
    """
    Fetch recent PumpLogs rows for the pumps being monitored.
    Only columns needed for the model + display.
    """
    query = f"""
        SELECT TOP ({limit})
            Frequency,
            OutputCurrent,
            OutputVoltage,
            Pressure,
            PumpLogDate,
            SitePumpID,
            Name
        FROM PumpLogs
        WHERE PumpLogDate >= '2025-01-01'
        ORDER BY PumpLogDate DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)

    return df


# --------------------------------------------------
# 2) Sensor logs → pivoted feature columns
# --------------------------------------------------
def fetch_sensor_features() -> pd.DataFrame:
    """
    Fetch sensor time series for the sensor IDs in SENSOR_TO_FEATURE and
    pivot them into feature columns like 'Conductivity_31489', etc.,
    using LogDateTimeFixed.
    """
    id_list = ", ".join(str(sid) for sid in SENSOR_IDS)

    q = text(f"""
        SELECT
            SensorID,
            Value,
            DATEADD(year, 1600, LogDateTime) AS LogDateTimeFixed
        FROM SensorLogs
        WHERE SensorID IN ({id_list})
          AND DATEADD(year, 1600, LogDateTime) >= '2025-01-01'
        ORDER BY LogDateTimeFixed
    """)

    with engine.connect() as conn:
        df = pd.read_sql_query(q, conn)

    if df.empty:
        return pd.DataFrame(columns=["SensorTime"])

    # Map each row to a feature label, e.g. "Conductivity_31489"
    df["feature_name"] = df["SensorID"].map(SENSOR_TO_FEATURE)
    df["feature_col"] = df["feature_name"] + "_" + df["SensorID"].astype(str)

    # Pivot: one row per timestamp, one column per feature_col
    piv = (
        df.pivot_table(
            index="LogDateTimeFixed",
            columns="feature_col",
            values="Value",
            aggfunc="last",
        )
        .reset_index()
        .rename(columns={"LogDateTimeFixed": "SensorTime"})
    )

    return piv


def merge_pump_and_sensors(pump_df: pd.DataFrame) -> pd.DataFrame:
    """
    Time-align sensor features (like conductivity) with PumpLogs using nearest
    timestamps. For now we mainly care about Conductivity_31489 for display.
    """
    sensor_df = fetch_sensor_features()

    if sensor_df.empty:
        # No sensor data; just return pump_df with a Conductivity column set to None
        pump_df[CONDUCTIVITY_COL] = None
        return pump_df

    pump_sorted = pump_df.sort_values("PumpLogDate")
    sensor_sorted = sensor_df.sort_values("SensorTime")

    merged = pd.merge_asof(
        pump_sorted,
        sensor_sorted,
        left_on="PumpLogDate",
        right_on="SensorTime",
        direction="nearest",
        tolerance=pd.Timedelta("2min"),
    )

    merged.drop(columns=["SensorTime"], inplace=True, errors="ignore")

    # For convenience, also expose a simple 'Conductivity' alias if the column exists
    if CONDUCTIVITY_COL in merged.columns:
        merged["Conductivity"] = merged[CONDUCTIVITY_COL]
    else:
        merged["Conductivity"] = None

    return merged


# --------------------------------------------------
# 3) Main entry: detect anomalies
# --------------------------------------------------

EXPLANATION_FEATURES = ["Frequency", "OutputCurrent", "OutputVoltage", "Pressure"]

def build_feature_stats(df):
    """
    Compute mean and std for each feature, used to generate explanations.
    """
    stats = {}
    for col in EXPLANATION_FEATURES:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            if std == 0 or pd.isna(std):
                std = 1.0  # avoid division by zero
            stats[col] = {"mean": mean, "std": std}
    return stats


def explain_row(row, stats):
    """
    Find the feature with largest z-score and generate a short text reason.
    """
    deviations = []

    for col in EXPLANATION_FEATURES:
        if col in stats and col in row:
            mean = stats[col]["mean"]
            std = stats[col]["std"]
            z = (row[col] - mean) / std
            deviations.append((col, z))

    if not deviations:
        return "Anomalous behavior detected across pump signals."

    # pick feature with largest absolute z-score
    col, z = max(deviations, key=lambda x: abs(x[1]))
    direction = "high" if z > 0 else "low"

    if col == "Frequency":
        if direction == "high":
            return "Frequency is significantly higher than typical values."
        else:
            return "Frequency dropped lower than usual or towards zero."

    if col == "OutputCurrent":
        if direction == "high":
            return "Output current is unusually high compared to normal operation."
        else:
            return "Output current is unusually low, indicating possible pump stall or no-load."

    if col == "OutputVoltage":
        if direction == "high":
            return "Output voltage spikes above its normal range."
        else:
            return "Output voltage is lower than typical operating levels."

    if col == "Pressure":
        if direction == "high":
            return "Discharge pressure is higher than normal, suggesting possible blockage or restriction."
        else:
            return "Discharge pressure is lower than normal, suggesting leak, cavitation, or no-flow condition."

    return "Anomalous behavior detected across pump signals."


def detect_anomalies(limit: int = 50000):
    """
    Run Isolation Forest on recent PumpLogs and return a list of
    anomalies with severity and textual explanations.
    """
    pump_df = fetch_pump_logs(limit=limit)
    if pump_df.empty:
        return []

    # If you have conductivity merged in, call that here instead:
    # df = merge_pump_and_sensors(pump_df)
    df = pump_df.copy()

    # Clean & sort
    df = df.sort_values("PumpLogDate")
    df = df.ffill().bfill().fillna(0)

    # Features for the model
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features for model: {missing}")

    X = df[FEATURE_COLS].astype(float)

    # Model inference
    preds = iso_model.predict(X)            # -1 = anomaly, 1 = normal
    scores = iso_model.decision_function(X)

    df["anom_flag"] = (preds == -1).astype(int)
    df["anom_score"] = scores

    # --- severity using quantiles over ALL rows ---
    q_low = df["anom_score"].quantile(0.10)   # bottom 10% -> HIGH
    q_med = df["anom_score"].quantile(0.25)   # bottom 25% -> MEDIUM

    def map_severity(score):
        if score <= q_low:
            return "HIGH"
        elif score <= q_med:
            return "MEDIUM"
        else:
            return "LOW"

    df["severity"] = df["anom_score"].apply(map_severity)

    # Only keep medium / high for the alerts feed
    alerts_df = df.copy()

    # Build stats for explanation
    stats = build_feature_stats(df)

    # Newest first
    alerts_df = alerts_df.sort_values("PumpLogDate", ascending=False)

    # Convert to list[dict] with explanation
    records = []
    for _, row in alerts_df.iterrows():
        reason = explain_row(row, stats)

        records.append({
            "pumpId": int(row["SitePumpID"]),
            "pumpName": row.get("Name"),
            "timestamp": row["PumpLogDate"],
            "frequency": float(row["Frequency"]),
            "current": float(row["OutputCurrent"]),
            "voltage": float(row["OutputVoltage"]),
            "pressure": float(row["Pressure"]),
            # if you have Conductivity column merged in:
            "conductivity": float(row["Conductivity"]) if "Conductivity" in row and pd.notna(row["Conductivity"]) else None,
            "score": float(row["anom_score"]),
            "severity": row["severity"],
            "reason": reason,
        })

    return records


