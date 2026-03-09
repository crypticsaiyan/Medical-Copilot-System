"""
database/seed.py — Module 28 NICU
Run: python -m database.seed  (from m28-neonatal-icu/)
Seeds all 5 collections with realistic, dense demo data.
"""
from __future__ import annotations
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.connection import db, neonates_col, admissions_col, observations_col, devices_col, vital_signs_col
from database.schema import apply_schemas

UTC = timezone.utc

def _dt(days_ago=0, hours_ago=0, minutes_ago=0):
    return datetime.now(UTC) - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

NEONATES = [
    {"neonate_id":"N001","name":"Arjun Mehta","dob":_dt(10),"blood_group":"B+","gestational_age_weeks":30,"gender":"Male","birth_weight_g":1450},
    {"neonate_id":"N002","name":"Priya Sharma","dob":_dt(5),"blood_group":"A+","gestational_age_weeks":28,"gender":"Female","birth_weight_g":980},
    {"neonate_id":"N003","name":"Rohan Das","dob":_dt(2),"blood_group":"O+","gestational_age_weeks":34,"gender":"Male","birth_weight_g":2100},
    {"neonate_id":"N004","name":"Ananya Iyer","dob":_dt(7),"blood_group":"AB+","gestational_age_weeks":32,"gender":"Female","birth_weight_g":1750},
    {"neonate_id":"N005","name":"Vikram Nair","dob":_dt(1),"blood_group":"O-","gestational_age_weeks":36,"gender":"Male","birth_weight_g":2400},
]

ADMISSIONS = [
    {"admission_id":"ADM001","neonate_id":"N001","admission_date":_dt(10),"bed_no":"B-01","diagnosis":"Respiratory Distress Syndrome","status":"Admitted"},
    {"admission_id":"ADM002","neonate_id":"N002","admission_date":_dt(5), "bed_no":"B-02","diagnosis":"Extreme Prematurity","status":"Admitted"},
    {"admission_id":"ADM003","neonate_id":"N003","admission_date":_dt(2), "bed_no":"B-03","diagnosis":"Neonatal Jaundice","status":"Admitted"},
    {"admission_id":"ADM004","neonate_id":"N004","admission_date":_dt(7), "bed_no":"B-04","diagnosis":"Neonatal Sepsis","status":"Admitted"},
    {"admission_id":"ADM005","neonate_id":"N005","admission_date":_dt(1), "bed_no":"B-05","diagnosis":"Hypoglycaemia","status":"Admitted"},
]

DEVICES = [
    {"device_id":"DEV001","device_type":"Pulse Oximeter","manufacturer":"Nellcor","model_number":"PM10N","last_calibrated":_dt(30),"status":"Active"},
    {"device_id":"DEV002","device_type":"Cardiorespiratory Monitor","manufacturer":"Philips","model_number":"MX40","last_calibrated":_dt(15),"status":"Active"},
    {"device_id":"DEV003","device_type":"Incubator Monitor","manufacturer":"Dräger","model_number":"Caleo","last_calibrated":_dt(7),"status":"Active"},
    {"device_id":"DEV004","device_type":"Ventilator","manufacturer":"Medtronic","model_number":"PB980","last_calibrated":_dt(20),"status":"Active"},
]

# Dense vitals: 12 readings per admission spread over 12 hours
def _vitals(adm_id, dev_id, base_hr, base_spo2, base_rr, base_temp, base_sbp, base_dbp):
    records = []
    for i in range(12):
        import random; random.seed(adm_id + str(i))
        offset_hr  = random.uniform(-15, 20)
        offset_sp  = random.uniform(-5,  3)
        offset_rr  = random.uniform(-8,  10)
        offset_tmp = random.uniform(-0.4, 0.5)
        records.append({
            "record_id":        f"VS_{adm_id}_{i:02d}",
            "admission_id":     adm_id,
            "device_id":        dev_id,
            "record_time":      _dt(hours_ago=12-i),
            "heart_rate":       round(base_hr  + offset_hr,  1),
            "spo2":             round(min(100, base_spo2 + offset_sp), 1),
            "respiratory_rate": round(base_rr  + offset_rr,  1),
            "temp":             round(base_temp + offset_tmp, 2),
            "systolic_bp":      round(base_sbp + random.uniform(-4, 5), 1),
            "diastolic_bp":     round(base_dbp + random.uniform(-3, 4), 1),
        })
    return records

VITALS = (
    _vitals("ADM001","DEV001", 155, 93, 56, 37.0, 48, 30) +
    _vitals("ADM002","DEV002", 110, 90, 48, 36.6, 44, 27) +
    _vitals("ADM003","DEV001", 152, 97, 44, 37.2, 54, 34) +
    _vitals("ADM004","DEV003", 170, 88, 65, 38.2, 50, 32) +  # ← several alerts
    _vitals("ADM005","DEV004", 145, 95, 50, 36.9, 52, 33)
)

OBSERVATIONS = [
    {"observation_id":"OBS001","admission_id":"ADM001","observation_time":_dt(hours_ago=11),"feeding_status":"IV Nutrition","crying_level":"Mild","notes":"Mild subcostal recession; CPAP ongoing."},
    {"observation_id":"OBS002","admission_id":"ADM001","observation_time":_dt(hours_ago=6), "feeding_status":"IV Nutrition","crying_level":"Moderate","notes":"SpO2 improved after CPAP pressure adjustment."},
    {"observation_id":"OBS003","admission_id":"ADM001","observation_time":_dt(hours_ago=2), "feeding_status":"IV Nutrition","crying_level":"Mild","notes":"Condition stabilising. Weight up +8g today."},
    {"observation_id":"OBS004","admission_id":"ADM002","observation_time":_dt(hours_ago=4), "feeding_status":"Formula","crying_level":"High","notes":"Poor sucking reflex. Weight gain: +12g."},
    {"observation_id":"OBS005","admission_id":"ADM002","observation_time":_dt(hours_ago=1), "feeding_status":"Formula","crying_level":"Moderate","notes":"Tolerating feeds better."},
    {"observation_id":"OBS006","admission_id":"ADM003","observation_time":_dt(hours_ago=3), "feeding_status":"Breastfed","crying_level":"None","notes":"Jaundice improving. Bilirubin trending down."},
    {"observation_id":"OBS007","admission_id":"ADM004","observation_time":_dt(hours_ago=5), "feeding_status":"IV Nutrition","crying_level":"High","notes":"Sepsis markers elevated. Antibiotics started."},
    {"observation_id":"OBS008","admission_id":"ADM004","observation_time":_dt(hours_ago=1), "feeding_status":"IV Nutrition","crying_level":"Moderate","notes":"Temp slightly reduced after antipyretics."},
    {"observation_id":"OBS009","admission_id":"ADM005","observation_time":_dt(hours_ago=4), "feeding_status":"Breastfed","crying_level":"None","notes":"Blood glucose stable after dextrose supplement."},
]


def seed(*, drop_existing=True):
    print("\n[seed] ── Applying JSON Schema validators ──")
    apply_schemas(db, verbose=True)
    collections_data = [
        (neonates_col,    NEONATES,    "neonates"),
        (admissions_col,  ADMISSIONS,  "nicu_admissions"),
        (devices_col,     DEVICES,     "monitoring_devices"),
        (vital_signs_col, VITALS,      "vital_signs_records"),
        (observations_col,OBSERVATIONS,"nurse_observations"),
    ]
    print("\n[seed] ── Seeding collections ──")
    for col, docs, name in collections_data:
        if drop_existing:
            col.delete_many({})
        result = col.insert_many(docs)
        print(f"  ✅  Inserted {len(result.inserted_ids)} docs → '{name}'")
    print(f"\n[seed] 🎉 Done. Database: {db.name}")


if __name__ == "__main__":
    seed()
