import streamlit as st
import snowflake.connector
from datetime import datetime, timedelta
import pandas as pd

@st.cache_resource
def get_snowflake_connection():
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["SF_USER"],
            password=st.secrets["SF_PASSWORD"],
            account=st.secrets["SF_ACCOUNT"],
            database=st.secrets["SF_DATABASE"],
            schema=st.secrets["SF_SCHEMA"],
            warehouse=st.secrets["SF_WAREHOUSE"],
            role=st.secrets["SF_ROLE"]
        )
        return conn
    except Exception as e:
        st.error(f"Snowflake Connection Error: {e}")
        return None

def run_query(query, params=None):
    conn = get_snowflake_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Query Error: {e}")
        return None
    
def create_statements_table_if_not_exists(fund_name):
    sanitized_fund_name = fund_name.replace(" ", "_")
    table_name = f"TESTINGAI.STATEMENTS.{sanitized_fund_name}_statements"
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id STRING,
        customer_id STRING,
        account_id STRING,
        portfolio STRING,
        date STRING,
        file_name STRING,
        file_content BINARY
    )
    """
    run_query(create_table_query)

def log_user_login(user_id):
    login_date = datetime.now().date()
    login_time = (datetime.now() - timedelta(hours=5)).time()
    query = f"""
    INSERT INTO TESTINGAI.USER_LOGS.{user_id} (USER_ID, LOGIN_DATE, LOGIN_TIME)
    VALUES (%s, %s, %s)
    """
    params = (user_id, login_date, login_time)
    run_query(query, params)