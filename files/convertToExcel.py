import streamlit as st
import snowflake.connector
import pandas as pd
import io
import utils.database

def TransToExcel(input, name):
    transactions_df = pd.DataFrame(input)
    transactions_df = transactions_df.sort_values('Posting Date', ascending=False)
    
    buffer = io.BytesIO()
    transactions_df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="Download Transactions Report", 
        data=buffer, 
        file_name=f"{name}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.success("Transactions report generated!")

def TransToExcelREC(input, name):
    transactions_df = pd.DataFrame(input)
    # transactions_df = transactions_df.sort_values('Event Date', ascending=False)
    
    buffer = io.BytesIO()
    transactions_df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="Download Transactions Report Rec", 
        data=buffer, 
        file_name=f"{name}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.success("Transactions report generated!") 

def TransToExcelART(input, name):
    transactions_df = pd.DataFrame(input)
    # transactions_df = transactions_df.sort_values('Posting Date', ascending=False)
    
    buffer = io.BytesIO()
    transactions_df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="Download Transactions Report ART", 
        data=buffer, 
        file_name=f"{name}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.success("Transactions report generated!")
