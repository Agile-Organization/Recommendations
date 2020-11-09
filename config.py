import os
import json

import logging

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgres://postgres:postgres@localhost:5432/postgres"
)

# Override if we are running in Cloud Foundry
if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.environ['VCAP_SERVICES'])
    user_provided_services = vcap['user-provided']
    for service in user_provided_services:
        if service['name'] == "ElephantSQL":
            DATABASE_URI = service['credentials']['url']
            break


# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
