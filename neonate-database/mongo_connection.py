from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

# Create / access database
db = client["nicu_monitoring_system"]

# Collections
neonates_collection = db["neonates"]
nicu_admissions_collection = db["nicu_admissions"]
growth_parameters_collection = db["growth_parameters"]
feeding_logs_collection = db["feeding_logs"]
gestational_age_ref_collection = db["gestational_age_reference"]
vital_signs_collection = db["vital_signs"]
monitoring_device_collection = db["monitoring_device"]

print("MongoDB Connected Successfully")