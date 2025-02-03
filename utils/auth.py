import streamlit as st
import hashlib
import requests
import json
import msal
import streamlit.components.v1 as components
from .database import log_user_login, run_query

auth = {
    "prod": {
        "pId": st.secrets["finicity"]["PARTNER_ID"],
        "secret": st.secrets["finicity"]["SECRET"],
        "key": st.secrets["finicity"]["KEY"]
    },
    "headers": {
        'Finicity-App-Key': st.secrets["finicity"]["KEY"],
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Finicity-App-Token': 'AwardyN4OiUHD6oNJleQ'
    },
    "url": st.secrets["finicity"]["URL"]
}

admins = st.secrets["admin"]["USERS"]

class AuthManager:
    def __init__(self):
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=st.secrets["azure"]["client_id"],
            client_credential=st.secrets["azure"]["client_secret"],
            authority=f"https://login.microsoftonline.com/{st.secrets['azure']['tenant_id']}"
        )

    def get_auth_url(self):
        return self.msal_app.get_authorization_request_url(
            scopes=["User.Read"],
            redirect_uri=st.secrets["azure"]["redirect_uri"]
        )

    def process_microsoft_auth(self, auth_code):
        try:
            token_response = self.msal_app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=["User.Read"],
                redirect_uri=st.secrets["azure"]["redirect_uri"]
            )
            if "access_token" in token_response:
                headers = {'Authorization': f'Bearer {token_response["access_token"]}'}
                user_info = requests.get(
                    'https://graph.microsoft.com/v1.0/me',
                    headers=headers
                ).json()
                
                email = user_info.get('userPrincipalName', '').lower()
                username = email.split('@')[0].upper()
                
                if self.validate_user(username):
                    st.session_state['user_role'] = username
                    st.session_state['logged_in'] = True
                    log_user_login(username)
                    return True
            return False
        except Exception as e:
            st.error(f"SSO Error: {str(e)}")
            return False

    def validate_user(self, username):
        """Validate if the user exists in the system"""
        return st.secrets["users"].get(f"{username.upper()}_USERNAME") is not None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    # Access the nested users section of secrets
    stored_username = st.secrets["users"].get(f"{username.upper()}_USERNAME")
    stored_password = st.secrets["users"].get(f"{username.upper()}_PASSWORD")
    
    if not stored_username or not stored_password:
        st.error("Invalid username")
        return False
    
    if hash_password(password) == hash_password(stored_password):
        st.session_state['user_role'] = username
        st.session_state['logged_in'] = True
        log_user_login(username)
        return True
    else:
        st.error("Invalid password")
        return False

def login_page():
    left_col, main_col, right_col = st.columns([1, 3, 1])
    with main_col:
        st.title("Login")
        
        auth_manager = AuthManager()
        
        # Handle Microsoft SSO callback
        if "code" in st.query_params:
            auth_success = auth_manager.process_microsoft_auth(st.query_params["code"])
            if auth_success:
                st.success("Logged in successfully via Microsoft!")
                # Don't return early, let the main app handle the flow
            else:
                st.error("Microsoft authentication failed")
        
        # Only show login options if not authenticated
        if not st.session_state.get('logged_in', False):
            microsoft_auth_url = auth_manager.get_auth_url()
            st.markdown(f'<a href="{microsoft_auth_url}" class="button">Login with Microsoft</a>', 
                       unsafe_allow_html=True)
            
            st.markdown("---")
            st.write("Or login with username and password:")
            
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
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
                <style>
                    .button {
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #0078d4;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        text-align: center;
                        width: 100%;
                        margin: 10px 0;
                    }
                    .button:hover {
                        background-color: #106ebe;
                    }
                </style>
            """, height=100)
            
            if st.button("Login"):
                if not username or not password:
                    st.error("Please enter both username and password")
                elif authenticate(username, password):
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid credentials")

def logout():
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'user_role' in st.session_state:
        del st.session_state['user_role']
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
            return allowed_tables
        else:
            st.write("No tables found for the user role.")
    else:
        st.write("No role assigned.")