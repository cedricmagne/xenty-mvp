import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import environment variables module (which auto-loads .env)
from utils.env_loader import get_env_var
from utils.data_loader import load_data

# Set page title
st.set_page_config(page_title="Dataset Visualization", layout="wide")

# Page header
st.title("Crypto Projects Dataset Exploration")
st.write("This page allows you to explore and analyze the crypto projects dataset.")

# Load the data using the centralized data loader

# Load the data
df = load_data()

if df is not None:
    # Display basic information
    st.header("Dataset Overview")
    
    # Show dataset shape
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Number of Records", df.shape[0])
    with col2:
        st.metric("Number of Features", df.shape[1])
    
    # Data preview with options
    st.subheader("Data Preview")
    
    # Add tabs for different views
    tab1, tab2, tab3 = st.tabs(["Data Sample", "Column Information", "Statistics"])
    
    with tab1:
        # Display options in a single row
        col1, col2 = st.columns([1, 2])
        with col1:
            sample_size = st.selectbox("Select sample size", [10, 50, min(100, len(df))], index=0)
        with col2:
            sample_method = st.radio("Sampling method", ["Top rows", "Random sample"], horizontal=True)
        
        if sample_method == "Top rows":
            st.dataframe(df.head(sample_size), use_container_width=True)
        else:
            st.dataframe(df.sample(sample_size), use_container_width=True)
    
    with tab2:
        # Column information
        column_info = pd.DataFrame({
            'Column': df.columns,
            'Type': df.dtypes.astype(str),
            'Non-Null Count': df.count().values,
            'Null Count': df.isna().sum().values,
            'Null %': (df.isna().sum() / len(df) * 100).round(2).astype(str) + '%'
        })
        st.dataframe(column_info, use_container_width=True)
        
        # Column selector for unique values
        st.subheader("Column Unique Values")
        selected_column = st.selectbox("Select a column to see unique values", df.columns)
        
        # Display unique values count
        unique_count = df[selected_column].nunique()
        st.write(f"Column '{selected_column}' has {unique_count} unique values")
        
        # Show unique values if not too many
        if unique_count <= 50:  # Only show if not too many unique values
            unique_values = df[selected_column].value_counts().reset_index()
            unique_values.columns = [selected_column, 'Count']
            st.dataframe(unique_values, use_container_width=True)
        else:
            st.write(f"Too many unique values to display ({unique_count}). Here's a sample:")
            st.dataframe(df[selected_column].value_counts().head(20).reset_index(), use_container_width=True)
    
    with tab3:
        # Numerical columns for statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            st.write("Descriptive Statistics for Numerical Columns")
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)
        else:
            st.write("No numerical columns found in the dataset.")
    
    # Advanced filtering
    st.header("Data Filtering")
    
    # Select columns to display
    st.subheader("Select Columns to Display")
    all_columns = st.checkbox("Select all columns", value=True)
    
    if all_columns:
        selected_columns = df.columns.tolist()
    else:
        selected_columns = st.multiselect("Choose columns", df.columns.tolist(), default=df.columns[:5].tolist())
    
    # Text search filter
    st.subheader("Search in Dataset")
    search_col, search_term = None, None
    
    col1, col2 = st.columns([1, 2])
    with col1:
        search_col = st.selectbox("Search column", ["Any column"] + df.columns.tolist())
    with col2:
        search_term = st.text_input("Search term")
    
    # Filter the dataframe based on search
    filtered_df = df.copy()
    
    if search_term:
        if search_col == "Any column":
            # Search in any string column
            mask = pd.Series(False, index=df.index)
            for col in df.select_dtypes(include=['object']).columns:
                mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = filtered_df[mask]
        else:
            # Search in specific column
            filtered_df = filtered_df[filtered_df[search_col].astype(str).str.contains(search_term, case=False, na=False)]
    
    # Show filtered data
    st.subheader("Filtered Data")
    st.write(f"Showing {len(filtered_df)} of {len(df)} records")
    st.dataframe(filtered_df[selected_columns], use_container_width=True)
    
    # Download filtered data
    st.download_button(
        label="Download filtered data as CSV",
        data=filtered_df[selected_columns].to_csv(index=False).encode('utf-8'),
        file_name='filtered_crypto_projects.csv',
        mime='text/csv',
    )
    
    # Data visualization section
    st.header("Data Visualization")
    
    # Only proceed if we have numerical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        # Select visualization type
        viz_type = st.selectbox(
            "Select visualization type",
            ["Histogram", "Scatter Plot", "Box Plot", "Bar Chart"]
        )
        
        if viz_type == "Histogram":
            col = st.selectbox("Select column for histogram", numeric_cols)
            fig = px.histogram(filtered_df, x=col, title=f"Histogram of {col}")
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Scatter Plot":
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("Select X-axis column", numeric_cols)
            with col2:
                y_col = st.selectbox("Select Y-axis column", numeric_cols, index=min(1, len(numeric_cols)-1))
                
            color_col = st.selectbox("Select column for color (optional)", [None] + df.columns.tolist())
            
            fig = px.scatter(
                filtered_df, x=x_col, y=y_col, color=color_col,
                title=f"Scatter Plot: {x_col} vs {y_col}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Box Plot":
            col = st.selectbox("Select column for box plot", numeric_cols)
            group_col = st.selectbox("Group by (optional)", [None] + df.select_dtypes(include=['object']).columns.tolist())
            
            if group_col:
                # Limit to top categories if too many
                top_categories = filtered_df[group_col].value_counts().nlargest(10).index.tolist()
                fig = px.box(filtered_df[filtered_df[group_col].isin(top_categories)], 
                             x=group_col, y=col, 
                             title=f"Box Plot of {col} by {group_col} (top 10 categories)")
            else:
                fig = px.box(filtered_df, y=col, title=f"Box Plot of {col}")
                
            st.plotly_chart(fig, use_container_width=True)
            
        elif viz_type == "Bar Chart":
            # For bar chart, we need a categorical column and a numeric column
            cat_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if cat_cols:
                col1, col2 = st.columns(2)
                with col1:
                    cat_col = st.selectbox("Select categorical column", cat_cols)
                with col2:
                    num_col = st.selectbox("Select numeric column", numeric_cols)
                    
                # Get top categories
                top_n = st.slider("Number of top categories to show", min_value=5, max_value=20, value=10)
                top_cats = filtered_df[cat_col].value_counts().nlargest(top_n).index
                
                # Prepare data for bar chart
                chart_data = filtered_df[filtered_df[cat_col].isin(top_cats)].groupby(cat_col)[num_col].mean().reset_index()
                fig = px.bar(chart_data, x=cat_col, y=num_col, title=f"Average {num_col} by {cat_col} (Top {top_n})")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No categorical columns available for bar chart.")
    else:
        st.write("No numerical columns found for visualization.")

else:
    st.error("Failed to load the dataset. Please check if the file exists and is accessible.")
    
    # Provide a file uploader as an alternative
    st.subheader("Upload a CSV file instead")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully!")
        st.dataframe(df.head(), use_container_width=True)