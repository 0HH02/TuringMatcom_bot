# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# import streamlit as st

# GOOGLE_API_KEY = st.secrets["general"]["GOOGLE_API_KEY"]
# TOKEN = st.secrets["general"]["TOKEN"]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOKEN = os.getenv("TOKEN")

if not GOOGLE_API_KEY or not TOKEN:
    raise ValueError(
        "API keys no configuradas correctamente. Asegúrese de configurar GOOGLE_API_KEY y TOKEN como variables de entorno."
    )
