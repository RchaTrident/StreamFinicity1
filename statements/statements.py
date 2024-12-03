import streamlit as st
import pandas as pd
import requests
import json
from utils.auth import get_token, auth
from utils.dateconverter import dateConverter
from utils.database import run_query, create_statements_table
from datetime import datetime
import os

def store_file_in_snowflake(table_name, file_name, file_content, customer_id, account_id, portfolio, date):
    query = f"""
    INSERT INTO {table_name} (id, customer_id, account_id, portfolio, date, file_name, file_content)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (file_name, customer_id, account_id, portfolio, date, file_name, file_content)
    run_query(query, params)

def getBankStatements(customerId, mapping_dict, end_time):
    get_token()
    for i in mapping_dict:
        accountId = i["ACCOUNT_ID"]
        portfolio = i["FUND_NAME"]
        last4 = i["ACCOUNTBANKLAST4"]
        month_day = end_time[5:10]
        file_name = f"{portfolio}_{month_day}_Account_{last4}.pdf"
        
        # Create the table for the fund if it doesn't exist
        create_statements_table(portfolio)

        table_name = f"TESTINGAI.TESTINGAISCHEMA.{portfolio}_statements"
        
        query = f"SELECT file_content FROM {table_name} WHERE file_name = %s"
        result = run_query(query, (file_name,))
        
        if result is None or result.empty:
            try:
                params = {
                    "index": "1"
                }
                
                with st.spinner(f"Downloading statement for {portfolio}..."):
                    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts/{accountId}/statement", params=params, headers=auth['headers'], timeout=180)

                    if response.status_code == 200 and response.headers['Content-Type'] == 'application/pdf':
                        file_content = response.content
                        store_file_in_snowflake(table_name, file_name, file_content, customerId, accountId, portfolio, month_day)
                        st.session_state[file_name] = file_content
                        st.write(f"Bank statement saved as '{file_name}'")
                    else:
                        st.write("Failed to get bank statement or the content is not in PDF format.")
            except requests.exceptions.Timeout:
                st.write("Request timed out. Consider adjusting the timeout value or handling the exception.")
        else:
            st.session_state[file_name] = result.iloc[0]['file_content']
            st.write(f"Bank statement already exists as '{file_name}'")

        st.download_button(
            label=f"Download {file_name}",
            data=st.session_state[file_name],
            file_name=file_name,
            mime="application/pdf"
        )

for file_name, file_content in st.session_state.items():
    if file_name.endswith(".pdf"):
        st.download_button(
            label=f"Download {os.path.basename(file_name)}",
            data=file_content,
            file_name=os.path.basename(file_name),
            mime="application/pdf"
        )