import streamlit as st
import pandas as pd
import requests
import json
from utils.auth import get_token, auth


def getInstitutions(search):
    get_token()
    params = {
        "start": 1,
        "limit" : 1000,
        "search" : search
    }

    response = requests.get(url = f"{auth['url']}/institution/v2/institutions", headers=auth['headers'], params=params)
    data = response.json()
    return data