import streamlit as st
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
import snowflake.connector
import requests
import json
import io
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL
from datetime import datetime, timedelta, timezone
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
        today = datetime.now(timezone.utc)
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = today.replace(day=1) - timedelta(days=1)

        start_time_default = first_day_last_month.strftime("%Y-%m-%d 00:00:00 UTC")
        end_time_default = last_day_last_month.strftime("%Y-%m-%d 23:59:59 UTC")

        start_date = st.date_input("Start Date", value=first_day_last_month)
        end_date = st.date_input("End Date", value=last_day_last_month)

        start_time = f"{start_date.strftime('%Y-%m-%d')} 00:00:00 UTC"
        end_time = f"{end_date.strftime('%Y-%m-%d')} 23:59:59 UTC"

        UnixStart = dateconverter.human_to_unix(start_time)
        UnixEnd = dateconverter.human_to_unix(end_time)
        
        database1 = st.selectbox("Database", ["Allvue", "Geneva"])
        if "Geneva" in database1:
            gen_report_type = st.selectbox("Geneva Report", ["REC", "ART"])
        report_type = st.multiselect("Report Type", ["Statements", "Transactions"])
    
        st.write("NOTE: It costs money each time you run a transaction or generate a statement. Please be conservative with how many requests you make! The date range and number of transactions do not matter, it is the frequency of requests we are charged on.")
        st.write("NOTE: IF YOU CLICK DOWNLOAD WHILE THE PROGRAM RUNS, IT WILL INTERRUPT. WAIT UNTIL ALL ARE DOWNLOADED")
        
        if st.button("Generate Report"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
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
        conn = database.get_snowflake_connection()
        instList = pd.read_sql(query, conn)
        instList.rename(columns={'BANK_NAME': 'Bank Name', 'BANK_ID': 'Bank ID', 'BANK_URL': 'Bank URL'}, inplace=True)
        st.dataframe(
            instList,
            column_config={
                "Bank Name": "Bank Name",
                "Bank ID": "Bank ID",
                "Bank URL": st.column_config.LinkColumn("Bank URL"),
            },
            use_container_width=True,
            hide_index=True
        )
        st.write("Can't find your institution? Search for it here:")
        search_term = st.text_input("type your bank name here")
        if st.button("Search Institution"):
            search_results = bankSearch.getInstitutions(search_term)
            
            # Extract relevant fields from the search results
            institutions_list = search_results['institutions']
            filtered_results = [
                {
                    'id': inst['id'],
                    'name': inst['name'],
                    'stateAgg': inst['stateAgg'],
                    'transAgg': inst['transAgg'],
                    'urlLogonApp': inst['urlLogonApp']
                }
                for inst in institutions_list
            ]
            search_results_df = pd.DataFrame(filtered_results)
            search_results_df.rename(columns={'id': 'Bank ID', 'name': 'Bank Name', 'stateAgg': 'Statement Availability: ', 'transAgg': 'Transactions Availability: ', 'urlLogonApp': 'Bank URL'}, inplace=True)

            st.dataframe(
                search_results_df,
                column_config={
                    "Bank Name": "Bank Name",
                    "Bank ID": "Bank ID",
                    "Statement Availability: ": "Statement Availability: ",
                    "Transactions Availability: ": "Transactions Availability: ",
                    "Bank URL": st.column_config.LinkColumn("Bank URL")
                },
                use_container_width=True,
                hide_index=True
            )
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

def display_download_buttons():

    st.write("### Download Statements")
    cols = st.columns([1, 1, 2])
    cols[0].write("**Portfolio Name**")
    cols[1].write("**Date**")
    cols[2].write("**Actions**")

    for i, (file_name, file_content) in enumerate(st.session_state.items()):
        if isinstance(file_content, (bytes, bytearray)) and file_name.endswith(".pdf"):
            portfolio_name, date_str, _account_info = file_name.split('_')
            unique_key_download = f"download-{file_name}-{i}-{uuid.uuid4()}"
            unique_key_delete = f"delete-{file_name}-{i}-{uuid.uuid4()}"
            unique_key_undo = f"undo-{file_name}-{i}-{uuid.uuid4()}"

            with cols[0]:
                st.write(portfolio_name)
            with cols[1]:
                st.write(date_str)
            with cols[2]:
                if st.button("Download", key=unique_key_download):
                    st.download_button(
                        label=f"Download {os.path.basename(file_name)}",
                        data=file_content,
                        file_name=os.path.basename(file_name),
                        mime="application/pdf",
                        key=f"download-{file_name}-{i}"
                    )
                if st.button("Delete", key=unique_key_delete):
                    st.session_state.pop(file_name, None)
                    st.write(f"Deleted {file_name}")
                    if st.button("Undo", key=unique_key_undo):
                        st.session_state[file_name] = file_content
                        st.write(f"Restored {file_name}")

if __name__ == "__main__":
    main()