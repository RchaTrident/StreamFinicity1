import streamlit as st
import hashlib
import requests
import json
from utils.auth import get_token, auth

def makeConsumer(customerId, fundName):
    body = {
            "firstName": "Consumer",
            "lastName": fundName,
            "address": "1100 Abernathy Road, NE",
            "city": "Marietta",
            "state": "GA",
            "zip": "30068",
            "phone": "404-233-5275",
            "ssn": "999-99-9999",
            "birthday": {
                "year": 1978,
                "month": 8,
                "dayOfMonth": 13
            },
            "email": "@tridenttrust.com",
            "suffix": "MBA",
            "endUser": {
                "address": "1100 Abernathy Road, NE",
                "city": "Marietta",
                "state": "GA",
                "zip": "30068",
                "phone": "404-233-5275",
                "email": "@tridenttrust.com",
                "url": "testurl.com"
            }
            }
    response = requests.post(url = f"{auth['url']}/decisioning/v1/customers/{customerId}/consumer", headers = auth['headers'], json=body)
    json_data = json.dumps(response.text)
    # print(json_data, "consumer data")
    return json_data

def getConsumer(customerId):
    token = get_token()
    auth['headers']['Finicity-App-Token'] = token
    response = requests.get(url = f"{auth['url']}/decisioning/v1/customers/{customerId}/consumer", headers = auth['headers'])
    json_data = json.loads(response.text)
    return response


def cashflowAna(customerId, userType,fromDate, accounts):
    token = get_token()
    auth['headers']['Finicity-App-Token'] = token
    body = {
            "accountIds": accounts,
            "analyticsReportData": {
                "forCraPurpose": False,
                "applicantIsPersonalGuarantor": False,
                "timeIntervalTypes": [
                "MONTHLY_CALENDAR"
                ]
            },
            "fromDate":fromDate

            }
    response= requests.post(url = f"{auth['url']}/decisioning/v2/customers/{customerId}/reports/cashflow-analytics/userTypes/{userType}", headers = auth['headers'], json=body, )
    # print(response)
    json_data = json.dumps(response.text)
    return json_data


def cashflowGenAna(customerId, accounts):
    params = {
        "reference-number" : "abc123"
    }
    body = {
            "accountIds": [
                7051082112,
                7051082109
            ],
            "lengthOfReport": 730
            }

    response= requests.post(url = f"{auth['url']}/analytics/cashflow/v1/customer/{customerId}", headers=auth['headers'], params=params, json=body)
    json_data = json.dumps(response.text)
    return json_data
