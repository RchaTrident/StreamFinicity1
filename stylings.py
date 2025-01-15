import streamlit as st

# Custom CSS for modern fintech styling
custom_css = """
    <style>
        /* Main container styling */
        .main {
            padding: 1rem;
            background-color: #ffffff
            
        }
        
        /* Card styling for containers */
        .stApp {
            background-color: #ffffff
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #1e2130;
            padding: 2rem 1rem;
        }
        
        /* Make all sidebar text white */
        [data-testid="stSidebar"] [data-testid="stMarkdown"],
        [data-testid="stSidebar"] .stRadio label,
        [data-testid="stSidebar"] .stButton,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: white !important;
        }

        /* Make sidebar collapse button white */
        button[kind="secondary"] svg {
            color: white !important;
            fill: white !important;
        }

        [data-testid="stSidebar"] .stRadio input {
            border-color: white !important;
        }

        [data-testid="stSidebar"] .block-container {
            color: white;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #0099cc;  /* Trident Trust light blue */
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            border: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            background-color: #808080;  /* Light grey hover state */
            color: white !important;     /* Force text to stay white */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        .stTextInput input {
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            padding: 0.5rem;
        }
        
        [data-testid="stDataFrame"] {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        .dataframe th {
            background-color: #f8f9fa;
            color: #1e2130;
            font-weight: 600;
        }
        
        h1, h2, h3 {
            color: #1e2130;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .stSelectbox label {
            color: #1e2130;
            font-weight: 500;
        }
        
        .stDateInput {
            margin-bottom: 1rem;
        }
        
        .stMultiSelect {
            margin-bottom: 1rem;
        }
    </style>
"""

def apply_styles():
    st.markdown(custom_css, unsafe_allow_html=True)

def init_styling():
    apply_styles()