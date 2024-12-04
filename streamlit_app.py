import streamlit as st
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import requests
import json
import io
import datetime
from utils import auth, database, dateconverter
from transactions import GetTransactions
from files import convertToExcel
from customers import customers
from institutions import bankSearch
from statements import statements
import uuid

st.set_page_config(page_title="Finicity-like App", layout="wide")

def prettify_name(name):
    """Converts a string like 'customer_transactions_parallaxes_capital_llc' to 'Parallaxes Capital LLC'."""
    words = name.split('_')
    pretty_name = ' '.join(word.capitalize() for word in words)
    return pretty_name

def main():
    conn = database.get_snowflake_connection()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        auth.login_page()
        return  

    taskbar = st.sidebar.radio(
        "Navigation",
        ("Reports", "Institutions", "Customers"),
        index=st.session_state.get('taskbar_index', 0)
    )

    if st.sidebar.button("Logout"):
        auth.logout()

    st.session_state['taskbar_index'] = ["Reports", "Institutions", "Customers"].index(taskbar)

    if taskbar == "Reports":
        st.title("Reports")
        query = "SHOW TABLES IN TESTINGAI.TESTINGAISCHEMA"
        table_names_df = database.run_query(query)
        if table_names_df is not None:
            table_names = table_names_df['name'].tolist()
        fund_name = st.selectbox("Fund Name", table_names, index=st.session_state.get('fund_name_index', 0))
        pretty_fund_name = prettify_name(fund_name)
        st.write(f"You selected: {pretty_fund_name}")
        st.session_state['fund_name_index'] = table_names.index(fund_name)
        
        try:
            query = f"SELECT * FROM {fund_name}" 
            mapping_df = database.run_query(query)
            mapping_dict = mapping_df.to_dict(orient='records')
            st.write(mapping_dict, "here is the mapping dict")
            if mapping_dict:
                customer_id = mapping_dict[0]["CUSTOMER_ID"]
                st.write('records found!')
            else:
                st.write("No mapping found for the selected fund.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")

        start_time = st.text_input("Start Time (IT MUST BE IN THIS FORMAT)", "2024-09-01 00:00:00 UTC")
        end_time = st.text_input("End Time (IT MUST BE IN THIS FORMAT)" , "2024-09-30 23:59:59 UTC")
        UnixStart = dateconverter.human_to_unix(start_time)
        UnixEnd = dateconverter.human_to_unix(end_time)
        
        database1 = st.selectbox("Database", ["Allvue", "Geneva"])
        if "Geneva" in database1:
            gen_report_type = st.selectbox("Geneva Report", ["REC", "ART"])
        report_type = st.multiselect("Report Type", ["Statements", "Transactions"])
    
        st.write("NOTE: It costs money each time you run a transaction or generate a statement. Please be conservative with how many requests you make! The date range and number of transactions do not matter, it is the frequency of requests we are charged on.")
        st.write("NOTE: IF YOU CLICK DOWNLOAD WHILE THE PROGRAM RUNS, IT WILL INTERRUPT. WAIT UNTIL ALL ARE DOWNLOADED")
        if st.button("Generate Report"):
            if "Statements" in report_type:
                statements.getBankStatements(customer_id, mapping_dict, end_time)
            if "Transactions" in report_type:
                transactions = GetTransactions.getCustomerTrans(customer_id, UnixStart, UnixEnd)
                transactions = transactions['transactions']
                fundName = mapping_dict[0]["FUND_NAME"]
                fileName = f"{fundName}_{end_time[5:10]}_transactions"
                if "Allvue" in database1:
                    transactionsConv = GetTransactions.convertTransAllvue(transactions, mapping_dict)
                    st.write(transactionsConv)
                    convertToExcel.TransToExcel(transactionsConv, fileName)
                if "Geneva" in database1:
                    if "REC" in gen_report_type:
                        transactionsConv = GetTransactions.convertTransREC(transactions, mapping_dict)  
                        convertToExcel.TransToExcel(transactionsConv, fileName)  
                    if "ART" in gen_report_type:
                        transactionsConv = GetTransactions.convertTransART(transactions, mapping_dict)  
                        convertToExcel.TransToExcel(transactionsConv, fileName)
        statements.display_download_buttons()

    elif taskbar == "Institutions":
        st.title("Institutions")
        query = "SELECT * FROM TESTINGAI.INSTITUTIONS.INSTITUTIONS"
        instList = pd.read_sql(query, conn) 
        st.write(instList)
        st.write("Can't find your institution? Search for it here:")
            
        search_term = st.text_input("type your bank name here")
        if st.button("Search Institution"):
            st.write(bankSearch.getInstitutions(search_term))
            
    elif taskbar == "Customers":
        customer_ID = ""
        st.title("Add new customer")
        ClientName = st.text_input("Type client's name here. Ex: ExampleFundPartnersLLC.", "ExampleFundPartnersLLC")
        firstName = st.text_input("First name of the client or owner of fund. Ex: John", "John")
        lastName = st.text_input("Last name of the client or owner of fund. Ex: Jingleheimer", "Jingleheimer")

        if st.button("Create Customer"):
            customer_data = customers.makeCustomer(ClientName, firstName, lastName)
            if customer_data:
                customer_ID = customer_data["id"]
                st.write(customer_ID)
                
        if st.button("Generate Connect Link"):
            customerId = st.text_input("input the customer Id")
            customerId = "7036039246"
            connect_link_data = customers.generateConnectLink(customerId, auth.auth["prod"]["pId"])
            st.write(connect_link_data)

        if st.button("Display All Customers"):
            connect_link_data = customers.getcustomers()
            st.write(connect_link_data) 

if __name__ == "__main__":
    main()