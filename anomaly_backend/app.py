from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text

from db import engine, test_connection
from ml_model import detect_anomalies

app = Flask(__name__)
CORS(app)  # allow React frontend to call this API

# Dummy dashboard credentials (for login page)
APP_USERNAME = "student"   # change if you want
APP_PASSWORD = "demo123"   # change if you want
DUMMY_TOKEN = "demo-token-123"


# -----------------------
# Health / sanity endpoints
# -----------------------
@app.route("/api/health", methods=["GET"])
def health():
    """
    Check that Flask is running and DB connection works.
    """
    try:
        db_status = test_connection()
        return jsonify({"status": "ok", "db": db_status}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/sample", methods=["GET"])
def sample():
    """
    Simple test endpoint to show how to run a SQL query.
    Right now it just runs: SELECT 1 AS test_value
    """
    sql = text("SELECT 1 AS test_value")
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()

    data = [dict(r) for r in rows]
    return jsonify(data), 200


# -----------------------
# Dummy login (for dashboard)
# -----------------------
@app.route("/api/login", methods=["GET", "POST", "OPTIONS"])
def login():
    """
    Dummy login for the dashboard.

    - GET: sanity check (so you don't get 405 in browser)
    - POST: real login
    - OPTIONS: CORS preflight
    """

    # CORS preflight
    if request.method == "OPTIONS":
        return "", 204

    # Simple GET sanity check
    if request.method == "GET":
        return jsonify({
            "message": "Login endpoint is alive. Use POST with JSON { username, password }."
        }), 200

    # POST: check credentials
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    if username == APP_USERNAME and password == APP_PASSWORD:
        return jsonify({
            "token": DUMMY_TOKEN,
            "user": {"username": username}
        }), 200

    return jsonify({"message": "Invalid username or password"}), 401


# -----------------------
# Flow meter logs
# -----------------------
@app.route("/api/flowmeter", methods=["GET"])
def get_flowmeter_logs():
    """
    Returns flow meter logs for FlowMeterIDs 5950, 5077, 4685, 5081
    between January 1, 2025 and January 1, 2026.
    """
    sql = text("""
        SELECT FlowMeterID, SitePipelineID, TotalVolume, DayVolume,
               FlowRate, LogStartTime, LogEndTime
        FROM FlowMeterLogs
        WHERE LogStartTime >= :start_2025
          AND LogStartTime <  :end_2026
          AND FlowMeterID IN (5950, 5077, 4685, 5081)
        ORDER BY LogStartTime DESC
    """)

    params = {
        "start_2025": "2025-01-01",
        "end_2026": "2026-01-01",
    }

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    data = [dict(r) for r in rows]
    return jsonify(data), 200


# -----------------------
# Pump cards (overview)
# -----------------------
@app.route("/api/pumps", methods=["GET"])
def get_pumps():
    """
    Returns one latest log row per pump (SitePumpID) to power the pump cards.
    Supports searching by pump name or SitePumpID using ?q=
    """

    search = request.args.get("q", "").strip()

    # base SQL: latest row per pump using ROW_NUMBER()
    base_sql = """
        WITH LatestPumpLog AS (
            SELECT
                SitePumpID,
                [Name],
                [Status],
                StatusID,
                Fault,
                UnderAlarm,
                Running,
                PumpLogDate,
                ROW_NUMBER() OVER (
                    PARTITION BY SitePumpID
                    ORDER BY PumpLogDate DESC
                ) AS rn
            FROM pumplogs
            WHERE PumpLogDate >= :start_date
              AND SitePumpID IN (47366, 48142, 46962, 47367)
        )
        SELECT
            SitePumpID,
            [Name],
            [Status],
            StatusID,
            Fault,
            UnderAlarm,
            Running,
            PumpLogDate
        FROM LatestPumpLog
        WHERE rn = 1
    """

    params = {"start_date": "2025-01-01"}

    # add optional search filter (by name or pump ID)
    if search:
        base_sql += """
          AND (
              [Name] LIKE :search
              OR CAST(SitePumpID AS VARCHAR(20)) LIKE :search
          )
        """
        params["search"] = f"%{search}%"

    sql = text(base_sql)

    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    pumps = []
    for r in rows:
        fault = int(r["Fault"])
        under_alarm = int(r["UnderAlarm"])
        running = int(r["Running"])

        alert_status = "ALERT" if (fault == 1 or under_alarm == 1) else "NORMAL"

        pumps.append({
            "sitePumpId": r["SitePumpID"],
            "name": r["Name"],
            "statusText": r["Status"],
            "statusId": r["StatusID"],
            "alertStatus": alert_status,
            "running": bool(running),
            "lastLogTime": r["PumpLogDate"].isoformat(),
        })

    return jsonify(pumps), 200


# -----------------------
# Single pump details
# -----------------------
@app.route("/api/pumps/<int:site_pump_id>", methods=["GET"])
def get_pump_details(site_pump_id):
    """
    Returns detailed info for a single pump (SitePumpID):
      - latest log row (summary card)
      - recent history (for trends/charts)
    """

    limit = int(request.args.get("limit", 200))

    # 1) Latest log row for this pump
    latest_sql = text("""
        SELECT TOP 1
            SitePumpID,
            [Name],
            [Status],
            StatusID,
            Frequency,
            TargetFrequency,
            OutputCurrent,
            OutputVoltage,
            Pressure,
            Fault,
            UnderAlarm,
            Running,
            Active,
            StartDate,
            PumpLogDate
        FROM pumplogs
        WHERE SitePumpID = :pump_id
        ORDER BY PumpLogDate DESC
    """)

    # 2) Recent history (just core numeric + timestamp fields)
    history_sql = text(f"""
        SELECT TOP {limit}
            PumpLogDate,
            Frequency,
            OutputCurrent,
            OutputVoltage,
            Pressure,
            Fault,
            UnderAlarm,
            Running
        FROM pumplogs
        WHERE SitePumpID = :pump_id
        ORDER BY PumpLogDate DESC
    """)

    params = {"pump_id": site_pump_id}

    with engine.connect() as conn:
        latest_row = conn.execute(latest_sql, params).mappings().first()

        if not latest_row:
            return jsonify({"status": "error", "message": "Pump not found"}), 404

        history_rows = conn.execute(history_sql, params).mappings().all()

    # Derive alert status from latest row
    fault = int(latest_row["Fault"])
    under_alarm = int(latest_row["UnderAlarm"])
    running = int(latest_row["Running"])

    alert_status = "ALERT" if (fault == 1 or under_alarm == 1) else "NORMAL"

    pump = {
        "sitePumpId": latest_row["SitePumpID"],
        "name": latest_row["Name"],
        "statusText": latest_row["Status"],
        "statusId": latest_row["StatusID"],
        "alertStatus": alert_status,
        "running": bool(running),
        "active": bool(latest_row["Active"]),
        "frequency": float(latest_row["Frequency"]) if latest_row["Frequency"] is not None else None,
        "targetFrequency": float(latest_row["TargetFrequency"]) if latest_row["TargetFrequency"] is not None else None,
        "outputCurrent": float(latest_row["OutputCurrent"]) if latest_row["OutputCurrent"] is not None else None,
        "outputVoltage": float(latest_row["OutputVoltage"]) if latest_row["OutputVoltage"] is not None else None,
        "pressure": float(latest_row["Pressure"]) if latest_row["Pressure"] is not None else None,
        "startDate": latest_row["StartDate"].isoformat() if latest_row["StartDate"] else None,
        "lastLogTime": latest_row["PumpLogDate"].isoformat() if latest_row["PumpLogDate"] else None,
    }

    history = [
        {
            "pumpLogDate": r["PumpLogDate"].isoformat(),
            "frequency": float(r["Frequency"]) if r["Frequency"] is not None else None,
            "outputCurrent": float(r["OutputCurrent"]) if r["OutputCurrent"] is not None else None,
            "outputVoltage": float(r["OutputVoltage"]) if r["OutputVoltage"] is not None else None,
            "pressure": float(r["Pressure"]) if r["Pressure"] is not None else None,
            "fault": int(r["Fault"]),
            "underAlarm": int(r["UnderAlarm"]),
            "running": bool(r["Running"]),
        }
        for r in history_rows
    ]

    return jsonify({
        "pump": pump,
        "history": history,
    }), 200


# -----------------------
# Failure logs list
# -----------------------
@app.route("/api/failures", methods=["GET"])
def get_failure_logs():
    """
    Returns failure logs from FailureLogs.

    Supports:
      - ?limit=100              → limit number of rows (default 200)
      - ?pumpId=47367           → filter by SitePumpID
      - ?siteId=37390           → filter by SiteID
      - ?q=motor                → search in FailureDetails or Notes
      - ?isPumpFailure=1 or 0   → filter by IsPumpFailure
    """

    limit = int(request.args.get("limit", 200))
    pump_id = request.args.get("pumpId")
    site_id = request.args.get("siteId")
    search = request.args.get("q", "").strip()
    is_pump_failure = request.args.get("isPumpFailure")  # "1" or "0"

    base_sql = f"""
        SELECT TOP {limit}
            FailureLogID,
            SitePumpID,
            SiteID,
            StartDate,
            EndDate,
            IsPumpFailure,
            FailureDetails,
            Notes,
            CreatedAt,
            UpdatedAt
        FROM FailureLogs
    """

    conditions = []
    params = {}

    if pump_id:
        conditions.append("SitePumpID = :pump_id")
        params["pump_id"] = pump_id

    if site_id:
        conditions.append("SiteID = :site_id")
        params["site_id"] = site_id

    if is_pump_failure in ("0", "1"):
        conditions.append("IsPumpFailure = :is_pump_failure")
        params["is_pump_failure"] = is_pump_failure

    if search:
        conditions.append("""
            (
                FailureDetails LIKE :search
                OR Notes LIKE :search
                OR CAST(SitePumpID AS VARCHAR(20)) LIKE :search
                OR CAST(SiteID AS VARCHAR(20)) LIKE :search
            )
        """)
        params["search"] = f"%{search}%"

    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    # newest failures first
    base_sql += " ORDER BY CreatedAt DESC"

    sql = text(base_sql)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()

    data = [dict(r) for r in rows]
    return jsonify(data), 200


# -----------------------
# ML alerts (21-feature model)
# -----------------------
@app.route("/api/ml-alerts", methods=["GET"])
def ml_alerts():
    """
    Returns ML-based anomaly alerts from the 21-feature Isolation Forest model.
    Optional: ?limit=50000
    """
    limit = request.args.get("limit", default=50000, type=int)
    try:
        alerts = detect_anomalies(limit=limit)
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
