from mongo_connection import (
    neonates_collection,
    nicu_admissions_collection,
    growth_parameters_collection,
    feeding_logs_collection,
    gestational_age_ref_collection,
    vital_signs_collection,
    monitoring_device_collection
)

# -------------------------------
# 1. NICU ADMISSION QUERIES
# -------------------------------

def get_active_admissions():
    # Handle common case variations of admission status.
    return list(
        nicu_admissions_collection.find(
            {"status": {"$regex": "^admitted$", "$options": "i"}}
        )
    )


def get_neonate_details(neonate_id):
    return neonates_collection.find_one({"neonate_id": neonate_id})


# -------------------------------
# 2. GROWTH TRACKING
# -------------------------------

def get_growth_history(neonate_id):
    return list(
        growth_parameters_collection.find({"neonate_id": neonate_id}).sort("date", 1)
    )


def calculate_growth_velocity(neonate_id):
    records = list(
        growth_parameters_collection.find({"neonate_id": neonate_id}).sort("date", 1)
    )

    if len(records) < 2:
        return "Not enough data"

    # Use earliest and latest records with valid weight values.
    valid = [r for r in records if r.get("weight") is not None]
    if len(valid) < 2:
        return "Not enough valid weight data"

    first = valid[0]
    last = valid[-1]

    weight_diff = last["weight"] - first["weight"]

    first_date = first.get("date")
    last_date = last.get("date")
    if first_date is not None and last_date is not None:
        delta = last_date - first_date
        days = delta.days if hasattr(delta, "days") else None
    else:
        days = None

    return {
        "weight_gain": weight_diff,
        "days_between": days,
        "weight_gain_per_day": (weight_diff / days) if days and days > 0 else None
    }


# -------------------------------
# 3. FEEDING ANALYSIS
# -------------------------------

def get_daily_feeding(neonate_id):
    pipeline = [
        {"$match": {"neonate_id": neonate_id}},
        {"$addFields": {"feeding_source": {"$ifNull": ["$feeding_date", "$feeding_time"]}}},
        {
            "$addFields": {
                "feeding_day": {
                    "$cond": [
                        {"$eq": [{"$type": "$feeding_source"}, "date"]},
                        {"$dateToString": {"format": "%Y-%m-%d", "date": "$feeding_source"}},
                        {"$substrBytes": ["$feeding_source", 0, 10]}
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$feeding_day",
                "total_feed": {"$sum": "$quantity_ml"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    return list(feeding_logs_collection.aggregate(pipeline))


# -------------------------------
# 4. GESTATIONAL AGE COMPARISON
# -------------------------------

def check_growth_against_reference(neonate_id):
    neonate = neonates_collection.find_one({"neonate_id": neonate_id})

    if not neonate:
        return "Neonate not found"

    ga = neonate.get("gestational_age_weeks")
    if ga is None:
        return "Gestational age missing"

    ref = gestational_age_ref_collection.find_one({"gestational_week": ga})

    latest_growth = growth_parameters_collection.find_one(
        {"neonate_id": neonate_id},
        sort=[("date", -1)]
    )

    if not ref or not latest_growth:
        return "Insufficient data"

    weight = latest_growth.get("weight")
    normal_range = ref.get("normal_weight_range")
    if weight is None or not normal_range or len(normal_range) != 2:
        return "Insufficient data"

    if weight < normal_range[0]:
        status = "Underweight"
    elif weight > normal_range[1]:
        status = "Overweight"
    else:
        status = "Normal"

    return {
        "weight": weight,
        "expected_range": normal_range,
        "status": status
    }


# -------------------------------
# 5. VITAL SIGNS ALERT
# -------------------------------

def check_abnormal_vitals(neonate_id):
    vitals = list(vital_signs_collection.find({"neonate_id": neonate_id}))

    alerts = []

    for v in vitals:
        heart_rate = v.get("heart_rate")
        oxygen_saturation = v.get("oxygen_saturation")
        reading_time = v.get("timestamp") or v.get("recorded_time") or v.get("date")

        if heart_rate is not None and heart_rate > 160:
            alerts.append({
                "type": "High Heart Rate",
                "value": heart_rate,
                "timestamp": reading_time
            })

        if oxygen_saturation is not None and oxygen_saturation < 90:
            alerts.append({
                "type": "Low Oxygen Level",
                "value": oxygen_saturation,
                "timestamp": reading_time
            })

    return alerts


# -------------------------------
# 6. DEVICE USAGE
# -------------------------------

def get_device_status():
    return list(monitoring_device_collection.find())


# -------------------------------
# 7. CORRECTED AGE (IMPORTANT)
# -------------------------------

def calculate_corrected_age(neonate_id, current_age_weeks):
    neonate = neonates_collection.find_one({"neonate_id": neonate_id})

    if not neonate:
        return "Neonate not found"

    gestational_age = neonate.get("gestational_age_weeks")
    if gestational_age is None:
        return "Gestational age missing"

    correction = 40 - gestational_age
    corrected_age = current_age_weeks - correction

    return {
        "chronological_age": current_age_weeks,
        "corrected_age": corrected_age
    }