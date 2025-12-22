# anomaly_backend/ml_model.py
import os
import pandas as pd
from sqlalchemy import text
from joblib import load

from db import engine

# -----------------------
# Load trained 21-feature bundle
# -----------------------
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "isolation_forest_sitepro_21features.joblib",
)

bundle = load(MODEL_PATH)
MODEL_BY_PUMP = bundle["models"]      # dict: pump_id -> {"model", "scaler"}
FEATURE_COLS = bundle["features"]     # list of 21 feature names

ALLOWED_PUMPS = [47366, 47367, 46962, 48142]  # Well 2, Well 1, Well 17, Injection

# FlowMeterID -> SitePumpID (from training notebook)
FLOWMETER_TO_PUMP = {
    4685: 46962,   # Well 17
    5077: 47366,   # Well 2
    5081: 47367,   # Well 1
    5950: 48142,   # Injection
}

# SensorID -> feature name mapping (matches training)
SENSOR_TO_FEATURE = {
    31487: "Pressure(psi)_31487",
    31488: "Flowrate(gal/min)_31488",
    31489: "Conductivity_31489",
    31538: "Flowrate(gal/min)_31538",
    40353: "Flowrate(gal/min)_40353",
    40355: "Frequency(Hz)_40355",
    42648: "Pressure(psi)_42648",
}

# SensorID -> SitePumpID mapping (site_map1 from training)
site_map1 = {
    28284: 46962, 27464: 46962,
    31486: 47366, 31535: 47367,
    31488: 47366, 31538: 47367,
    27430: 47367, 28283: 47367,
    31487: 47366, 31536: 47367, 31537: 47367,
    31489: 47366,
    32406: 47366, 32407: 47367, 32416: 47367,
    27883: 46962, 27915: 46962,
    37662: 47366, 37669: 46962,
    42648: 48142, 42649: 48142,
    40353: 48142, 40355: 48142,
    38676: 47366, 38681: 47367,
    38730: 46962, 28279: 46962, 28280: 46962,
    29145: 46962, 39324: 46962,
    40352: 48142,
    28281: 46962, 28282: 46962,
}

# -----------------------
# Data fetch
# -----------------------
def fetch_recent_data(limit: int = 200_000):
    """Grab PumpLogs + FlowMeterLogs + SensorLogs needed for features."""
    pump_sql = f"""
        SELECT TOP ({limit})
            Frequency,
            OutputCurrent,
            OutputVoltage,
            Pressure,
            IGBTTemperature,
            PumpLogDate,
            SitePumpID,
            Name
        FROM PumpLogs
        WHERE PumpLogDate >= '2025-01-01'
          AND SitePumpID IN (47366, 47367, 46962, 48142)
        ORDER BY PumpLogDate ASC
    """

    sensor_sql = """
        SELECT
            SensorID,
            SiteID,
            Value,
            ValueUnits,
            DATEADD(year, 1600, LogDateTime) AS LogDateTimeFixed
        FROM SensorLogs
        WHERE DATEADD(year, 1600, LogDateTime) >= '2025-01-01'
          AND SensorID IN (31487,31488,31489,31538,40353,40355,42648)
    """

    flow_sql = """
        SELECT
            FlowMeterID,
            FlowRate,
            LogStartTime
        FROM FlowMeterLogs
        WHERE LogStartTime >= '2025-01-01'
          AND FlowMeterID IN (5950, 5077, 4685, 5081)
        ORDER BY LogStartTime ASC
    """

    with engine.begin() as conn:
        pump_df = pd.read_sql(text(pump_sql), conn)
        sensor_df = pd.read_sql(text(sensor_sql), conn)
        flow_df = pd.read_sql(text(flow_sql), conn)

    return pump_df, sensor_df, flow_df

# -----------------------
# Feature engineering to match 21-feature training
# -----------------------
def build_features_21(limit: int = 200_000) -> pd.DataFrame:
    """Rebuild the 21-feature table for the four pumps."""
    pump_df, sensor_df, flow_df = fetch_recent_data(limit)

    # ----- Pump side -----
    pump_df["PumpLogDate"] = pd.to_datetime(pump_df["PumpLogDate"])
    pump_df = pump_df.sort_values(["SitePumpID", "PumpLogDate"])

    # Align PumpLogs to minute
    pump_df["ts_minute"] = pump_df["PumpLogDate"].dt.floor("T")

    # ----- FlowMeterLogs -> FlowRate -----
    flow_df["LogStartTime"] = pd.to_datetime(flow_df["LogStartTime"])
    flow_df["ts_minute"] = flow_df["LogStartTime"].dt.floor("T")
    flow_df["SitePumpID"] = flow_df["FlowMeterID"].map(FLOWMETER_TO_PUMP)
    flow_df = flow_df[flow_df["SitePumpID"].isin(ALLOWED_PUMPS)].copy()

    flow_summary = (
        flow_df
        .groupby(["SitePumpID", "ts_minute"])["FlowRate"]
        .mean()
        .reset_index()
    )

    # Merge FlowRate into pump_df
    pump_df = pump_df.merge(
        flow_summary,
        how="left",
        on=["SitePumpID", "ts_minute"],
    )

    # Fill gaps
    pump_df = pump_df.ffill().bfill()
    if "FlowRate" not in pump_df.columns:
        pump_df["FlowRate"] = 0.0
    pump_df["FlowRate"] = pump_df["FlowRate"].fillna(0.0)

    # Group per pump
    g = pump_df.groupby("SitePumpID", group_keys=False)

    # long-window baselines for deviations (≈2 hours)
    baseline_pressure = g["Pressure"].transform(
        lambda s: s.rolling(window=120, min_periods=30).mean()
    )
    baseline_current = g["OutputCurrent"].transform(
        lambda s: s.rolling(window=120, min_periods=30).mean()
    )

    pump_df["pressure_dev"] = pump_df["Pressure"] - baseline_pressure
    pump_df["current_dev"] = pump_df["OutputCurrent"] - baseline_current

    pump_df["pressure_dev_pct"] = pump_df["pressure_dev"] / baseline_pressure.replace(0, pd.NA)
    pump_df["current_dev_pct"] = pump_df["current_dev"] / baseline_current.replace(0, pd.NA)

    # short rolling stats (window=5)
    pump_df["Pressure_roll_mean_5"] = g["Pressure"].transform(
        lambda s: s.rolling(window=5, min_periods=1).mean()
    )
    pump_df["Pressure_roll_std_5"] = g["Pressure"].transform(
        lambda s: s.rolling(window=5, min_periods=1).std().fillna(0)
    )
    pump_df["OutputCurrent_roll_mean_5"] = g["OutputCurrent"].transform(
        lambda s: s.rolling(window=5, min_periods=1).mean()
    )
    pump_df["OutputCurrent_roll_std_5"] = g["OutputCurrent"].transform(
        lambda s: s.rolling(window=5, min_periods=1).std().fillna(0)
    )
    pump_df["FlowRate_roll_mean_5"] = g["FlowRate"].transform(
        lambda s: s.rolling(window=5, min_periods=1).mean()
    )
    pump_df["FlowRate_roll_std_5"] = g["FlowRate"].transform(
        lambda s: s.rolling(window=5, min_periods=1).std().fillna(0)
    )

    # ----- Sensor side -----
    sensor_df["SitePumpID"] = sensor_df["SensorID"].map(site_map1)
    sensor_df = sensor_df[sensor_df["SitePumpID"].isin(ALLOWED_PUMPS)].copy()
    sensor_df["LogDateTimeFixed"] = pd.to_datetime(sensor_df["LogDateTimeFixed"])
    sensor_df["ts_minute"] = sensor_df["LogDateTimeFixed"].dt.floor("T")

    sensor_pivot = (
        sensor_df
        .pivot_table(
            index=["SitePumpID", "ts_minute"],
            columns="SensorID",
            values="Value",
            aggfunc="mean",
        )
        .rename(columns=SENSOR_TO_FEATURE)
        .reset_index()
    )

    merged = pump_df.merge(
        sensor_pivot,
        how="left",
        on=["SitePumpID", "ts_minute"],
    )

    # make sure all training features exist
    for col in FEATURE_COLS:
        if col not in merged.columns:
            merged[col] = 0.0

    merged = merged.ffill().bfill().fillna(0)

    return merged

# -----------------------
# Main entry used by Flask
# -----------------------
def detect_anomalies(limit: int = 200_000):
    """
    Build 21-feature table, run per-pump models, and return a list of anomalies.
    """
    df = build_features_21(limit=limit)

    all_rows = []

    # run each pump through its own model
    for pump_id, group in df.groupby("SitePumpID"):
        model_pack = MODEL_BY_PUMP.get(int(pump_id))
        if model_pack is None:
            continue

        scaler = model_pack["scaler"]
        model = model_pack["model"]

        X = group[FEATURE_COLS].astype(float)
        X_scaled = scaler.transform(X)

        preds = model.predict(X_scaled)                  # 1 normal, -1 anomaly
        scores = model.decision_function(X_scaled)       # lower = more anomalous

        g2 = group.copy()
        g2["pred"] = preds
        g2["anom_score"] = scores
        all_rows.append(g2)

        if not all_rows:
            return []

        merged = pd.concat(all_rows, ignore_index=True)

        # keep anomalies only
        anomalies = merged[merged["pred"] == -1].copy()
        if anomalies.empty:
            return []

        # --- sort anomalies: newest first, then most anomalous (lowest score) ---
        anomalies = anomalies.sort_values(
            ["PumpLogDate", "anom_score"],
            ascending=[False, True],  # newer date first, lower score first
        )

        # severity based on anomaly scores (computed from anomalies only)
        q_low = anomalies["anom_score"].quantile(0.10)   # bottom 10% = HIGH
        q_med = anomalies["anom_score"].quantile(0.25)   # bottom 25% = MEDIUM

        def map_severity(s: float) -> str:
            if s <= q_low:
                return "HIGH"
            elif s <= q_med:
                return "MEDIUM"
            else:
                return "LOW"

        anomalies["severity"] = anomalies["anom_score"].apply(map_severity)


    # precompute a conductivity baseline (if present) using all data
    cond_baseline = None
    if "Conductivity_31489" in merged.columns:
        cond_baseline = merged["Conductivity_31489"].median()

    def build_reason(row):
        reasons = []

        # Pressure vs long-term baseline
        pdp = row.get("pressure_dev_pct", None)
        if pdp is not None and pdp == pdp:  # not NaN
            if pdp > 0.35:
                reasons.append("Pressure significantly higher than typical baseline.")
            elif pdp < -0.35:
                reasons.append("Pressure significantly lower than typical baseline.")

        # Current vs long-term baseline
        cdp = row.get("current_dev_pct", None)
        if cdp is not None and cdp == cdp:
            if cdp > 0.35:
                reasons.append("Current draw higher than expected for this pump.")
            elif cdp < -0.35:
                reasons.append("Current draw lower than expected for this pump.")

        # Flow rate vs short-term behavior
        fr = row.get("FlowRate", None)
        fr_mean5 = row.get("FlowRate_roll_mean_5", None)
        if fr is not None and fr_mean5 is not None and fr_mean5 not in (0, float("inf")):
            try:
                if fr < 0.7 * fr_mean5:
                    reasons.append("Flow rate has dropped compared to recent history.")
                elif fr > 1.3 * fr_mean5:
                    reasons.append("Flow rate is spiking compared to recent history.")
            except TypeError:
                pass

        # High conductivity compared to typical
        if cond_baseline is not None:
            cond = row.get("Conductivity_31489", None)
            if cond is not None and cond == cond and cond_baseline > 0:
                if cond > 1.3 * cond_baseline:
                    reasons.append("Conductivity higher than typical for this pump.")

        if not reasons:
            return "Model flagged this point as anomalous based on combined sensor patterns."
        return " ".join(reasons)

    # --- Build final payload ---
    results = []
    for _, row in anomalies.iterrows():
        results.append({
            "pumpId": int(row["SitePumpID"]),
            "pumpName": row.get("Name", "Unknown Pump"),
            "timestamp": row["PumpLogDate"].isoformat(),

            "frequency": float(row["Frequency"]),
            "voltage": float(row["OutputVoltage"]),
            "current": float(row["OutputCurrent"]),
            "pressure": float(row["Pressure"]),
            "conductivity": float(row.get("Conductivity_31489", 0.0)),

            "score": float(row["anom_score"]),
            "severity": row["severity"],
            "reason": build_reason(row),
        })

    return results
