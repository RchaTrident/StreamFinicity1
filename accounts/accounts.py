import requests, json
import os
from utils.auth import get_token, auth
import re
import sys
sys.path.append('/workspaces/StreamFinicity1')


token = get_token()

def allAccounts():
    return "Please provide a customer ID to retrieve accounts."


def getAccountsByInstitutionId(institutionId):
    response = requests.post(url=f"{auth['url']}/aggregation/v1/customers/7024682666/institutionLogins/{institutionId}/accounts", headers=auth['headers'])
    json_data = json.loads(response.text)
    return json.dumps(json_data)
    
def getCustomerAccounts(customerId):
    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts", headers=auth['headers'])
    json_data = json.loads(response.text)
    return json.dumps(json_data)


