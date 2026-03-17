import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def load_env() -> None:
    """Load .env from project root first, then local folder as fallback."""
    root_env = Path(__file__).resolve().parents[1] / ".env"
    local_env = Path(__file__).resolve().parent / ".env"
    load_dotenv(root_env)
    load_dotenv(local_env, override=False)


def main() -> None:
    load_env()

    uri = os.getenv("MONGO_URI")
    if not uri:
        print("FAILED: MONGO_URI is missing. Add it to .env")
        raise SystemExit(1)

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=8000)
        client.admin.command("ping")
        print("SUCCESS: MongoDB connection is working.")
    except PyMongoError as exc:
        print(f"FAILED: MongoDB connection error: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
