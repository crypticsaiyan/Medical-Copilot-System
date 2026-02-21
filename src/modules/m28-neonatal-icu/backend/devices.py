"""
backend/devices.py
──────────────────
Module 28 — Neonatal ICU Monitoring System

Read operations for Monitoring_Device entity.
Devices are typically managed by biomedical staff and rarely updated
through the NICU portal, so only read + status-update functions are exposed.
Returns (result, raw_query) tuples.
"""

from __future__ import annotations

from datetime import datetime, timezone

from database.connection import devices_col

UTC = timezone.utc


def get_all_devices() -> tuple[list[dict], dict]:
    """Return all monitoring devices."""
    raw_query = {
        "operation":  "find",
        "collection": "monitoring_devices",
        "filter":     {},
        "projection": {"_id": 0},
    }
    results = list(devices_col.find({}, {"_id": 0}))
    return results, raw_query


def get_device(device_id: str) -> tuple[dict | None, dict]:
    """Fetch a single monitoring device by ID."""
    query = {"device_id": device_id}
    raw_query = {
        "operation":  "find_one",
        "collection": "monitoring_devices",
        "filter":     query,
        "projection": {"_id": 0},
    }
    result = devices_col.find_one(query, {"_id": 0})
    return result, raw_query


def get_active_devices() -> tuple[list[dict], dict]:
    """Return only devices with status='Active'."""
    query = {"status": "Active"}
    raw_query = {
        "operation":  "find",
        "collection": "monitoring_devices",
        "filter":     query,
        "projection": {"_id": 0},
    }
    results = list(devices_col.find(query, {"_id": 0}))
    return results, raw_query


def update_device_status(device_id: str, status: str) -> tuple[dict, dict]:
    """Update a device's operational status."""
    query  = {"device_id": device_id}
    update = {"$set": {"status": status, "updated_at": datetime.now(UTC)}}
    raw_query = {
        "operation":  "update_one",
        "collection": "monitoring_devices",
        "filter":     query,
        "update":     {"$set": {"status": status}},
    }
    result = devices_col.update_one(query, update)
    return {"matched": result.matched_count, "modified": result.modified_count}, raw_query
