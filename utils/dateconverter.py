import streamlit as st
import snowflake.connector
import pandas as pd
import datetime

def dateConverter(original_date_string):
    creationDate = datetime.datetime.fromtimestamp(int(original_date_string))
    formatted_date = creationDate.strftime('%m-%d-%Y')
    return formatted_date

def human_to_unix(human_time):
    dt_object = datetime.datetime.strptime(human_time, "%Y-%m-%d %H:%M:%S %Z")
    unix_timestamp = int(dt_object.timestamp())
    return unix_timestamp