import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import uuid
import json
from utils import auth, database, dateconverter
import numpy as np
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
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        auth.login_page()
        return  
    if 'logged_in' in st.session_state:
        auth.get_token()

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
    user_role = st.session_state.get('user_role')
    if taskbar == "Reports":
        st.title("Reports")
        if user_role:
            allowed_tables = auth.user_roles[user_role]["tables"]
            print(f"Allowed tables for {user_role}: {allowed_tables}")
            query = "SHOW TABLES IN TESTINGAI.TESTINGAISCHEMA"
            table_names_df = database.run_query(query)

            if table_names_df is not None:
                table_names = table_names_df['name'].tolist()
                print(f"Retrieved table names: {table_names}")
                
                if "ALL" not in allowed_tables:
                    allowed_table_names = [table.split('.')[-1] for table in allowed_tables]
                    table_names = [table for table in table_names if table in allowed_table_names]
                    print(f"Filtered table names: {table_names}")
                
                if table_names:
                    fund_name = st.selectbox("Fund Name", table_names, index=st.session_state.get('fund_name_index', 0))
                    pretty_fund_name = prettify_name(fund_name)
                    st.write(f"You selected: {pretty_fund_name}")
                    
                    try:
                        query = f"SELECT * FROM {fund_name}" 
                        mapping_df = database.run_query(query)
                        mapping_dict = mapping_df.to_dict(orient='records')
                        if mapping_dict:
                            customer_id = mapping_dict[0]["CUSTOMER_ID"]
                            print(mapping_dict[0], "THE MAPPING DICT -------------------")
                            st.write('Records found!')
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
                    customerId = mapping_dict[0]["CUSTOMER_ID"]

                    if st.button("Generate Cashflows Report"):
                        # reset_session_state(['user_role', 'logged_in'])
                        # st.success("Session state reset except 'user_role' and 'logged_in'")
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
                            customers.refreshCustomerAccounts(customer_id)
                            statements.getBankStatements(customer_id, mapping_dict, end_time)
                        if "Transactions" in report_type:
                            customers.refreshCustomerAccounts(customer_id)
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
                                    convertToExcel.TransToExcelART(transactionsConv, fileName)

                        statements.display_download_buttons()
                else:
                    st.write("No tables found.")
            else:
                st.write("No tables found.")
        else:
            st.write("No role assigned.")
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
        # Conditional import for customer operations
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
            customers = []
            allowed_customers = auth.user_roles[user_role]["customers"]
            # arr = np.array(connect_link_data["customers"])
            arr = connect_link_data["customers"]
            if allowed_customers == "ALL":
                st.dataframe(arr)
            else:
                for i in arr:
                    if i["id"] in allowed_customers:
                        customers.append(i)

            # st.write(customers)

        if st.button("Get Customer Accounts"):
            connect_link_data = customers.getCustomerAccounts(customerId)
            print(connect_link_data, "THE LIIINKaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa DATA")
            organizedAccounts = customers.filter_and_organize_data(connect_link_data)
            df = pd.DataFrame(organizedAccounts)
            st.dataframe(df)

        

if __name__ == "__main__":
    main()