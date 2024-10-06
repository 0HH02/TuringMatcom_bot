# config.py
import os
import streamlit as st

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCpQ7M42a7fsZtqCoeYrZCJDVOn-9GexP0")
TOKEN = os.getenv("token_prueba", "7563404155:AAHNN39uBNjWIl8rEOGzWj4mFhz7HSnPnrI")

if not GOOGLE_API_KEY or not TOKEN:
    raise ValueError(
        "API keys no configuradas correctamente. Asegúrese de configurar GOOGLE_API_KEY y TOKEN como variables de entorno."
    )
