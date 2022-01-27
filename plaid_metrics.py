
# Import libraries
import os
import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import timedelta
import plotly.express as px
import matplotlib.pyplot as plt




# Initialize 'feedback' dict
feedback = {'credit': [], 'velocity': [], 'stability': [], 'diversity': []}

# Declare scoring grids as immutable np arrays
cred_mix = np.array([[0, 0.1, 0.3, 0.7],[0, 0.4, 0.7, 0.8],[0, 0.8, 0.9, 1]], dtype=float) 
profile_mix = np.array([[0, 0.4, 0.6, 0.7], [0.4, 0.8, 1, 1], [0.6, 1, 1, 1], [0.7, 1, 1, 1]], dtype=float)
cred_length = np.array([30, 90, 1800])                     #bins: 0-30 | 31-90 | 91-1800 | >1800
cred_count = np.array([0, 1, 2])                           #bins: 0 | 1 | 2 | >=3
cred_lively = np.array([5, 10, 15, 25])                    #bins: ...
prod_count = np.array([1, 3, 4, 6])  
cum_balance = np.array([5000, 10000, 30000, 75000]) 
grid_double = np.array([0, 0.125, 0.25, 0.50, 1]) 
grid_triple = np.array([0, 0.3, 0.6, 0.9, 1]) 


cred_mix.flags.writeable = False
cred_length.flags.writeable = False
cred_count.flags.writeable = False
cred_lively.flags.writeable = False
cum_balance.flags.writeable = False
profile_mix.flags.writeable=False
grid_double.flags.writeable = False



# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #

def dynamic_select(tx):
    """
    dynamically pick the best credit account,
    i.e. the account that performs best in 2 out of these 3 categories:
    highest credit limit / largest txn count / longest txn history
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                best (str): Plaid account_id of best credit account 
    """
    try:
        acc = tx['accounts']
        txn = tx['transactions']

        info = []
        for i in range(len(acc)):
            if 'credit' in acc[i]['type']:
                id = acc[i]['account_id']
                type = acc[i]['type']+' '+str(acc[i]['subtype'])+' '+str(acc[i]['official_name'])
                limit = acc[i]['balances']['limit']
                transat = [i for i in txn if i['account_id']==id]
                txn_count = len(transat)
                if len(transat)!=0:
                    length = (datetime.today().date() - datetime.strptime(transat[-1]['date'], '%Y-%m-%d').date()).days
                else:
                    length=0
                info.append([id, type, limit, txn_count, length])

        if len(info)!=0:
            best = info[0][0] #WIP # a = np.array(info).T # max(a[2])
        else:
            best = 'inexistent'
        return best

    except Exception as e:
        print('Error in dynamic_select()')

        




# -------------------------------------------------------------------------- #
#                               Metric #1 Credit                             #
# -------------------------------------------------------------------------- #     

def credit_mix(tx):
    """
    returns score based on composition and status of user's credits accounts

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): gained based on number of credit accounts owned and duration
    """
    try: 
        # How many credit products does the user own?
        acc = tx['accounts']
        credit_acc = []
        credit_ids = []
        for i in range(len(acc)):
            if 'credit' in acc[i]['type']:
                tup = (acc[i]['type'], acc[i]['subtype'], acc[i]['official_name'], acc[i]['account_id'])
                credit_acc.append(tup)
                credit_ids.append(acc[i]['account_id'])
                
        how_many = len(credit_acc)
        feedback['credit'].append('credit account(s) = '+str(how_many)) 
        if how_many==0:
            score = 0
        else:
            # How long has the user owned their credit products for?
            txn = tx['transactions']
            credit_txn = [i for i in txn if i['account_id'] in credit_ids]
            feedback['credit'].append('cumulative count credit txns= '+str(len(credit_txn)))

            oldest_credit_txn = datetime.strptime(credit_txn[-1]['date'], '%Y-%m-%d').date()
            date_today = datetime.today().date() 
            how_long = (date_today - oldest_credit_txn).days #date today - date of oldest credit transaction
            m = np.digitize(how_many, cred_count, right=True)
            n = np.digitize(how_long, cred_length, right=True)
            score = cred_mix[m][n]
        return score

    except Exception as e:
        print('Error in credit_mix()')




def credit_length(tx):
    """
    returns score based on length of user's best credit account
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): gained because of credit account duration
    """
    try:
        id = dynamic_select(tx)
        txn = tx['transactions']
        alltxn = [i for i in txn if i['account_id']==id]

        if len(alltxn)!=0:
            oldest_txn = datetime.strptime(alltxn[-1]['date'], '%Y-%m-%d').date()
            date_today = datetime.today().date() 
            how_long = (date_today - oldest_txn).days #date today - date of oldest credit transaction
            score = grid_double[np.digitize(how_long, cred_length, right=True)]
        else:
            score = 0
        return score
    
    except Exception as e:
        print('Error in credit_length()')





def livelihood(tx):
    """
    returns score quantifying the avg monthly txn count for your best credit account

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): based on avg monthly txn count
    """
    try:
        id = dynamic_select(tx)
        txn = tx['transactions']
        alltxn = [i for i in txn if i['account_id']==id]
        if len(alltxn)==0:
            score = 0
        else:
            dates = []
            amounts = []
            for i in range(len(alltxn)):
                date = datetime.strptime(alltxn[i]['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = alltxn[i]['amount']
                amounts.append(amount)

            df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))
            d = df.groupby(pd.Grouper(freq="M")).count()
            if len(d['amounts'])>=2:
                if d['amounts'][0] < 5: #exclude initial and final month with < 5 txn
                    d = d[1:]
                if d['amounts'][-1] < 5:
                    d = d[:-1]
            mean = d['amounts'].mean()
            score = grid_double[np.digitize(mean, cred_lively, right=True)]
        return score
        
    except Exception as e:
        print('Error in livelihood()')



# -------------------------------------------------------------------------- #
#                            Metric #2 Velocity                              #
# -------------------------------------------------------------------------- #   


# -------------------------------------------------------------------------- #
#                            Metric #3 Stability                             #
# -------------------------------------------------------------------------- #   

def tot_balance_now(tx):
    """
    returns score based on total balance now across ALL accounts owned by the user
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): for cumulative current balance
    """
    try:
        acc = tx['accounts']

        balance = 0
        for i in range(len(acc)):
            type = acc[i]['type']+'_'+str(acc[i]['subtype'])+'_'+str(acc[i]['official_name'])

            if type.split('_')[0]=='depository':
                if type.split('_')[1]=='savings':
                    balance += int(acc[i]['balances']['current'] or 0)
                else:
                    balance += int(acc[i]['balances']['available'] or 0)
            else:
                balance += int(acc[i]['balances']['available'] or 0)

        score = grid_double[np.digitize(balance, cum_balance, right=True)]
        return score

    except Exception as e:
        print('Error in tot_balance_now()')




# -------------------------------------------------------------------------- #
#                            Metric #4 Diversity                             #
# -------------------------------------------------------------------------- #   

def acc_count(tx):
    """
    returns score based on count of accounts owned by the user
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): score for accounts count
    """
    try:
        score = grid_triple[np.digitize(len(tx['accounts']), prod_count, right=True)]
        return score
        
    except Exception as e:
        print('Error in acc_count()')




def profile(tx):
    """
    returns score for number of saving and investment accounts owned
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): points scored for accounts owned
    """
    try:
        save = []
        loan = []
        invest = [] 
        acc = [x for x in tx['accounts'] if x['type']=='loan' or int(x['balances']['available'] or 0)!=0] #exclude $0 balance accounts

        for y in acc:
            id = y['account_id']
            type = y['type']+'_'+str(y['subtype'])
            if 'saving' in type:
                save.append(id)
            if 'loan' in type.split('_')[0]:
                loan.append(id)
            if type.split('_')[0] in ['investment', 'brokerage']:
                invest.append(id)

        m = np.digitize(len(invest), cred_count, right=True)
        n = np.digitize(len(save), cred_count, right=True)
        score = profile_mix[m][n]
        return score

    except Exception as e:
        print('Error in profile()')
