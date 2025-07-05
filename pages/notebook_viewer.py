import streamlit as st
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import environment variables module (which auto-loads .env)
from utils.env_loader import get_env_var
from utils.notebook_display import display_notebook

# Set page title
st.set_page_config(page_title="Notebook Viewer", layout="wide")

# Page header
st.title("Jupyter Notebook Viewer")
st.write("This page allows you to view Jupyter notebooks within the Streamlit app.")

# Create a notebooks directory if it doesn't exist
notebooks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "notebooks")
os.makedirs(notebooks_dir, exist_ok=True)

# Check if there are any notebooks in the directory
notebook_files = [f for f in os.listdir(notebooks_dir) if f.endswith('.ipynb')] if os.path.exists(notebooks_dir) else []

if notebook_files:
    # Let user select a notebook to display
    selected_notebook = st.selectbox("Select a notebook to view", notebook_files)
    notebook_path = os.path.join(notebooks_dir, selected_notebook)
    
    # Display the selected notebook
    display_notebook(notebook_path)
else:
    st.info("No notebooks found in the notebooks directory.")
    
    # Option to upload a notebook
    uploaded_file = st.file_uploader("Upload a notebook (.ipynb file)", type=["ipynb"])
    if uploaded_file is not None:
        # Save the uploaded notebook
        notebook_path = os.path.join(notebooks_dir, uploaded_file.name)
        with open(notebook_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Notebook '{uploaded_file.name}' uploaded successfully!")
        
        # Display the uploaded notebook
        display_notebook(notebook_path)
