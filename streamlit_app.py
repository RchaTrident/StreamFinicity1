import streamlit as st
import snowflake.connector
import pandas as pd

st.set_page_config(page_title="Finicity-like App", layout="wide")

def init_connection():
    return snowflake.connector.connect(
        user=st.secrets["SF_USER"],
        password=st.secrets["SF_PASSWORD"],
        account=st.secrets["SF_ACCOUNT"],
        database=st.secrets["SF_DATABASE"],
        schema=st.secrets["SF_SCHEMA"], 
        warehouse=st.secrets["SF_WAREHOUSE"],
        role=st.secrets["SF_ROLE"] 
    )

@st.cache_resource
def get_snowflake_connection():
    try:
        return init_connection()
    except Exception as e:
        st.error(f"Error connecting to Snowflake: {e}")
        return None

def run_query(conn, query):
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error running query: {e}")
        return None

def main():
    # Establish Snowflake connection
    conn = get_snowflake_connection()

    # Define the taskbar
    taskbar = st.sidebar.radio(
        "Navigation",
        ("Customers", "Authentication", "Institutions", "Transactions")
    )

    # Display content based on taskbar selection
    if taskbar == "Authentication":
        show_authentication(conn)
    elif taskbar == "Customers":
        show_customers(conn)
    elif taskbar == "Institutions":
        show_institutions(conn)
    elif taskbar == "Transactions":
        show_transactions(conn)

def show_authentication(conn):
    st.title("Authentication")
    st.write("Securely authenticate users and manage access tokens.")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            st.success(f"Authenticated as {username}")
    
    with col2:
        st.subheader("Connection Status")
        if conn:
            st.success("Connected to Snowflake")
        else:
            st.error("Not connected to Snowflake")

def show_customers(conn):
    st.title("Customers")
    st.write("Manage customer profiles and account information.")
    
    if conn:
        # Example of running an actual Snowflake query
        query = "SELECT * FROM YOUR_CUSTOMERS_TABLE LIMIT 10"
        customers = run_query(conn, query)
        
        if customers is not None:
            st.dataframe(customers)
        else:
            st.warning("Unable to fetch customer data")
    else:
        st.error("No Snowflake connection available")
    
    st.subheader("Add New Customer")
    new_name = st.text_input("Name")
    new_email = st.text_input("Email")
    if st.button("Add Customer"):
        st.success(f"Added customer: {new_name}")

def show_institutions(conn):
    st.title("Institutions")
    st.write("View and manage connected financial institutions.")
    
    if conn:
        # Example of running an actual Snowflake query
        query = "SELECT * FROM YOUR_INSTITUTIONS_TABLE"
        institutions = run_query(conn, query)
        
        if institutions is not None:
            for index, row in institutions.iterrows():
                st.checkbox(row['INSTITUTION_NAME'], key=str(row['INSTITUTION_ID']))
    else:
        st.error("No Snowflake connection available")
    
    st.subheader("Add New Institution")
    new_inst = st.text_input("Institution Name")
    if st.button("Add Institution"):
        st.success(f"Added institution: {new_inst}")

def show_transactions(conn):
    st.title("Transactions")
    st.write("View and analyze financial transactions.")
    
    if conn:
        # Example of running an actual Snowflake query
        query = "SELECT * FROM YOUR_TRANSACTIONS_TABLE LIMIT 50"
        transactions = run_query(conn, query)
        
        if transactions is not None:
            st.dataframe(transactions)
            
            # Assuming you have a 'AMOUNT' column for the chart
            if 'AMOUNT' in transactions.columns:
                st.subheader("Transaction Analysis")
                st.line_chart(transactions['AMOUNT'])
        else:
            st.warning("Unable to fetch transactions")
    else:
        st.error("No Snowflake connection available")

if __name__ == "__main__":
    main()