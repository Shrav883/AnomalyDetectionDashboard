Anomaly Detection Dashboard

Full-Stack Monitoring System (Flask + React + SQL Server)

A complete anomaly detection dashboard built for pump monitoring using:

React + Vite + TailwindCSS (Frontend)

Flask + SQLAlchemy (Backend API)

Microsoft SQL Server (Data source)

SQL-based anomaly and status calculations

Protected login system (dummy auth for class demo)

This project was developed for academic demonstration and integrates real SQL Server datasets from industrial pump logs from SitePro Inc. 

Project Structure

Anomaly_Detection_Dashboard/
│
├── anomaly_backend/          # Flask backend API
│   ├── app.py                # API routes
│   ├── db.py                 # Database engine + ODBC connection
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Local DB credentials (NOT pushed to GitHub)
│
├── anomaly-frontend/         # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── pages/            # Dashboard, Alerts, Failures, Login, PumpDetails
│   │   ├── components/       # Layout, ProtectedRoute, etc.
│   │   └── index.css         # Tailwind import
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
│
└── README.md                 # Documentation (this file)


Backend Setup (Flask)

1️. Create virtual environment (first time only)
cd anomaly_backend
python -m venv venv

2️. Activate the environment

PowerShell

    .\venv\Scripts\activate

CMD

    venv\Scripts\activate.bat

3️. Install dependencies

    pip install -r requirements.txt

4️. Configure environment variables

    Create anomaly_backend/.env:

    DB_SERVER=<SERVER_IP>
    DB_NAME=<DB.NAME>
    DB_USER=YOUR_USER_NAME
    DB_PASSWORD=YOUR_PASSWORD