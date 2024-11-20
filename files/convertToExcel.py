import streamlit as st
import snowflake.connector
import pandas as pd
import io


def TransToExcel(input):
    transactions_df = pd.DataFrame(input)
    buffer = io.BytesIO()
    transactions_df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="Download Transactions Report",
        data=buffer,
        file_name="transactions_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    st.success("Transactions report generated!")
