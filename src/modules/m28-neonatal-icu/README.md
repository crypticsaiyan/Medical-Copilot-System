# Module 28 — Neonatal ICU Monitoring System

> **DBMS Project** | Python · PyMongo · MongoDB Atlas · Streamlit

---

## Project Structure

```
src/modules/m28-neonatal-icu/
├── .env.example          ← Copy to .env and fill credentials
├── .gitignore
├── database/
│   ├── connection.py     ← Singleton MongoDB client (dotenv)
│   ├── schema.py         ← $jsonSchema validators for 5 collections
│   └── seed.py           ← Seed demo data
├── backend/
│   ├── admissions.py     ← CRUD — Neonate + NICU_ADMISSION
│   ├── observations.py   ← CRUD — Nurse_Observation
│   ├── vitals.py         ← CRUD — Vital_Signs_Record
│   ├── devices.py        ← Read — Monitoring_Device
│   ├── analytics.py      ← Aggregation Pipelines (simulated Views)
│   └── triggers.py       ← Threshold checks (simulated Triggers)
└── frontend/
    ├── app.py            ← Streamlit entrypoint
    └── components/
        ├── admission_form.py
        ├── patient_selector.py
        ├── vitals_chart.py
        ├── observations_panel.py
        ├── query_display.py
        └── trigger_alerts.py
```

## Setup

```bash
# 1. Create local env file
cp .env.example .env
# Edit .env and set your MONGO_URI and DB_NAME

# 2. Install dependencies (from project root venv)
pip install pymongo python-dotenv streamlit pandas

# 3. Seed the database (run from module root)
cd src/modules/m28-neonatal-icu
python -m database.seed

# 4. Run the Streamlit dashboard
streamlit run frontend/app.py
```

## Collections (ER Diagram → MongoDB)

| Entity | Collection | Key Fields |
|---|---|---|
| Neonate | `neonates` | neonate_id, name, dob, blood_group, gestational_age_weeks, gender, birth_weight_g |
| NICU_ADMISSION | `nicu_admissions` | admission_id, neonate_id (ref), admission_date, bed_no, diagnosis |
| Nurse_Observation | `nurse_observations` | observation_id, admission_id (ref), observation_time, feeding_status, crying_level, notes |
| Monitoring_Device | `monitoring_devices` | device_id, device_type, manufacturer, model_number, last_calibrated |
| Vital_Signs_Record | `vital_signs_records` | record_id, admission_id (ref), device_id (ref), record_time, heart_rate, spo2, respiratory_rate, temp, systolic_bp, diastolic_bp |

## DBMS Concepts Implemented

### Views → Aggregation Pipelines (`backend/analytics.py`)
| View | Pipeline |
|---|---|
| `vital_signs_summary_view` | `$group` avg/min/max per admission |
| `daily_admissions_view` | `$group` by date |
| `alert_vitals_view` | `$match` outside thresholds |
| `neonate_admission_join_view` | `$lookup` join on neonate_id |

### Triggers → Change Streams (`backend/triggers.py`)
- `check_vital_thresholds(doc)` — pure function mimicking trigger body
- `watch_vitals_stream()` — real `collection.watch()` Change Stream on Atlas
- SQL trigger equivalent shown in the dashboard UI for comparison

## Git Commit History

```
feat(m28): scaffold module dir, .gitignore, .env.example, db connection
feat(m28): add MongoDB collection schema validation for all 5 entities
feat(m28): add CRUD operations for neonate admission, observations, vital signs and monitoring devices
feat(m28): implement aggregation pipelines as simulated MongoDB Views and Change Stream trigger simulation for vital alerts
feat(m28): add Streamlit dashboard — admission form, patient selector, vitals chart, observations panel, trigger alerts
feat(m28): add README and finalise module integration
```

---

 
