import streamlit as st
import pandas as pd
import requests
import json
from utils.auth import get_token, auth
from utils.dateconverter import dateConverter



final = []
@st.cache_data
def getCustomerTrans(customerId, fromDate, toDate):
    get_token()
    params = {
        "fromDate": fromDate,
        "toDate": toDate,
        "limit": 1000,
        "includePending": True
    }
    response = requests.get(url=f"{auth['url']}/aggregation/v3/customers/{customerId}/transactions", headers=auth['headers'], params=params)
    st.write(f"{auth['url']}/aggregation/v3/customers/{customerId}/transactions")
    print(response)
    json_data = json.loads(response.text)
    print(json_data, "jSON DATA")
    return json_data


def convertTransAllvue(arr, mapping_dict):
    if len(arr) > 0:
        keys_to_keep = {'amount', 'accountId', 'description', 'memo', 'transactionDate'}
        for index, j in enumerate(arr):
            if len(arr) == 0:
                st.write("there are no transactions this timespan")
                return
            i = j.copy()
    
            categorization = i.pop("categorization")
            i.update(categorization)

            res = {p: i[p] for p in i if p in keys_to_keep}

            skip_values = ["Sweep Repo Interest", "SWEEP TO TREAS REPO I", "Sweep Repo Maturity"]
            if 'memo' in res and res['memo'] in skip_values:
                continue
            docNo = "000000"
            newNo = str(int(docNo) + index + 1).zfill(len(docNo))
            TableDict = {}
            
            for i in mapping_dict:
                # st.write("this is the ACCOUNT_ID",i["ACCOUNT_ID"], "and this is the res account_id", str(res["accountId"]))
                if i["ACCOUNT_ID"] == str(res["accountId"]):
                    TableDict = i
                    # st.write(TableDict, "THE TABLE DICT")

            res['Amount'] = res['amount']
            res["Amount (CCY)"] = res['amount']
            res["Amount (BCY)"] = res['amount']
            res['Amount (LCY)'] = res.pop('amount')
            res['Company Type'] = 'Fund'
            res["Security Description"] = ''
            res["Lot No."] = ''
            res["Due from gp Code"] = ''
            res["Due to master Code"] = ''
            res["SCY Code"] = ''
            res["BCY Code"] = ''
            res["ACY Code"] = ''
            aid = str(res["accountId"])
            # st.write("this is the tabler dict, " ,TableDict)
            accountCompanyCode = TableDict["ACCOUNTCOMPANYCODE"]
            BankNumber = TableDict["BANKNUMBER"]
            FundName = TableDict["FUND_NAME"]
            
            res['Company Code'] = accountCompanyCode

            res['Posting Date'] = dateConverter(str(res['transactionDate']))
            res['Document Date'] = dateConverter(str(res.pop('transactionDate')))
            # res['ActualSettleDate'] = dateConverter(str(res.pop('postedDate')))
            res['Document Type'] = ''
            res['Document No.'] = f'{res["Company Code"]}_Q2_{newNo}'
            res['External Document No.'] = ''
            res['Account Type'] = 'G/L Account'
            
            
            res['Bal. Account No.'] = BankNumber
            #name of the type of transaction
            # res['Account No.'] = accountBankLast4[FundName][aid]
            res['Account No.'] = '[INSERT GL/ACCOUNT HERE]'
            res.pop("accountId")
            #the code of the account
            # res['Account Name'] = fundStructure[FundName][aid]
            res['Account Name'] = ''
            description = res.pop('description', '')
            limited_desc = description[:250]
            res['Description'] = limited_desc
            res['Security No.'] = ''
            res['Amounts Relation Type'] = 'Exchange Rate'
            res['Quantity'] = ''
            res['Currency Code'] = 'USD'
            res['Exchange Rate Amount'] = '1.00'
            res['Relational Exch. Rate Amount'] = '1.00'
            res['Amount (SCY)'] = '0'
            res['CCY Code'] = 'USD'
            res['Exchange Rate Amount1'] = '1.00'
            res['Relational Exch. Rate Amount1'] = '1.00'
            res['Exchange Rate Amount2'] = ''
            res['Relational Exch. Rate Amount2'] = ''
            res['Exchange Rate Amount3'] = ''
            res['Relational Exch. Rate Amount3'] = ''
            res['Exchange Rate Amount4'] = ''
            res['Relational Exch. Rate Amount4'] = ''
            res['Amount (ACY)'] = '0.00'
            res['Bal. Account Type'] = 'Bank Account'
            
            res['Allocation Rule Code'] = 'INSERT ALLOCATION RULE HERE'
            res['Allocation Rule Description'] = ''
            res['Deal Code'] = ''
            res['Deal Description'] = ''
            memo = res.pop('memo', '')
            limited_memo = memo[:250]
            if 'memo' in res:
                res['Comment'] =limited_memo
            else: 
                res["Comment"] = ""
            res['Business Unit Code'] = ''
            final.append(res)
    # st.write(json.dumps(final), "the final result")
    else:
        st.write("no transactions this period")
        exit()
    # st.write(final[:50], "this is final")
    return final
#ForGenevaREC
@st.cache_data
def convertTransREC(arr, mapping_dict):
    all_keys = set().union(*(d.keys() for d in arr))
    keys_to_keep = {'amount', 'type', 'accountId', 'description', 'memo', 'postedDate', 'transactionDate', 'createdDate'}


    for j in arr:
        if len(arr) == 0:
            print("there are no transactions this timespan")
            exit()
        i = j.copy()
        categorization = i.pop("categorization")
        i.update(categorization)
        res = {p: i[p] for p in i if p in keys_to_keep}
        TableDict = {}
        # st.write( mapping_dict, "the mapping dict")
        
        for i in mapping_dict:
            if i["ACCOUNT_ID"] == str(res["accountId"]):
                TableDict = i
        if 'type' in res:
            if res['type'] == "debit":
                res['RecordType'] = 'Withdrawal'
            elif res['type'] == "credit":
                res['RecordType'] = 'Deposit'
            elif res['type'] == 'cash':
                res['RecordType'] = 'Withdrawal'
            elif res['type'] == 'atm':
                res['RecordType'] = 'Deposit'
            elif res['type'] == 'check':
                res['RecordType'] = 'Deposit'
            elif res['type'] == 'deposit':
                res['RecordType'] = 'Deposit'
            elif res['type'] == 'directDebit':
                res['RecordType'] = 'Sell'
            elif res['type'] == 'directDeposit':
                res['RecordType'] = 'Deposit'
            elif res['type'] == 'dividend':
                res['RecordType'] = 'Dividend'
            elif res['type'] == 'fee':
                res['TradeExpenses.ExpenseAmt'] = abs(res['amount'])
            elif res['type'] == 'interest':
                res['RecordType'] = 'Interest'
            elif res['type'] == 'other':
                res['RecordType'] = '-'
            elif res['type'] == 'payment':
                res['RecordType'] = 'Withdrawal'
            elif res['type'] == 'pointOfSale':
                res['RecordType'] = 'Deposit'
            elif res['type'] == 'repeatPayment':
                res['RecordType'] = 'Repeat'
            elif res['type'] == 'serviceCharge':
                res['TradeExpenses.ExpenseAmt'] = abs(res['amount'])
            elif res['type'] == 'transfer':
                res['RecordType'] = 'Withdrawal'
        else:
            if res['amount'] < 0:
                res['RecordType'] = 'Sell'
            elif res['amount'] > 0:
                res['RecordType'] = 'Buy'
        res['NetInvestmentAmount'] = abs(res['amount'])
        if 'type' in res and res['type'] not in ('serviceCharge', 'fee'):
            res["Quantity"] = abs(res.pop('amount'))
        else:
            res["Quantity"] = 0
        res['RecordAction'] = 'InsertUpdate'
        res['KeyValue'] = 'NULL'
        accnt2 = res['accountId']
        res['Portfolio'] = TableDict["FUND_NAME"]
        res['FundStructure'] = TableDict["FUNDSTRUCTURE"]
        res['Strategy'] = "Undefined"
        res['EventDate'] = dateConverter(str(res['transactionDate']))
        res['SettleDate'] = dateConverter(str(res.pop('transactionDate')))
        res['ActualSettleDate'] = dateConverter(str(res.pop('postedDate')))
        res['BrokerName'] = 'UND'
        res['LocationAccount'] = TableDict["FUNDCODES"]
        res['Investment'] = 'USD'
        res['CounterInvestment'] = 'USD'  
        res['TradeExpenses.ExpenseNumber'] = 1.00
        res['TradeExpenses.ExpenseCode'] = 'Miscellaneous' 
        res['TotCommission'] = 0 
        res['NetCounterAmount'] = res['NetInvestmentAmount']
        res['tradeFX'] = 1
        res['PriceDenomination'] = 'USD'
        res['CounterFXDenomination'] = 'USD'
        res['Price'] = 1
        res.pop('accountId')
        res.pop('description')
        res["TradeExpenses.ExpenseAmt"] = 0
        if 'memo' in res:
            res.pop('memo')
        if 'type' in res:
            res.pop('type')
        final.append(res)
    # print(json.dumps(final), "the final result")
    return final

def convertTransART(arr, mapping_dict):
    grouped_data = []
    for item in arr:
        item['RecordAction'] = 'InsertUpdate'
        item['KeyValue'] = 'NULL'
        accnt2 = item['accountId']

        item['EventDate'] = dateConverter(str(item['transactionDate']))
        item['Portfolio'] =  mapping_dict["ACCOUNTCOMPANYCODE"]
        item['SettleDate'] =  dateConverter(str(item.pop('transactionDate')))
        item['ActualSettleDate'] =  dateConverter(str(item.pop('postedDate')))
        item['Investment'] = 'USD'
        item['LocationAccount'] =  mapping_dict["FUND_NAME"]
        item['FundStructure'] =  mapping_dict["FUND_NAME"]

        if item["amount"] > 0:
            item["AdjLines.DebitAmount"] = 0
            item["AdjLines.CreditAmount"] = abs(item["amount"])
        if item["amount"] < 0:
            item["AdjLines.CreditAmount"] = 0
            item["AdjLines.DebitAmount"] = abs(item["amount"])
        
        item['Strategy'] = "Undefined"
        item['CounterInvestment'] = 'USD'
        itemCategory = item["categorization"]["category"]
        memo = None
        if "memo" in item:
            memo = item["memo"]
        item["AdjLines.FinAcctCode"] = f"{itemCategory}_{memo}"
        item["AdjLines.TaxLotType"] = "UseDefault"
        item["AdjLines.LineNumber"] = 1

        item2 = item.copy()
        item2['RecordAction'] = 'InsertUpdate'
        item2['KeyValue'] = 'NULL'
        item2["AdjLines.LineNumber"] = 2
        item2['EventDate'] = None
        item2['Portfolio'] =  None
        item2['SettleDate'] =  None
        item2['ActualSettleDate'] =  None
        item2['Investment'] = None
        item2['LocationAccount'] = None
        item2['FundStructure'] =  None
        item2['Strategy'] = None
        item2['CounterInvestment'] = 'USD'
        itemCategory = item2["categorization"]["category"]
        memo = None
        if "memo" in item:
            memo = item["memo"]
        item2["AdjLines.FinAcctCode"] = f"{itemCategory}_{memo}"
        item2["AdjLines.TaxLotType"] = "UseDefault"
        item2["AdjLines.LineNumber"] = 1

        if item["amount"] > 0:
            item2["AdjLines.DebitAmount"] = abs(item2["amount"])
            item2["AdjLines.CreditAmount"] = 0
        if item["amount"] < 0:
            item2["AdjLines.CreditAmount"] = abs(item2["amount"])
            item2["AdjLines.DebitAmount"] = 0
        item.pop("id")
        item.pop("customerId")
        item.pop("status")
        item.pop("description")
        if "type" in item:
            item.pop("type")
        
        item.pop("createdDate")
        item.pop("categorization")
        item.pop("amount")
        item.pop("accountId")
        if "memo" in item:
            item.pop("memo")

        item2.pop("id")
        item2.pop("customerId")
        item2.pop("status")
        item2.pop("description")

        item2.pop("createdDate")
        item2.pop("categorization")
        item2.pop("amount")
        item2.pop("accountId")

        
        grouped_data.append(item)
        grouped_data.append(item2)
    
    df = pd.json_normalize(grouped_data)
    print(grouped_data)
