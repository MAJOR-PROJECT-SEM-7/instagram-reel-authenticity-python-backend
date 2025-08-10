from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

settings = Settings()
