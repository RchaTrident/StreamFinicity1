import streamlit as st
import stylings
st.set_page_config(
    page_title="Fintech Dashboard",
    page_icon="tridentlogo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
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

center_column = st.columns([30, 40, 30])  # This creates columns of 30%, 40%, 30% of the viewport
with center_column[1]:  # Using the middle 40% column
    st.image("tridentlogo.png", use_column_width=True)


hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

def main():
    stylings.init_styling()
    conn = get_snowflake_connection()
    user_role = st.session_state.get('user_role')
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        auth.login_page()
        return  
    if 'logged_in' in st.session_state:
        
        auth.get_token()

    taskbar = st.sidebar.radio(
        "Navigation",
        ("Reports", "Institutions", "Customers", "Accounts", "Issue? Report it here"),
        index=st.session_state.get('taskbar_index', 0)
    )
    # print("--------------------------------------------------------")
    print("Current session state login status:", st.session_state["user_role"], st.session_state["logged_in"])
    # if st.button("Reset Session State"):
    #     reset_session_state(['user_role', 'logged_in'])
    #     st.success("Session state reset except 'user_role' and 'logged_in'")
    if st.sidebar.button("Logout"):
        auth.logout()
    st.sidebar.write(f"Logged in as: {user_role}")

    if taskbar == "Reports":
        left_col, main_col, right_col = st.columns([1, 3, 1])
        with main_col:
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
                    database.log_user_login(user_role, statements="Generated")
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
                        database.log_user_login(user_role, transactions="Allvue")
                    if "Geneva" in database1:
                        if "REC" in gen_report_type:
                            transactionsConv = GetTransactions.convertTransREC(transactions, mapping_dict)  
                            convertToExcel.TransToExcel(transactionsConv, fileName)
                            database.log_user_login(user_role, transactions="Geneva Rec") 
                        if "ART" in gen_report_type:
                            transactionsConv = GetTransactions.convertTransART(transactions, mapping_dict)  
                            convertToExcel.TransToExcelART(transactionsConv, fileName)
                            database.log_user_login(user_role, transactions="Geneva ART")

                statements.display_download_buttons()
    
    if taskbar == "Institutions":
        left_col, main_col, right_col = st.columns([1, 3, 1])
        with main_col:
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
        left_col, main_col, right_col = st.columns([1, 3, 1])
        with main_col:
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
                customerEditMap = {
                    "7026859829" : "Comerica",
                    "7029249040": "Phorcys",
                    "7029496551": "TIOGA",
                    "7029508303": "MVP"
                }
                connect_link_data = [
                        {
                            "id": i["id"],
                            "username": customerEditMap[i["id"]] if i["id"] in customerEditMap else i["username"],
                            "createdDate": i["createdDate"],
                            "type": i["type"]
                        }
                        for i in customers.getcustomers()
                    ]

                customers = []
                query = f"""
                SELECT CUSTOMER_ID
                FROM TESTINGAI.USER_LOGS.USER_TABLE_MAPPING
                WHERE USER_ID = '{user_role}';
                """
                allowed_cust = database.run_query(query)
                allowed_customers = allowed_cust['CUSTOMER_ID'].tolist()
                
                if user_role in auth.admins:
                    st.dataframe(connect_link_data)
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
        left_col, main_col, right_col = st.columns([1, 3, 1])
        with main_col:
            query = f"""
            SELECT CUSTOMER_ID
            FROM TESTINGAI.USER_LOGS.USER_TABLE_MAPPING
            WHERE USER_ID = '{user_role}';
            """
            if user_role in auth.admins:
                allowed_customers = accounts.allAccounts()
                st.write(allowed_customers)
            else:
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

    if taskbar == "AI (Coming soon!)":
        left_col, main_col, right_col = st.columns([1, 3, 1])
        with main_col:
            st.write("""
                        # Proposed AI models:
                        RNN: Designed for processing sequential data. Good for series forecasting
                        
                        LSTM: a larger version of RNN, used for longer time periods (longer than 2 years)
                        
                        Llama: Facebook produced AI, good all purpose open source with ample support. a GPT style model though, would require more resources.
                        
                        # Step 1: Prepare Your Model
                        Save Your Model: Ensure your model is saved in a format that Snowflake supports, such as a serialized file (e.g., .pkl for Python models).
                        
                        # Step 2: Upload Your Model to Snowflake
                        Create a Stage: A stage is a location in Snowflake where you can store files.
                        CREATE OR REPLACE STAGE my_stage;
                        Upload Your Model File: Use the SnowSQL command-line tool or the Snowflake web interface to upload your model file to the stage.

                        snowsql -q "PUT file://path_to_your_model_file @my_stage";
                        
                        # Step 3: Register Your Model
                        Create a Table to Store the Model:

                        CREATE OR REPLACE TABLE my_models (
                            model_name STRING,
                            model VARIANT
                        );
                        Insert Your Model into the Table:

                        INSERT INTO my_models (model_name, model)
                        SELECT 'my_model', PARSE_JSON($1)
                        FROM @my_stage/your_model_file;
                        
                        # Step 4: Use Your Model
                        Load Your Model: Use Snowflake's Python integration (Snowpark) to load and use your model.
                        import snowflake.snowpark as snowpark
                        import pickle

                        # instructions:
                        ## Create a Snowpark session
                        session = snowpark.Session.builder.configs(your_config).create()

                        ## Load the model from the table
                        model_row = session.table("my_models").filter("model_name = 'my_model'").collect()[0]
                        model = pickle.loads(model_row['model'])

                        ## Use the model for predictions
                        predictions = model.predict(your_data)
                        Additional Resources
                        Snowflake Documentation: Detailed guides on using stages and Snowpark12.
                        Snowflake Cortex: Explore advanced AI features and integrations1.
                        """)  
            body = st.text_input("Thoughts? write them here")
            login_date = datetime.now().date()
            login_time = (datetime.now() - timedelta(hours=5)).time()
            query = f"""
            INSERT INTO TESTINGAI.SUPPORT.AI (USER_ROLE, POSTED_DATE, POSTED_TIME,
            BODY) 
            VALUES (%s, %s, %s, %s)
            """
            params = (user_role, login_date, login_time, body)
            if st.button("Submit"):
                database.run_query(query, params)
                st.success("Data inserted successfully!")


    if taskbar == "Issue? Report it here":
        left_col, main_col, right_col = st.columns([1, 3, 1])
        with main_col:
            if user_role in auth.admins:
                login_date = datetime.now().date()
                login_time = (datetime.now() - timedelta(hours=5)).time()
                
                tab1, tab2, tab3 = st.tabs(["Support Tickets", "User Logs", "AI Feedback"])
                
                with tab1:
                    query_general = """
                    SELECT USER_ROLE, POSTED_DATE, POSTED_TIME, BODY
                    FROM TESTINGAI.SUPPORT.GENERAL
                    """
                    result_general = database.run_query(query_general)
                    
                    if result_general is not None and not result_general.empty:
                        st.write("Data from TESTINGAI.SUPPORT.GENERAL:")
                        st.write(result_general)
                    else:
                        st.warning("No data found in TESTINGAI.SUPPORT.GENERAL.")

                with tab2:
                    # List of all user log tables
                    user_tables = [
                        "TRIDENT_CHELSEA", "TRIDENT_GREG_M", "TRIDENT_LEE", "TRIDENT_MARY_GRACE",
                        "TRIDENT_NATHAN", "TRIDENT_TAYLOR", "TRIDENT_TITUS", "FINICITYTTUS",
                        "ADMIN_BRIAN", "ADMIN_BILL"
                    ]
                    
                    view_option = st.radio("Select View", ["Combined Logs", "Individual User Logs"])
                    
                    if view_option == "Combined Logs":
                        # Create a UNION ALL query for all tables
                        union_queries = []
                        for table in user_tables:
                            union_queries.append(f"""
                                SELECT '{table}' as SOURCE_TABLE, *
                                FROM TESTINGAI.USER_LOGS.{table}
                            """)
                        
                        combined_query = " UNION ALL ".join(union_queries)
                        combined_query += " ORDER BY LOGIN_DATE DESC, LOGIN_TIME DESC"
                        
                        result_logs = database.run_query(combined_query)
                        
                        if result_logs is not None and not result_logs.empty:
                            st.write("Combined User Logs:")
                            st.dataframe(result_logs, use_container_width=True)
                            
                            # Add download button for combined logs
                            csv = result_logs.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "Download Combined Logs",
                                csv,
                                "combined_user_logs.csv",
                                "text/csv"
                            )
                        else:
                            st.warning("No log data found.")
                            
                    else:  # Individual User Logs
                        for table in user_tables:
                            st.write(f"### {table.replace('_', ' ')} Logs")
                            query = f"""
                            SELECT *
                            FROM TESTINGAI.USER_LOGS.{table}
                            ORDER BY LOGIN_DATE DESC, LOGIN_TIME DESC
                            """
                            result = database.run_query(query)
                            
                            if result is not None and not result.empty:
                                st.dataframe(result, use_container_width=True)
                                
                                # Add download button for each user's logs
                                csv = result.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    f"Download {table} Logs",
                                    csv,
                                    f"{table}_logs.csv",
                                    "text/csv",
                                    key=f'download_{table}'
                                )
                            else:
                                st.warning(f"No data found for {table}")
                            st.divider()

                with tab3:
                    query_ai = """
                    SELECT USER_ROLE, POSTED_DATE, POSTED_TIME, BODY
                    FROM TESTINGAI.SUPPORT.AI
                    """
                    result_ai = database.run_query(query_ai)
                    
                    if result_ai is not None and not result_ai.empty:
                        st.write("Data from TESTINGAI.SUPPORT.AI:")
                        st.write(result_ai)
                    else:
                        st.warning("No data found in TESTINGAI.SUPPORT.AI.")

            else:
                body = st.text_input("Please enter problems or feedback here")
                login_date = datetime.now().date()
                login_time = (datetime.now() - timedelta(hours=5)).time()
                query = """
                INSERT INTO TESTINGAI.SUPPORT.GENERAL (USER_ROLE, POSTED_DATE, POSTED_TIME, BODY)
                VALUES (%s, %s, %s, %s)
                """
                params = (user_role, login_date, login_time, body)
                if body:
                    result = database.run_query(query, params)
                    if result is not None:
                        st.success("Data inserted successfully!")
                    else:
                        st.error("Failed to insert data.")
                else:
                    st.warning("Please enter your thoughts before submitting.")
                

            

if __name__ == "__main__":
    main()