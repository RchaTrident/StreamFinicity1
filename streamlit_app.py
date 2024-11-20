import streamlit as st

st.set_page_config(page_title="Finicity-like App", layout="wide")
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import requests
import json
import io
import datetime
# Assuming utils folder is in the same directory
from utils import auth, database  # Import both auth and database modules


def prettify_name(name):
    """Converts a string like 'customer_transactions_parallaxes_capital_llc' to 'Parallaxes Capital LLC'."""
    words = name.split('_')
    pretty_name = ' '.join(word.capitalize() for word in words)
    return pretty_name


def main():
    # Establish Snowflake connection
    conn = database.get_snowflake_connection()

    # --- Authentication ---
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        auth.login_page()
        return  # Stop execution until user logs in

    # --- App Content (after login) ---
    taskbar = st.sidebar.radio(
        "Navigation",
        ("Reports", "Institutions", "Customers")
    )

    # --- Logout ---
    if st.sidebar.button("Logout"):
        auth.logout()

    if taskbar == "Reports":
        st.title("Reports")
        
        # Query to fetch table names from the current database and schema
        query = "SHOW TABLES IN TESTINGAI.TESTINGAISCHEMA"
        
        # Execute the query and load table names into a DataFrame
        @st.cache_data(ttl=600)  # Cache the results for 10 minutes to avoid repeated queries
        def get_table_names():
            return pd.read_sql(query, conn)  # Use conn here
            
        # Fetch the table names
        table_names_df = get_table_names()
        
        # Extract table names from the DataFrame
        table_names = table_names_df['name'].tolist()
        
        # Display a selectbox with the table names
        fund_name = st.selectbox("Fund Name", table_names)
        
        pretty_fund_name = prettify_name(fund_name)

        # Display the prettified fund name
        st.write(f"You selected: {pretty_fund_name}")
        try:
            # Assuming you have a session object to interact with Snowflake
            mapping_df = conn.table(fund_name).to_pandas()  # Use conn here
            mapping_dict = mapping_df.to_dict(orient='records')
            if mapping_dict:
                customer_id = mapping_dict[0]["CUSTOMER_ID"]
                st.write('records found!')
            else:
                st.write("No mapping found for the selected fund.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")
        
        
        def human_to_unix(human_time):
            # Parse the human-readable time string into a datetime object
            dt_object = datetime.datetime.strptime(human_time, "%Y-%m-%d %H:%M:%S %Z")
            
            # Convert the datetime object to a Unix timestamp
            unix_timestamp = int(dt_object.timestamp())
            
            return unix_timestamp
            
            
        start_time = st.text_input("Start Time (IT MUST BE IN THIS FORMAT)", "2024-09-01 00:00:00 UTC")
        end_time = st.text_input("End Time (IT MUST BE IN THIS FORMAT)" , "2024-09-30 23:59:59 UTC")
        UnixStart = human_to_unix(start_time)
        UnixEnd = human_to_unix(end_time)

        database1 = st.selectbox("Database", ["Allvue", "Geneva"])
        if "Geneva" in database1:
            gen_report_type = st.selectbox("Geneva Report", ["REC", "ART"])
        # Transaction type input
        report_type = st.multiselect("Report Type", ["Statements", "Transactions"])
        
        @st.cache_data
        def getCustomerTrans(customerId, fromDate, toDate):
            auth.get_token()  # Get token using the function from auth.py
            params = {
                "fromDate": fromDate,
                "toDate": toDate,
                "limit": 1000,
                "includePending": True
            }
            response = requests.get(url=f"{auth.auth['url']}/aggregation/v3/customers/{customerId}/transactions", headers=auth.auth['headers'], params=params)  # Use auth.auth
            json_data = json.loads(response.text)
            return json_data

        st.write("NOTE: It costs money each time you run a transaction or generate a statement. Please be conservative with how many requests you make! The date range and number of transactions do not matter, it is the frequncy of requests we are charged on.")
        if st.button("Generate Report"):
            if "Statements" in report_type:
                # Generate statements report (currently blank)
                statements_df = pd.DataFrame()  # Placeholder for actual data
                buffer = io.BytesIO()
                statements_df.to_excel(buffer, index=False)
                buffer.seek(0)
                st.download_button(
                    label="Download Statements Report",
                    data=buffer,
                    file_name="statements_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("Statements report generated!")
            if "Transactions" in report_type:
                # Fetch transactions data
                transactions = getCustomerTrans(customer_id, UnixStart, UnixEnd)
                transactions = transactions['transactions']
                if "Allvue" in database1:
                    transactionsConv = convertTransAllvue(transactions, mapping_dict)  # Assuming you have this function defined
                    TransToExcel(transactionsConv)  # Assuming you have this function defined
                if "Geneva" in database1:
                    if "REC" in gen_report_type:
                        transactionsConv = convertTransREC(transactions, mapping_dict)  # Assuming you have this function defined
                        TransToExcel(transactionsConv)  # Assuming you have this function defined
                    if "ART" in gen_report_type:
                        transactionsConv = convertTransART(transactions, mapping_dict)  # Assuming you have this function defined
                        TransToExcel(transactionsConv)  # Assuming you have this function defined

    elif taskbar == "Institutions":
        st.title("Institutions")
        query = "SELECT * FROM TESTINGAI.INSTITUTIONS.INSTITUTIONS"
        instList = pd.read_sql(query, conn)  # Use conn here
        st.write(instList)
        st.write("Can't find your institution? Search for it here:")
        
        @st.cache_data
        def getInstitutions(search):
            auth.get_token()  # Get token using the function from auth.py
            token = auth.get_token()  # Get token using the function from auth.py
            auth.auth['headers']['Finicity-App-Token'] = token  # Use auth.auth
            params = {
                "start": 1,
                "limit" : 1000,
                "search" : search
            }
        
            response = requests.get(url = f"{auth.auth['url']}/institution/v2/institutions", headers=auth.auth['headers'], params=params)  # Use auth.auth
            data = response.json()
            return data
            
        search_term = st.text_input("type your bank name here")
        if st.button("Search Institution"):
            st.write(getInstitutions(search_term))
            
    
    elif taskbar == "Customers":
        customer_ID = ""
        st.title("Add new customer")
        ClientName = st.text_input("Type client's name here. Ex: ExampleFundPartnersLLC. Do not use spaces.","ExampleFundPartnersLLC" )
        firstName = st.text_input("First name of the client or owner of fund. Ex: John", "John")
        lastName = st.text_input("Last name of the client or owner of fund. Ex: Jingleheimer", "Jingleheimer")


        customerBody = {
            "username": ClientName,
            "firstName": firstName,
            "lastName": lastName,
            "phone": "404-233-5275",
            "email": f"{ClientName}@tridenttrust.com",
            "applicationId" : '8407cf1e-b044-486f-a2bb-ed78cbfe4f16'
            }
            
        if st.button("Create Customer"):
            customer_data = makeCustomer(customerBody)  # Assuming you have this function defined
            if customer_data:
                customer_ID = customer_data["id"]
                st.write(customer_ID)
                
        if st.button("Generate Connect Link"):
            st.text_input("input the customer Id")
            connect_link_data = generateConnectLink(7034897269,auth.auth["prod"]["pId"] )  # Use auth.auth
            st.write(connect_link_data)  # Assuming you have this function defined

if __name__ == "__main__":
    main()