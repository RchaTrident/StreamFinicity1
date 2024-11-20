import streamlit as st
import snowflake.connector
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