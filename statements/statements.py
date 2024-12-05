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
import streamlit as st
import pandas as pd
import base64


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

    # Check if the given date is the last day of the month
    next_month = end_time.replace(day=28) + timedelta(days=4)  # this will always get to the next month
    last_day_of_month = next_month - timedelta(days=next_month.day)

    if end_time != last_day_of_month:
        # If not the last day of the month, set to the last day of the previous month
        end_time = end_time.replace(day=1) - timedelta(days=1)

    index = (today.year - end_time.year) * 12 + today.month - end_time.month
    month_day = end_time.strftime("%m_%d")
    return index, month_day

def sanitize_portfolio(portfolio):
    # Replace spaces with underscores and & with _and_
    sanitized_portfolio = portfolio.replace(" ", "_").replace("&", "_and_")
    return sanitized_portfolio

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
        sanitized_portfolio = sanitize_portfolio(portfolio)
        
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
                    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts/{accountId}/statement", params=params, headers=auth['headers'], timeout=360)
                    if response.status_code == 200 and response.headers['Content-Type'] == 'application/pdf':
                        file_content = response.content
                        store_file_in_snowflake(table_name, file_name, file_content, customerId, accountId, portfolio, month_day)
                        st.session_state[file_name] = file_content
                        st.write(f"Bank statement saved as '{file_name}'")
                    else:
                        st.write("Failed to get bank statement or the content is not in PDF format.")
                        print(response.status_code, "the response code", response, "the actual response")
            except requests.exceptions.Timeout:
                st.write("Request timed out. Consider adjusting the timeout value or handling the exception.")
        
        else:
            file_content_bytes = bytes(result.iloc[0]['FILE_CONTENT'])

            st.session_state[file_name] = file_content_bytes
            st.write(f"Bank statement already exists as '{file_name}'")
        
        st.session_state['current_step'] = i + 1
        time.sleep(5)

def display_download_buttons():
    data = []
    for i, (file_name, file_content) in enumerate(st.session_state.items()):
        if isinstance(file_content, (bytes, bytearray)) and file_name.endswith(".pdf"):
            b64 = base64.b64encode(file_content).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(file_name)}">Download {os.path.basename(file_name)}</a>'
            data.append({"File Name": file_name, "Download Link": href})

    if data:
        df = pd.DataFrame(data)
        st.write(df.to_html(escape=False), unsafe_allow_html=True)