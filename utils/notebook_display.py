"""
Utility functions for displaying Jupyter notebooks in Streamlit
"""

import streamlit as st
import nbformat
from nbconvert import HTMLExporter
import os

def display_notebook(notebook_path):
    """
    Display a Jupyter notebook in Streamlit
    
    Args:
        notebook_path (str): Path to the notebook file (.ipynb)
    """
    if not os.path.exists(notebook_path):
        st.error(f"Notebook file not found: {notebook_path}")
        return
    
    try:
        # Read the notebook
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        
        # Convert to HTML
        html_exporter = HTMLExporter()
        html_exporter.template_name = 'classic'
        (body, _) = html_exporter.from_notebook_node(notebook)
        
        # Display in Streamlit
        st.components.v1.html(body, scrolling=True, height=800)
        
    except Exception as e:
        st.error(f"Error displaying notebook: {str(e)}")
