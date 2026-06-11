import os
from dotenv import load_dotenv

# Resolve absolute path to backend/.env file location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings:
    PROJECT_NAME: str = "FinSight"
    
    # Read variables from environment, using safe dummy strings if the .env is missing
    DB_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/finops_intelligence"
    )
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET", 
        "fallback_secret_for_local_dev_only_never_use_in_production"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    ROOT_DIR: str = os.path.dirname(BASE_DIR)
    DATA_DIR: str = os.path.join(ROOT_DIR, "data")

# Instantiate settings so it can be imported cleanly across the app
settings = Settings()