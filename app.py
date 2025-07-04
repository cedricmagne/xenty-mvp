import streamlit as st
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import environment variables module (which auto-loads .env)
from utils.env_loader import get_env_var
from constants.config import APP_TITLE, APP_DESCRIPTION

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=":world_map:️",
    layout="wide",
)

"""
# Welcome to Xenty!
"""

APP_DESCRIPTION

"""
If you have any questions, checkout our [Github](https://github.com/cedric-alyra/xenty) and [Kaggle
project](https://www.kaggle.com/competitions/xenty).

"""

left, right = st.columns(2)