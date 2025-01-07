import streamlit as st
import pandas as pd
import requests
import json
import sys
sys.path.append('/workspaces/StreamFinicity1')
from utils.auth import get_token, auth
import re


def generateConnectLink(customerID,partnerId):
    token = get_token()
    st.write(token)
    st.write(customerID)
    body = {
        "partnerId": partnerId,
        "customerId": customerID,
        "redirectUri": "https://www.finicity.com/connect/",
        "webhookContentType": "application/json",
        "webhookData": {},
        "webhookHeaders": {},
        "singleUseUrl": True,
        "institutionSettings": {},
        "fromDate": 1059756050,
        "experience" : "ae1b8ef6-9bf3-43f1-bbca-c15f2b82dbca",
        "reportCustomFields": [
            {
                "label": "loanID",
                "value": "123456",
                "shown": True
            }
        ]
    }
    response = requests.post(url = f"{auth['url']}/connect/v2/generate", headers=auth['headers'], json=body)
    json_data = response.json()
    st.write(json_data)
    link = json_data["link"]
    return link

def makeCustomer(ClientName, firstName, lastName):
    body = {
            "username": ClientName,
            "firstName": firstName,
            "lastName": lastName,
            "phone": "404-233-5275",
            "email": f"{ClientName}@tridenttrust.com",
            "applicationId" : '8407cf1e-b044-486f-a2bb-ed78cbfe4f16'
            }
    token = get_token()
    auth['headers']['Finicity-App-Token'] = token
    response = requests.post(url=f"{auth['url']}/aggregation/v2/customers/active", json=body, headers=auth['headers'])
    if 200 <= response.status_code < 300:
        data = response.json()
        st.write(data)
        return data
    elif 400 <= response.status_code < 408:
        st.write(f"an error occurred: {response.status_code}")
    elif response.status_code ==409:
        st.write(f"Customer already exists!")
    elif 410 <= response.status_code <= 600:
        st.write(f"an error occurred: {response.status_code}")

def getcustomers():

    params = {
        "type" : "active",
        "start" : 1,
        "limit" : 1000
    }
    token = get_token()
    auth['headers']['Finicity-App-Token'] = token
    response = requests.get(url = f"{auth['url']}/aggregation/v1/customers", headers=auth['headers'], params=params)
    data = response.json()
    return data['customers']

def getCustomerAccounts(customerId):
    token = get_token()
    auth['headers']['Finicity-App-Token'] = token
    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts", headers = auth['headers'])
    data = response.json()
    accounts = data['accounts']
    for account in accounts:
        if 'detail' in account and account['detail']:
            formatted_detail = {}
            for key, value in account['detail'].items():
                
                formatted_key = ' '.join(word.capitalize() for word in re.findall('[A-Z]?[a-z]+', key))
                formatted_detail[formatted_key] = value
            account['detail'] = formatted_detail
    return accounts

def filter_and_organize_data(data):
    filtered_data = []
    for item in data:
        filtered_item = {
            "id": item["id"],
            "number": item["number"],
            "accountNumberDisplay": item["accountNumberDisplay"],
            "name": item["name"],
            "type": item["type"],
            "institutionId": item["institutionId"]
        }
        filtered_data.append(filtered_item)
    print(filtered_data)
    return filtered_data


def refreshCustomerAccounts(customerId):
    token = get_token()
    auth['headers']['Finicity-App-Token'] = token
    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts",headers = auth['headers'])

print(refreshCustomerAccounts(7030895347))