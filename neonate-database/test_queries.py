from queries import (
    get_active_admissions,
    get_neonate_details,
    get_growth_history,
    calculate_growth_velocity,
    get_daily_feeding,
    check_growth_against_reference,
    check_abnormal_vitals,
    get_device_status,
    calculate_corrected_age,
)


def safe_run(label, fn):
    try:
        result = fn()
        print(f"{label}: {result}")
    except Exception as exc:
        print(f"{label} FAILED: {exc}")


if __name__ == "__main__":
    # Replace with an actual neonate_id from your MongoDB data.
    test_id = "N001"

    safe_run("1) Active admissions count", lambda: len(get_active_admissions()))
    safe_run("2) Neonate details", lambda: get_neonate_details(test_id))
    safe_run("3) Growth history count", lambda: len(get_growth_history(test_id)))
    safe_run("4) Growth velocity", lambda: calculate_growth_velocity(test_id))
    safe_run("5) Daily feeding", lambda: get_daily_feeding(test_id))
    safe_run("6) Growth vs reference", lambda: check_growth_against_reference(test_id))
    safe_run("7) Abnormal vitals", lambda: check_abnormal_vitals(test_id))
    safe_run("8) Device status count", lambda: len(get_device_status()))
    safe_run("9) Corrected age", lambda: calculate_corrected_age(test_id, 10))
