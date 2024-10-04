# config.py
import os
import streamlit as st

GOOGLE_API_KEY = "7872510777:AAHhL7S1vwznoop42anPipzKA2AMVy9NsWQ"
# os.getenv("GOOGLE_API_KEY")
TOKEN = "AIzaSyCpQ7M42a7fsZtqCoeYrZCJDVOn-9GexP0"
# os.getenv("TOKEN")

if not GOOGLE_API_KEY or not TOKEN:
    raise ValueError(
        "API keys no configuradas correctamente. Asegúrese de configurar GOOGLE_API_KEY y TOKEN como variables de entorno."
    )
