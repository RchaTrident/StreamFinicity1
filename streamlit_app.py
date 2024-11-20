import streamlit as st
import snowflake.connector
import pandas as pd

# Move st.set_page_config() to the top, right after imports
st.set_page_config(page_title="Finicity-like App", layout="wide")

#Attempt to import Snowflake, but don't fail if it's not available
try:
    from snowflake.snowpark.context import get_active_session
    snowflake_available = True
except ImportError:
    snowflake_available = False
    
    # Define the taskbar
    taskbar = st.sidebar.radio(
        "Navigation",
        ("Customers", "Authentication", "Institutions", "Transactions")
    )

    # Get the current Snowflake session
    session = get_snowflake_session()

    # Display content based on taskbar selection
    if taskbar == "Authentication":
        show_authentication(session)
    elif taskbar == "Customers":
        show_customers(session)
    elif taskbar == "Institutions":
        show_institutions(session)
    elif taskbar == "Transactions":
        show_transactions(session)

def show_authentication(session):
    st.title("Authentication")
    st.write("Securely authenticate users and manage access tokens.")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            st.success(f"Authenticated as {username}")
    
    with col2:
        st.subheader("Active Sessions")
        if session:
            st.write("Connected to Snowflake")
        else:
            st.warning("Not connected to Snowflake")

def show_customers(session):
    st.title("Customers")
    st.write("Manage customer profiles and account information.")
    
    if session:
        # Placeholder for actual Snowflake query
        customers = pd.DataFrame({
            "CustomerID": range(1, 6),
            "Name": ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Carol White"],
            "Email": ["john@example.com", "jane@example.com", "alice@example.com", "bob@example.com", "carol@example.com"],
            "RegisteredDate": pd.date_range(start="2023-01-01", periods=5)
        })
    else:
        customers = pd.DataFrame(columns=["CustomerID", "Name", "Email", "RegisteredDate"])
    
    st.dataframe(customers)
    
    st.subheader("Add New Customer")
    new_name = st.text_input("Name")
    new_email = st.text_input("Email")
    if st.button("Add Customer"):
        st.success(f"Added customer: {new_name}")

def show_institutions(session):
    st.title("Institutions")
    st.write("View and manage connected financial institutions.")
    
    institutions = ["Bank of America", "Wells Fargo", "Chase", "Citibank", "Capital One"]
    for inst in institutions:
        st.checkbox(inst, key=inst)
    
    st.subheader("Add New Institution")
    new_inst = st.text_input("Institution Name")
    if st.button("Add Institution"):
        st.success(f"Added institution: {new_inst}")

def show_transactions(session):
    st.title("Transactions")
    st.write("View and analyze financial transactions.")
    
    if session:
        # Placeholder for actual Snowflake query
        transactions = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=10),
            "Amount": [100, -50, 200, -75, 300, -100, 150, -200, 250, -150],
            "Description": ["Deposit", "Groceries", "Salary", "Utilities", "Bonus", "Rent", "Freelance", "Shopping", "Investment", "Dining"]
        })
    else:
        transactions = pd.DataFrame(columns=["Date", "Amount", "Description"])
    
    st.dataframe(transactions)
    
    st.subheader("Transaction Analysis")
    st.line_chart(transactions.set_index("Date")["Amount"])

if __name__ == "__main__":
    main()