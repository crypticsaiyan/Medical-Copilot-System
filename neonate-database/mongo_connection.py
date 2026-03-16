from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

# Create / access database
db = client["nicu_monitoring_system"]

# Collections
growth_parameters_collection = db["growth_parameters"]
monitoring_device_collection = db["monitoring_device"]
neonates_collection = db["neonates"]
nicu_admissions_collection = db["nicu_admissions"]
nurse_observation_collection = db["nurse_observation"]
vital_signs_collection = db["vital_signs"]

print("MongoDB Connected Successfully")