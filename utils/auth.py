import streamlit as st
import hashlib
import requests
import json
import streamlit.components.v1 as components
from .database import log_user_login, run_query

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
        'Finicity-App-Token': 'AwardyN4OiUHD6oNJleQ'
    },
    "url": st.secrets["FINICITY_URL"]
}

admins = json.loads(st.secrets["ADMINS"])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    stored_username = st.secrets.get(f"{username.upper()}_USERNAME")
    stored_password = st.secrets.get(f"{username.upper()}_PASSWORD")
    if not stored_username or not stored_password:
        st.error("Authentication credentials not configured")
        return False
    
    if hash_password(password) == hash_password(stored_password):
        st.session_state['user_role'] = username
        return True
    else:
        return False

def login_page():
    left_col, main_col, right_col = st.columns([1, 3, 1])
    with main_col:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Custom HTML to trigger input events
        components.html("""
            <script>
                const usernameInput = document.querySelector('input[aria-label="Username"]');
                const passwordInput = document.querySelector('input[aria-label="Password"]');
                
                usernameInput.addEventListener('input', () => {
                    usernameInput.dispatchEvent(new Event('change', { bubbles: true }));
                });
                
                passwordInput.addEventListener('input', () => {
                    passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                });
            </script>
        """, height=0)
        
        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password")
            elif authenticate(username, password):
                st.session_state['logged_in'] = True
                log_user_login(username)
                st.success("Logged in successfully!")
                st.rerun() 
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state['logged_in'] = False
    st.rerun() 

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
    )
    if response.status_code == 200:
        auth['headers']['Finicity-App-Token'] = response.json()['token']
        return auth['headers']['Finicity-App-Token']
    else:
        st.error(f"Failed to get token. Status code: {response.status_code}, Response: {response.text}")
        return None

def display_content():
    user_role = st.session_state.get('user_role')
    
    if user_role:
        st.write(f"Logged in as: {user_role}")
        
        if user_role in admins:
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'TESTINGAISCHEMA'
            AND TABLE_CATALOG = 'TESTINGAI'
            """
        else:
            query = f"SELECT TABLE_NAME FROM TESTINGAI.USER_LOGS.USER_TABLE_MAPPING WHERE USER_ID = '{user_role}'"
            
        tables_df = run_query(query)
        if tables_df is not None:
            allowed_tables = tables_df['TABLE_NAME'].tolist()
            # st.write("Access to tables:", allowed_tables)
            return allowed_tables
        else:
            st.write("No tables found for the user role.")
    else:
        st.write("No role assigned.")
    


if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        if st.button("Logout"):
            logout()
    else:
        login_page()