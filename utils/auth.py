import streamlit as st
import hashlib
import requests
import json


def hash_password(password):
    """Simple password hashing (for demonstration - use more secure methods in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    """
    Check credentials against secrets
    """
    stored_username = st.secrets.get("ADMIN_USERNAME")
    stored_password = st.secrets.get("ADMIN_PASSWORD")
    
    if not stored_username or not stored_password:
        st.error("Authentication credentials not configured")
        return False
    
    # Compare hashed passwords
    return (username == stored_username and 
            hash_password(password) == hash_password(stored_password))

def login_page():
    """
    Streamlit login page
    """
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['logged_in'] = True
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

def logout():
    """
    Logout functionality
    """
    st.session_state['logged_in'] = False
    st.experimental_rerun()


# --- Finicity Integration ---
auth = {
    "prod": {
        "pId": st.secrets["FINICITY_PARTNER_ID"],
        "secret": st.secrets["FINICITY_SECRET"],
        "key": st.secrets["FINICITY_KEY"]
    },
    "headers": {
        'Finicity-App-Key': st.secrets["FINICITY_KEY"],
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Finicity-App-Token': 'AwardyN4OiUHD6oNJleQ'  # Placeholder, will be updated
    },
    "url": st.secrets["FINICITY_URL"]
}

def get_token():
    body = {
        "partnerId": auth["prod"]["pId"],
        "partnerSecret": auth["prod"]["secret"]
    } 
    session = requests.Session()
    response = session.post(
    url=f"{auth['url']}/aggregation/v2/partners/authentication",
    json=body,
    headers=auth['headers'],
    # verify=cert_path  # If you need to use a certificate for the connection
    )
    if response.status_code == 200:
        auth['headers']['Finicity-App-Token'] = response.json()['token']
        return auth['headers']['Finicity-App-Token']
    else:
        st.error(f"Failed to get token. Status code: {response.status_code}, Response: {response.text}")
        return None

# --- Example usage (after successful login) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
else:
    # User is logged in, show Finicity related content
    st.title("Finicity Integration")

    # Get Finicity token
    if st.button("Get Finicity Token"):
        token = get_token()
        if token:
            st.success(f"Token obtained: {token}")

    # ... rest of your Finicity integration code ... 

    if st.button("Logout"):
        logout() 