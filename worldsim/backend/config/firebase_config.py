"""
firebase_config.py - Firebase Admin SDK Initialization for WorldSim

Initializes the Firebase Admin SDK with service account credentials
and exposes a module-level Firestore client (`db`) for use across
the backend. Any module can import the client directly:

    from config.firebase_config import db

The initialization is idempotent - calling initialize_firebase()
multiple times will not create duplicate Firebase app instances.
"""

import os
import logging

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from .env file
# ---------------------------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------

SERVICE_ACCOUNT_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "backend/config/serviceAccountKey.json"
)

PROJECT_ID = os.getenv(
    "FIREBASE_PROJECT_ID",
    "worldsim-hackathon"
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("firebase_config")


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def initialize_firebase() -> firestore.Client:
    """
    Initialize the Firebase Admin SDK and return a Firestore client.

    Uses service account credentials from the path specified by the
    GOOGLE_APPLICATION_CREDENTIALS environment variable (or the
    default fallback path). Safe to call multiple times - subsequent
    calls return the existing Firestore client without re-initializing.

    Returns:
        firestore.Client: Authenticated Firestore database client.

    Raises:
        SystemExit: If initialization fails due to missing or invalid
                    credentials. The error is logged before exit.
    """
    try:
        # Check if a Firebase app is already initialized
        firebase_admin.get_app()
        logger.info("Firebase app already initialized, reusing existing instance.")

    except ValueError:
        # No app exists yet - initialize a new one
        try:
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            # Use the project ID from credentials if the environment variable
            # doesn't match. This prevents 403 errors when the service account
            # belongs to a different Firebase project than the default.
            actual_project = getattr(cred, 'project_id', None) or PROJECT_ID
            firebase_admin.initialize_app(cred, {
                "projectId": actual_project,
            })
            logger.info(
                "Firebase Admin SDK initialized successfully "
                "(project: %s).", actual_project
            )

        except FileNotFoundError:
            logger.warning(
                "Service account file not found at '%s'. "
                "Running WITHOUT Firestore — writes will be skipped. "
                "Set GOOGLE_APPLICATION_CREDENTIALS in your .env file "
                "or place serviceAccountKey.json in backend/config/.",
                SERVICE_ACCOUNT_PATH,
            )
            return None

        except ValueError as exc:
            logger.warning(
                "Invalid service account credentials file: %s. "
                "Running WITHOUT Firestore.", exc
            )
            return None

        except Exception as exc:
            logger.warning(
                "Firebase initialization failed: %s. "
                "Running WITHOUT Firestore.", exc
            )
            return None

    # Return a Firestore client bound to the initialized app
    return firestore.client()


# ---------------------------------------------------------------------------
# Module-level Firestore client
# ---------------------------------------------------------------------------
# Any module can import `db` directly:
#   from config.firebase_config import db
# db will be None if credentials are missing — all writes become no-ops.
# ---------------------------------------------------------------------------

db = initialize_firebase()


# ---------------------------------------------------------------------------
# Connection Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Firebase connection...")
    test_db = initialize_firebase()

    # Write a test document to verify connectivity
    test_db.collection("test").document("connection").set({
        "status": "connected",
        "timestamp": firestore.SERVER_TIMESTAMP,
    })
    print("Firebase connection successful")
    print(f"Project: {PROJECT_ID}")
    print("Check Firestore console -> 'test' collection -> 'connection' document")
