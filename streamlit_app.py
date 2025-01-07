import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import uuid
import json
from utils import auth, database, dateconverter
from accounts import accounts
import numpy as np
import io


@st.cache_resource
def get_snowflake_connection():
    return database.get_snowflake_connection()

@st.cache_data
def load_data(query, params=None):
    conn = get_snowflake_connection()
    return pd.read_sql(query, conn, params=params)

def reset_session_state(except_keys):
    for key in list(st.session_state.keys()):
        if key not in except_keys:
            del st.session_state[key]

def prettify_name(name):
    """Converts a string like 'customer_transactions_parallaxes_capital_llc' to 'Parallaxes Capital LLC'."""
    words = name.split('_')
    pretty_name = ' '.join(word.capitalize() for word in words)
    return pretty_name

st.image("tridentlogo.png", use_column_width=True)


def main():
    conn = get_snowflake_connection()
    user_role = st.session_state.get('user_role')
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        auth.login_page()
        return  
    if 'logged_in' in st.session_state:
        
        auth.get_token()
        
    if user_role == "TRIDENT_TITUS":
        taskbar = st.sidebar.radio(
        "Navigation",
        ("Reports", "Institutions", "Customers", "Accounts"),
        index=st.session_state.get('taskbar_index', 0)
    )
    else:
        taskbar = st.sidebar.radio(
            "Navigation",
            ("Reports", "Institutions", "Customers"),
            index=st.session_state.get('taskbar_index', 0)
        )
    # print("--------------------------------------------------------")
    print("Current session state login status:", st.session_state["user_role"], st.session_state["logged_in"])
    # if st.button("Reset Session State"):
    #     reset_session_state(['user_role', 'logged_in'])
    #     st.success("Session state reset except 'user_role' and 'logged_in'")
    if st.sidebar.button("Logout"):
        auth.logout()
    # st.session_state['taskbar_index'] = ["Reports", "Institutions", "Customers"].index(taskbar)

    if taskbar == "Reports":
        st.title("Reports")
        table_names = auth.display_content()
        fund_name = st.selectbox("Fund Name", table_names, index=st.session_state.get('fund_name_index', 0))
        pretty_fund_name = prettify_name(fund_name)
        st.write(f"You selected: {pretty_fund_name}")

        query = f"SELECT * FROM {fund_name}" 
        mapping_df = database.run_query(query)
        mapping_dict = mapping_df.to_dict(orient='records')
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

        customerId = mapping_dict[0]["CUSTOMER_ID"]
        if st.button("Generate Cashflows Report"):
            query = f"SELECT ACCOUNT_ID FROM {fund_name}" 
            account_mapping_df = database.run_query(query)
            account_mapping_dict = account_mapping_df.to_dict(orient='records')
            account_ids = ', '.join(d['ACCOUNT_ID'] for d in account_mapping_dict)
            print(account_ids, "the account ids", type(account_ids), 'type of account ids')
            from cashflows import cashflows
            fromDate = start_time
            print(fromDate, "from date")
            consumer = cashflows.getConsumer(customerId)
            consumer_data = json.loads(consumer.text)
            if 200 <= consumer.status_code <= 300:
                print(consumer.status_code, "the status code", consumer_data, "the consumer data")
                st.write(cashflows.cashflowAna(customerId,"personal", fromDate, account_ids))        
            else: 
                fundName = mapping_dict[0]["FUND_NAME"]
                print(fundName)
                st.write(cashflows.makeConsumer(customerId, fundName))
                st.write(cashflows.cashflowAna(customerId,"business", fromDate, account_ids))

        if st.button("Generate Report"):
            reset_session_state(['user_role', 'logged_in'])
            st.success("Session state reset except 'user_role' and 'logged_in'")

            from customers import customers
            from transactions import GetTransactions
            from files import convertToExcel
            from statements import statements
            
            if "Statements" in report_type:
                customers.refreshCustomerAccounts(customerId)
                statements.getBankStatements(customerId, mapping_dict, end_time)
            if "Transactions" in report_type:
                customers.refreshCustomerAccounts(customerId)
                transactions = GetTransactions.getCustomerTrans(customerId, UnixStart, UnixEnd)
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
                        convertToExcel.TransToExcelART(transactionsConv, fileName)

            statements.display_download_buttons()
    
    if taskbar == "Institutions":
        st.title("Institutions")
        query = "SELECT * FROM TESTINGAI.INSTITUTIONS.INSTITUTIONS"
        conn = get_snowflake_connection()
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
            # Conditional import for institution search
            from institutions import bankSearch
            search_results = bankSearch.getInstitutions(search_term)
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
    if taskbar == "Customers":
        customer_ID = ""
        st.title("Add new customer")

        from customers import customers
        
        ClientName = st.text_input("Type client's name here. Ex: ExampleFundPartnersLLC.", "ExampleFundPartnersLLC")
        firstName = st.text_input("First name of the client or owner of fund. Ex: John", "John")
        lastName = st.text_input("Last name of the client or owner of fund. Ex: Jingleheimer", "Jingleheimer")

        if st.button("Create Customer"):
            customer_data = customers.makeCustomer(ClientName, firstName, lastName)
            if customer_data:
                customer_ID = customer_data["id"]
                st.write(customer_ID)

        customerId = st.text_input("input the customer Id")
        if st.button("Generate Connect Link"):
            connect_link_data = customers.generateConnectLink(customerId, auth.auth["prod"]["pId"])
            st.write(connect_link_data)
        else:
            st.write("Please input the customer Id.")

        if st.button("Display All Customers"):
            
            connect_link_data = customers.getcustomers()
            print(connect_link_data)
            customers = []
            query = f"""
            SELECT CUSTOMER_ID
            FROM TESTINGAI.USER_LOGS.USER_TABLE_MAPPING
            WHERE USER_ID = '{user_role}';
            """
            allowed_cust = database.run_query(query)
            allowed_customers = allowed_cust['CUSTOMER_ID'].tolist()
            print(allowed_customers)
            if user_role == "FINICITYTTUS":
                st.dataframe(allowed_customers)
            else:
                for i in connect_link_data:
                    if i["id"] in allowed_customers:
                        customers.append(i)

            st.dataframe(customers)

        if st.button("Get Customer Accounts"):
            connect_link_data = customers.getCustomerAccounts(customerId)
            organizedAccounts = customers.filter_and_organize_data(connect_link_data)
            df = pd.DataFrame(organizedAccounts)
            st.dataframe(df)

    if taskbar == "Accounts":
        query = f"""
        SELECT CUSTOMER_ID
        FROM TESTINGAI.USER_LOGS.USER_TABLE_MAPPING
        WHERE USER_ID = '{user_role}';
        """
        allowed_customers = database.run_query(query)
        allowed_customers_list = allowed_customers['CUSTOMER_ID'].tolist()
        
        for customer_id in allowed_customers_list:
            if st.button(f"Get Positions for {customer_id}"):
                try:
                    # Fetch accounts for the specific customer
                    customer_accounts = accounts.getCustomerAccounts(customer_id)
                    print(customer_accounts)
                    # Process the account data
                    positions_df, accounts_df = accounts.process_account_positions(customer_accounts)
                    
                    # Create Excel file
                    excel_data = accounts.export_to_excel(positions_df, accounts_df, customer_id)
                    
                    # Download button for Excel file
                    st.download_button(
                        label=f"Download Full Position Data for {customer_id}",
                        data=excel_data,
                        file_name=f"{customer_id}_full_positions.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    # Display preview of positions
                    st.write("Positions Preview:")
                    st.dataframe(positions_df)
                    
                    # Display preview of accounts
                    st.write("Accounts Preview:")
                    st.dataframe(accounts_df)
                    
                except Exception as e:
                    st.error(f"Error processing data for customer {customer_id}: {e}")
                    import traceback
                    st.error(traceback.format_exc())

if __name__ == "__main__":
    main()