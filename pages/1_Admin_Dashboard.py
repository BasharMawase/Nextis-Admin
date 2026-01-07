import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_processor import load_and_clean_data

st.set_page_config(page_title="Nextis Admin", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Enhanced Dark Mode Dashboard
st.markdown("""
<style>
    /* Dark Mode Background with subtle gradient */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1d29 100%);
        color: #fafafa;
    }
    
    /* Sidebar Dark with gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d24 0%, #0e1117 100%);
        border-right: 1px solid #2d3748;
    }
    
    /* Card Style for Search Results - Enhanced Dark Mode */
    .business-card {
        background: linear-gradient(135deg, #1e2330 0%, #252b3b 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 24px;
        border-left: 5px solid #e63946;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        margin-bottom: 24px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .business-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(230,57,70,0.3);
    }
    
    .card-title {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 12px;
        letter-spacing: -0.5px;
    }
    
    .card-detail {
        color: #cbd5e0;
        font-size: 1rem;
        margin-bottom: 8px;
        line-height: 1.6;
    }
    
    /* Input fields enhanced dark mode */
    .stTextInput input {
        background: linear-gradient(135deg, #1e2330 0%, #252b3b 100%);
        color: #fafafa;
        border: 2px solid #2d3748;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #e63946;
        box-shadow: 0 0 0 3px rgba(230,57,70,0.1);
    }
    
    /* Metrics enhanced */
    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0aec0;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #e63946 0%, #c1121f 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(230,57,70,0.4);
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #1e2330 0%, #252b3b 100%);
        border: 2px dashed #2d3748;
        border-radius: 12px;
        padding: 20px;
    }
    
    /* Success/Warning messages */
    .stSuccess {
        background: linear-gradient(135deg, #1e3a2f 0%, #2d5a45 100%);
        border-left: 4px solid #48bb78;
        border-radius: 8px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #3a2e1e 0%, #5a4a2d 100%);
        border-left: 4px solid #ed8936;
        border-radius: 8px;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #2d3748 50%, transparent 100%);
        margin: 2rem 0;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1d24;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2d3748;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #e63946;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Admin Data Dashboard")
st.markdown("Upload client files, search records, and view analytics.")

# --- Sidebar: Upload & Filters ---
with st.sidebar:
    st.header("Upload Data")
    uploaded_files = st.file_uploader(
        "Upload Excel/CSV Files", 
        type=['xlsx', 'xls', 'csv'], 
        accept_multiple_files=True
    )
    
    st.markdown("---")
    st.header("Filters")
    location_filter = st.selectbox("Filter by Location", ["All"])

# --- Main Logic ---
if uploaded_files:
    # Process Data
    df = load_and_clean_data(uploaded_files)
    
    if not df.empty:
        # Update Location Filter
        locations = ["All"] + sorted(df['Location'].astype(str).unique().tolist())
        # If sidebar selection is valid, filter
        if location_filter != "All":
            df = df[df['Location'] == location_filter]
        
        # --- Search Business Section (Moved to Top) ---
        st.subheader("🔍 Search Business")
        search_query = st.text_input("Enter Business Name", placeholder="Type business name...")
        
        if search_query:
            # Case-insensitive partial match
            results = df[df['Business Name'].astype(str).str.contains(search_query, case=False, na=False)]
            
            if not results.empty:
                st.success(f"Found {len(results)} matches")
                for _, row in results.iterrows():
                    # Beautiful Card Render
                    # Build More Info Table
                    more_info_html = '<div style="margin-top:10px; border-top: 1px solid #eee; padding-top: 10px;">'
                    for key, val in row.items():
                        if key not in ['Business Name', 'Location', 'Phone', 'AnyDesk', 'source_file', 'Location_Normalized']:
                            more_info_html += f'<div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:0.9rem;"><span style="color:#666; font-weight:600;">{key}:</span> <span>{val}</span></div>'
                    more_info_html += '</div>'

                    st.markdown(f"""
                    <div class="business-card">
                        <div class="card-title">{row['Business Name']}</div>
                        <div class="card-detail">📍 <b>Location:</b> {row['Location']}</div>
                        <div class="card-detail" style="color: #2a9d8f; font-weight: bold;">
                            📞 <b>Phone:</b> {row.get('Phone', 'אין')}
                        </div>
                        <div class="card-detail" style="background-color: #ffe8cc; padding: 5px; border-radius: 4px; display: inline-block; margin-top: 5px;">
                            💻 <b>AnyDesk:</b> <span style="color: #d00000; font-family: monospace; font-size: 1.1em;">{row.get('AnyDesk', 'אין')}</span>
                        </div>
                        <div class="card-detail" style="margin-top: 5px; font-size: 0.8rem; color: #888;">
                            📂 Source: {row.get('source_file', 'Unknown')}
                        </div>
                        <details style="margin-top: 10px;">
                            <summary style="cursor: pointer; color: #e63946; font-weight: 500;">More Info</summary>
                            {more_info_html}
                        </details>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No businesses found matching that name.")
        
        st.markdown("---")
        
        # --- Analytics Section ---
        st.subheader("📊 Location Analysis - Top 10 Cities")
        
        # Normalize city names to combine variations
        def normalize_city(city):
            city = str(city).strip()
            # Combine באקה variations
            if 'באקה' in city:
                return 'באקה אל גרבייה'
            return city
        
        # Apply normalization
        df['Location_Normalized'] = df['Location'].apply(normalize_city)
        
        # Get location counts - TOP 10 ONLY
        loc_counts = df['Location_Normalized'].value_counts().head(10)
        total_clients = len(df)
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Clients", total_clients)
        with col2:
            st.metric("🌍 Unique Locations", len(df['Location_Normalized'].unique()))
        with col3:
            st.metric("🏆 Top Location", loc_counts.index[0] if len(loc_counts) > 0 else "N/A")
        
        st.markdown("---")
        
        # Create a grid of location cards
        st.markdown("### Top 10 Location Breakdown")
        
        # Display locations in a grid (2 columns)
        locations_list = list(loc_counts.items())
        for i in range(0, len(locations_list), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(locations_list):
                    location, count = locations_list[i + j]
                    percentage = (count / total_clients) * 100
                    
                    with col:
                        # Create enhanced styled card
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #1e2330 0%, #252b3b 100%); 
                                    padding: 24px; 
                                    border-radius: 12px; 
                                    border-left: 5px solid #e63946; 
                                    margin-bottom: 20px; 
                                    box-shadow: 0 8px 16px rgba(0,0,0,0.4);
                                    transition: all 0.3s ease;
                                    cursor: pointer;">
                            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                                <span style="font-size: 1.8rem; margin-right: 12px;">📍</span>
                                <h3 style="margin: 0; color: #ffffff; font-weight: 700; font-size: 1.2rem; letter-spacing: -0.3px;">{location}</h3>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px;">
                                <div>
                                    <div style="font-size: 0.75rem; color: #a0aec0; margin-bottom: 4px;">CLIENTS</div>
                                    <div style="font-size: 2.2rem; font-weight: 700; color: #e63946;">{count}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.75rem; color: #a0aec0; margin-bottom: 4px;">PERCENTAGE</div>
                                    <div style="font-size: 1.8rem; font-weight: 600; color: #48bb78;">{percentage:.1f}%</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- Data Table View ---
        st.markdown("### Raw Data")
        with st.expander("View Full Dataset"):
            st.dataframe(df)
            
    else:
        st.warning("Uploaded files contained no valid data.")

else:
    st.info("👋 Welcome! Please upload data files (Excel/CSV) in the sidebar to begin.")
    # Show mock data download helper
    with open("utils/generate_mock_data.py", "r") as f:
        pass # Just ensuring it exists
    
    st.markdown("---")
    st.markdown("Need sample data?")
    
    # Check if mock file exists to provide download button
    if os.path.exists("mock_clients_hebrew.xlsx"):
        with open("mock_clients_hebrew.xlsx", "rb") as file:
            btn = st.download_button(
                    label="Download Mock Hebrew Data",
                    data=file,
                    file_name="mock_clients_hebrew.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
