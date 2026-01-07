import streamlit as st
from PIL import Image

# Page Config
st.set_page_config(
    page_title="Nextis - POS Solutions",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for White Page Design
st.markdown("""
<style>
    /* White Page Background */
    .stApp {
        background-color: #ffffff;
        color: #333333;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        font-family: 'Heebo', sans-serif;
        color: #1a1a1a;
    }
    
    /* Card/Features Styling */
    .feature-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-top: 4px solid #e63946;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    /* Button Styling */
    .stButton>button {
        background-color: #e63946;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #c1121f;
        color: white;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Hero Section ---
col1, col2 = st.columns([1, 2])

with col1:
    try:
        # Load logo
        image = Image.open('assets/logo.jpg')
        st.image(image, width=250)
    except:
        st.error("Logo not found. Please ensure assets/logo.jpg exists.")

with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    st.title("Nextis POS Solutions")
    st.subheader("Transform Your Business with Modern Point of Sale")
    st.write("""
    **Nextis** provides cutting-edge systems designed for businesses of all sizes. 
    Managing clients, inventory, and analytics has never been easier.
    """)
    st.button("Get Started")

st.markdown("---")

# --- Features Section (Mocking 'What does this company show') ---
st.header("Why Choose Nextis?")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card">
        <h3>🚀 Fast Performance</h3>
        <p>Optimized for speed to keep your checkout lines moving efficiently.</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="feature-card">
        <h3>🌍 Cloud Integration</h3>
        <p>Access your business data from anywhere in the world, securely.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Smart Analytics</h3>
        <p>Real-time insights into sales, inventory, and customer growth.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<center>© 2026 Nextis POS. All Rights Reserved.</center>", unsafe_allow_html=True)
