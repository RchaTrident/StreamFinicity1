import streamlit as st
import snowflake.connector
import pandas as pd
import datetime

def dateConverter(original_date_string):
    creationDate = datetime.datetime.fromtimestamp(int(original_date_string))
    formatted_date = creationDate.strftime('%m-%d-%Y')
    return formatted_date