import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import environment variables module (which auto-loads .env)
from utils.env_loader import get_env_var
from constants.config import APP_TITLE, APP_DESCRIPTION

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=":world_map:️",
    layout="centered",
)

"""
# Welcome to Xenty!
"""

APP_DESCRIPTION

"""
If you have any questions, checkout our [Github](https://github.com/cedric-alyra/xenty).

"""

st.write("")

st.header("Engagement Analysis - Machine Learning")
st.write("Analyzing tweets interactions on Twitter using Machine Learning.")
st.image("./viz/ML.png", width=800)

st.write("")

st.header("Sentiment Analysis - Deep Learning")
st.write("Analyzing comments sentiment on Twitter using Deep Learning.")
st.image("./viz/DL.png", width=800)