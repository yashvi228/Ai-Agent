import os
from dotenv import load_dotenv


load_dotenv()


class AppConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_REAL_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))
    REQUEST_TIMEOUT_SEC = float(os.getenv("REQUEST_TIMEOUT_SEC", "60"))

