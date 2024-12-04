import streamlit as st
import pandas as pd
import requests
import json
from utils.auth import get_token, auth
from utils.dateconverter import dateConverter
from utils.database import run_query, create_statements_table_if_not_exists
from datetime import datetime, timedelta, timezone
import os
import uuid
import time

def store_file_in_snowflake(table_name, file_name, file_content, customer_id, account_id, portfolio, date):
    unique_id = str(uuid.uuid4())
    query = f"""
    INSERT INTO {table_name} (id, customer_id, account_id, portfolio, date, file_name, file_content)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (unique_id, customer_id, account_id, portfolio, date, file_name, file_content)
    run_query(query, params)

def get_index_and_month_day(end_time_str):
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S %Z")
    today = datetime.now(timezone.utc)
    
    # Calculate the difference in months
    index = (today.year - end_time.year) * 12 + today.month - end_time.month
    
    # Adjust for end-of-month logic
    if end_time.day < 28:  # Assuming statements are available on the last day of the month
        end_time = end_time.replace(day=1) - timedelta(days=1)
        index += 1
    
    month_day = end_time.strftime("%m_%d")
    return index, month_day

def getBankStatements(customerId, mapping_dict, end_time):
    get_token()
    if 'current_step' not in st.session_state:
        st.session_state['current_step'] = 0

    for i in range(st.session_state['current_step'], len(mapping_dict)):
        account = mapping_dict[i]
        accountId = account["ACCOUNT_ID"]
        portfolio = account["FUND_NAME"]
        last4 = account["ACCOUNTBANKLAST4"]
        
        index, month_day = get_index_and_month_day(end_time)
        file_name = f"{portfolio}_{month_day}_Account_{last4}.pdf"
        sanitized_portfolio = portfolio.replace(" ", "_")
        
        create_statements_table_if_not_exists(sanitized_portfolio)
        
        table_name = f"TESTINGAI.STATEMENTS.{sanitized_portfolio}_statements"
        
        query = f"SELECT file_content FROM {table_name} WHERE file_name = %s"
        result = run_query(query, (file_name,))
        
        print("File Name:", file_name)
        
        if result is None or result.empty:
            try:
                params = {
                    "index": str(index)
                }
                
                with st.spinner(f"Downloading statement for {portfolio}..."):
                    print(f"Calling API for customerId: {customerId}, accountId: {accountId}")
                    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts/{accountId}/statement", params=params, headers=auth['headers'], timeout=180)

                    if response.status_code == 200 and response.headers['Content-Type'] == 'application/pdf':
                        file_content = response.content
                        store_file_in_snowflake(table_name, file_name, file_content, customerId, accountId, portfolio, month_day)
                        st.session_state[file_name] = file_content
                        st.write(f"Bank statement saved as '{file_name}'")
                        st.download_button(
                            label=f"Download {os.path.basename(file_name)}",
                            data=file_content,
                            file_name=os.path.basename(file_name),
                            mime="application/pdf",
                            key=f"download-{file_name}-{i}"
                        )
                    else:
                        st.write("Failed to get bank statement or the content is not in PDF format.")
            except requests.exceptions.Timeout:
                st.write("Request timed out. Consider adjusting the timeout value or handling the exception.")
        
        else:
            file_content_bytes = bytes(result.iloc[0]['FILE_CONTENT'])

            st.session_state[file_name] = file_content_bytes
            st.write(f"Bank statement already exists as '{file_name}'")

            st.download_button(
                label=f"Download {os.path.basename(file_name)}",
                data=file_content_bytes,
                file_name=os.path.basename(file_name),
                mime="application/pdf",
                key=f"download-{file_name}-{i}"
            )
        
        st.session_state['current_step'] = i + 1
        time.sleep(5)

def display_download_buttons():
    for i, (file_name, file_content) in enumerate(st.session_state.items()):
        if isinstance(file_content, (bytes, bytearray)) and file_name.endswith(".pdf"):
            st.download_button(
                label=f"Download {os.path.basename(file_name)}",
                data=file_content,
                file_name=os.path.basename(file_name),
                mime="application/pdf",
                key=f"download-{file_name}-{i}"
            )