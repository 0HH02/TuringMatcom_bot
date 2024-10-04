# config.py
import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCpQ7M42a7fsZtqCoeYrZCJDVOn-9GexP0")
TOKEN = os.getenv("TOKEN", "7872510777:AAHhL7S1vwznoop42anPipzKA2AMVy9NsWQ")

if not GOOGLE_API_KEY or not TOKEN:
    raise ValueError(
        "API keys no configuradas correctamente. Asegúrese de configurar GOOGLE_API_KEY y TOKEN como variables de entorno."
    )
