import requests, json
import os
from utils.auth import get_token, auth
import re
import sys
sys.path.append('/workspaces/StreamFinicity1')
import pandas as pd
import json
import io
from datetime import datetime
from collections import Counter

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

#we use the simple to get the status code of which particular accounts are failing
def getCustomerAccountSimple(customerId):
    response = requests.get(url=f"{auth['url']}/aggregation/v1/customers/{customerId}/accounts/simple", headers=auth['headers'])
    json_data = json.loads(response.text)
    accounts = json_data.get('accounts', [])
    column_mapping = {
        'aggregationStatusCode': 'Aggregation',
        'customerId': 'CustomerId',
        'institutionId': 'InstitutionId',
        'aggregationSuccessDate': 'Aggregated Success Date',
        'aggregationAttemptDate': 'Aggregated Attempt Date',
        'createdDate': 'Account Creation Date',
        'linkedAccountDate': 'Account First Link',
        'institutionLoginId': 'InstitutionLoginId',
        'accountNumberDisplay': 'Bank Last 4',
        'name': 'Name',
        'status': 'Status'
    }
    
    df = pd.DataFrame(accounts)
    available_columns = [col for col in column_mapping.keys() if col in df.columns]
    df = df[available_columns]
    
    rename_mapping = {k: column_mapping[k] for k in available_columns}
    df = df.rename(columns=rename_mapping)
    
    date_columns = [
        'Aggregated Success Date', 
        'Aggregated Attempt Date', 
        'Account Creation Date', 
        'Account First Link'
    ]
    
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: datetime.fromtimestamp(x).strftime('%d %b %Y %H:%M:%S') if pd.notnull(x) and x else ''
            )
    
    if 'Aggregation' in df.columns:
        status_counts = Counter(df['Aggregation'])
        status_counters = {f"{code}Counter": count for code, count in status_counts.items() if code != 0}
        
        for code, count in status_counters.items():
            df[code] = count
    
    return df

def process_account_positions(customer_accounts):
    """
    Process the full account and position data into a structured format for Excel export
    
    Args:
        customer_accounts (str): JSON string containing account and position data
    
    Returns:
        tuple: (positions_df, accounts_df) containing processed DataFrames
    """
    try:
        # Parse the JSON data
        accounts_data = json.loads(customer_accounts)
        
        # Lists to store position and account data
        all_positions = []
        account_details = []
        
        for account in accounts_data.get('accounts', []):
            # Store account-level information
            account_info = {
                'account_id': account.get('id'),
                'account_number': account.get('number'),
                'account_name': account.get('name'),
                'account_balance': account.get('balance'),
                'account_type': account.get('type'),
                'currency': account.get('currency'),
                'status': account.get('status')
            }
            
            # Process each position in the account
            for position in account.get('position', []):
                position_data = {
                    'account_id': account.get('id'),  # Link back to account
                    'symbol': position.get('symbol'),
                    'cusip': position.get('cusipNo'),
                    'security_name': position.get('securityName'),
                    'security_type': position.get('securityType'),
                    'hold_type': position.get('holdType'),
                    'units': position.get('units'),
                    'average_cost': position.get('averageCost'),
                    'current_price': position.get('currentPrice'),
                    'market_value': position.get('marketValue'),
                    'position_type': position.get('posType'),
                    'status': position.get('status'),
                    'face_value': position.get('faceValue'),
                    'rate': position.get('rate'),
                    'expiration_date': position.get('expirationDate'),
                    'current_price_date': position.get('currentPriceDate'),
                    'description': position.get('description')
                }
                all_positions.append(position_data)
            
            account_details.append(account_info)
        
        # Create DataFrames
        positions_df = pd.DataFrame(all_positions)
        accounts_df = pd.DataFrame(account_details)
        
        return positions_df, accounts_df
        
    except Exception as e:
        raise Exception(f"Error processing account data: {str(e)}")

def export_to_excel(positions_df, accounts_df, customer_id):
    """
    Export position and account data to an Excel file with multiple sheets
    
    Args:
        positions_df (DataFrame): Positions data
        accounts_df (DataFrame): Account data
        customer_id (str): Customer identifier
    
    Returns:
        bytes: Excel file content as bytes
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        positions_df.to_excel(writer, sheet_name='Positions', index=False)
        accounts_df.to_excel(writer, sheet_name='Accounts', index=False)
    
    return output.getvalue()
