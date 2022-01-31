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
# naming convention: content+shape+symmetry, Even+4x4+SymmetricAlongDyagonal1 -> e4x4sd1
# naming convention: content+shape+symmetry, Odd+3x4+Asymmetric -> o3x4a

cred_mix = np.array([   
                        [0.0, 0.1, 0.3, 0.7],
                        [0.0, 0.4, 0.7, 0.8],
                        [0.0, 0.8, 0.9, 1.0]], dtype=float) 
profile_mix = np.array([
                        [0.0, 0.4, 0.6, 0.7], 
                        [0.4, 0.8, 1.0, 1.0], 
                        [0.6, 1.0, 1.0, 1.0], 
                        [0.7, 1.0, 1.0, 1.0]], dtype=float)
e4x4sd1 = np.array([
                        [0.0, 0.1, 0.2, 0.4], 
                        [0.1, 0.2, 0.6, 0.8], 
                        [0.2, 0.6, 0.8, 1.0], 
                        [0.4, 0.8, 1.0, 1.0]], dtype=float)  

cred_length = np.array([30, 90, 180])                     #bins: 0-30 | 31-90 | 91-180 | >180
cred_count = np.array([0, 1, 2])                           #bins: 0 | 1 | 2 | >=3
count1 = np.array([1, 2, 3])                               #bins: <=1 | (1,2] | (2,3] | >=3 
cred_lively = np.array([5, 10, 15, 25])                    #bins: ...
prod_count = np.array([1, 3, 4, 6])   
count2 = np.array([5, 15, 25, 40])
slope_checking = np.array([-1.5, -0.5, 0, 1, 3, 15])
product_checking = np.array([0, 0.25, 0.5, 1, 1.5, 2])
cum_balance = np.array([5000, 10000, 30000, 75000]) 
grid_double = np.array([0, 0.125, 0.25, 0.50, 1]) 
grid_triple = np.array([0, 0.3, 0.6, 0.9, 1])  
grid_log = np.array([-0.3, -0.2, -0.1, 0.2, 0.4, 0.9, 1])
volume_min_run = np.array([5000, 15000, 25000])
volume_deposit = np.array([1000, 4000, 8000])
volume_withdraw = np.array([500, 1000, 3000])
volume_flow = np.array([500, 1000, 3000, 4000])


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

def get_tx(path_dir, userid):
    """
    returns the Plaid 'Transaction' product for one user

            Parameters:
                path_dir (str): path to the directory where the transaction files are stored
                userid (str): number of the user you want to retrieve transaction data for
        
            Returns: 
                tx (dict of lists): with transactions of all user's bank accoutns (credit, checking, saving, load, etc.) in chronological order (newest to oldest)
    """

    # Iterate through all files in a directory
    directory = os.fsencode(path_dir)
    mobi_plaid = []
    for f in os.listdir(directory):
        filename = os.fsdecode(f)
        if filename.endswith(".json"):
            mobi_plaid.append(filename) # append file names to list
    mobi_plaid =  sorted(mobi_plaid) 


    #Select one user and retrieve their transaction history
    lol = []
    for f in mobi_plaid:
        if f.startswith("{}-tx_".format(userid)): #choose your user
            tx_one_page = json.load(open(path_dir+f)) #open json
            acc = tx_one_page['accounts']
            lol.append(tx_one_page['transactions']) #append txn data only
    txn = list(np.concatenate(lol).flat) #flatten list 
    tx = {'accounts':acc, 'transactions':txn}
    return tx
    
    



def dynamic_select(tx, acc_name):
    """
    dynamically pick the best credit account,
    i.e. the account that performs best in 2 out of these 3 categories:
    highest credit limit / largest txn count / longest txn history
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 
                acc_name (str): acccepts 'credit' or 'checking'
        
            Returns: 
                best (str): Plaid account_id of best credit account 
    """
    try:
        acc = tx['accounts']
        txn = tx['transactions']

        info = []
        for a in acc:
            if acc_name in "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower():
                id = a['account_id']
                type = "{1}{0}{2}{0}{3}".format('_', str(a['type']), str(a['subtype']), str(a['official_name'])).lower()
                limit = a['balances']['limit']
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

        




def get_acc(tx):
    """
    returns list of all accounts owned by the user

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                info (list of lists): all account owned by the user
    """
    try: 
        acc = tx['accounts']
        txn = tx['transactions'] 
        info = []
        for a in acc:
            id = a['account_id']
            type = "{1}{0}{2}{0}{3}".format('_', str(a['type']), str(a['subtype']), str(a['official_name'])).lower()
            mask = a['mask']
            limit = int(a['balances']['limit'] or 0)
            transat = [x for x in txn if x['account_id']==id]
            txn_count = len(transat)
            if len(transat)!=0:
                length = (datetime.today().date() - datetime.strptime(transat[-1]['date'], '%Y-%m-%d').date()).days
            else:
                length=0
            info.append([id, type, mask, limit, txn_count, length])
        return info

    except Exception as e:
        print('Error in get_acc()')

        



def flows(tx):
    """
    returns monthly net flow

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                flow (df): pandas dataframe with amounts for monthly new flow and datetime index
    """
    try: 
        acc = tx['accounts']
        txn = tx['transactions']

        dates = []
        amounts = []
        deposit_acc = []

        # Keep only deposit->checking accounts
        for a in acc:
            id = a['account_id']
            type = "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                deposit_acc.append(id)

        # Keep only txn in deposit->checking accounts
        transat = [x for x in txn if x['account_id'] in deposit_acc]

        # Keep only income and expense transactions
        for t in transat:
            if t['category'] is None:
                pass
            else:
                category = t['category']
                
            #exclude micro txn and exclude internal transfers
            if abs(t['amount']) > 5 and 'internal account transfer' not in category: 
                date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = t['amount']
                amounts.append(amount)
        df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

        # Bin by month
        flow = df.groupby(pd.Grouper(freq='M')).sum()

        # Exclude current month
        if flow.iloc[-1,].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
            flow = flow[:-1] 

        # Keep only past 12 months. If longer, then crop
        daytoday = datetime.today().date().day
        lastmonth = datetime.today().date() - pd.offsets.DateOffset(days=daytoday)
        yearago = lastmonth - pd.offsets.DateOffset(months=12)
        if yearago in flow.index:
            flow = flow[flow.index.tolist().index(yearago):]

        return flow

    except Exception as e:
        print('Error in flow(()')




def balance_now(tx):
    """
    returns total balance available now across ALL accounts owned by the user
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                balance (float): cumulative current balance
    """
    try:
        acc = tx['accounts']

        balance = 0
        for a in acc:
            type = "{1}{0}{2}{0}{3}".format('_', str(a['type']), str(a['subtype']), str(a['official_name'])).lower()

            if type.split('_')[0]=='depository':
                if type.split('_')[1]=='savings':
                    balance += int(a['balances']['current'] or 0)
                else:
                    balance += int(a['balances']['available'] or 0)
            else:
                balance += int(a['balances']['available'] or 0)

        return balance

    except Exception as e:
        print('Error in balance_now()')


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


def withdrawals(tx):
    """
    returns score based on count and volumne of monthly automated withdrawals

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): score associated with reccurring monthly withdrawals
    """
    try: 
        txn = tx['transactions']
        withdraw = [['Service', 'Subscription'], ['Service', 'Financial', 'Loans and Mortgages'], ['Service', 'Insurance'], ['Payment', 'Rent']]
        dates = []
        amounts = []
        for t in txn:
            if t['category'] in withdraw and t['amount'] > 15:
                date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = abs(t['amount'])
                amounts.append(amount)
        df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

        if len(df)==0:
            score = 0
        else:
            cnt = df.groupby(pd.Grouper(freq='M')).count().iloc[:,0].tolist()
            how_many = sum(cnt)/len(cnt)
            volumes = df.groupby(pd.Grouper(freq='M')).sum().iloc[:,0].tolist()
            volume = sum(volumes)/len(volumes)
            m = np.digitize(how_many, count1*2, right=True)
            n = np.digitize(volume, volume_withdraw, right=True)
            score = e4x4sd1[m][n]
        return score

    except Exception as e:
        print('Error in deposits()')



def deposits(tx):
    """
    returns score based on count and volumne of monthly automated deposits

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): score associated with direct deposits
    """
    try: 
        txn = tx['transactions']
        dates = []
        amounts = []
        for t in txn:
            if t['amount'] < -200 and 'payroll' in [c.lower() for c in t['category']]:
                date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = abs(t['amount'])
                amounts.append(amount)
        df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

        if len(df)==0:
            score = 0
        else:
            cnt = df.groupby(pd.Grouper(freq='M')).count().iloc[:,0].tolist()
            how_many = sum(cnt)/len(cnt)
            volumes = df.groupby(pd.Grouper(freq='M')).sum().iloc[:,0].tolist()
            volume = sum(volumes)/len(volumes)
            m = np.digitize(how_many, count1, right=True)
            n = np.digitize(volume, volume_deposit, right=True)
            score = e4x4sd1[m][n]
        return score

    except Exception as e:
        print('Error in deposits()')



def month_net_flow(tx):
    """
    returns score for monthly net flow

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): score associated with monthly new flow
    """
    try: 
        flow = flows(tx)
        avg_net_flow = sum(flow['amounts'].tolist())/len(flow)
        avg_net_flow
        score = grid_triple[np.digitize(avg_net_flow, volume_flow, right=True)]
        return score

    except Exception as e:
        print('Error in month_net_flow(()')





def month_txn_count(tx):
    """
    returns score based on count of mounthly transactions

            Parameters:
                tx (dic): Plaid 'Transactions' product 
        
            Returns: 
                score (float): the lrget the monthly count the larger the score
    """
    try: 
        acc = tx['accounts']
        txn = tx['transactions']


        dates = []
        amounts = []
        mycounts = []
        deposit_acc = []

        # Keep only deposit->checking accounts
        for a in acc:
            id = a['account_id']
            type = "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                deposit_acc.append(id)

        # Keep only txn in deposit->checking accounts
        for d in deposit_acc:
            transat = [x for x in txn if x['account_id'] == d]

            # Bin transactions by month 
            for t in transat:
                if t['amount'] > 5:
                    date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                    dates.append(date)
                    amount = t['amount']
                    amounts.append(amount)
            df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

            # Calculate avg count of monthly transactions for one checking account at a time
            if len(df)==0:
                score = 0
            else:
                cnt = df.groupby(pd.Grouper(freq='M')).count().iloc[:,0].tolist()
            mycounts.append(cnt)

        mycounts = [x for y in mycounts for x in y]
        how_many=sum(mycounts)/len(mycounts)
        score = grid_triple[np.digitize(how_many, count2, right=True)]
        return score


    except Exception as e:
        print('Error in deposits()')



def slope(tx):
    """
    returns score for the historical behavior of the net monthly flow for past 24 months
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): score for flow net behavior over past 24 months
    """
    try:
        acc = tx['accounts']
        txn = tx['transactions']

        dates = []
        amounts = []
        deposit_acc = []

        # Keep only deposit->checking accounts
        for a in acc:
            id = a['account_id']
            type = "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                deposit_acc.append(id)

        # Keep only txn in deposit->checking accounts
        transat = [x for x in txn if x['account_id'] in deposit_acc]

        # Keep only income and expense transactions
        for t in transat:
            if t['category'] is None:
                pass
            else:
                category = t['category']
                
            #exclude micro txn and exclude internal transfers
            if abs(t['amount']) > 5 and 'internal account transfer' not in category: 
                date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = t['amount']
                amounts.append(amount)
        df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

        # Bin by month
        flow = df.groupby(pd.Grouper(freq='M')).sum()

        # Exclude current month
        if flow.iloc[-1,].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
            flow = flow[:-1] 

        # Keep only past 24 months
        daytoday = datetime.today().date().day
        lastmonth = datetime.today().date() - pd.offsets.DateOffset(days=daytoday)
        yearago = lastmonth - pd.offsets.DateOffset(months=24)
        if yearago in flow.index:
            flow = flow[flow.index.tolist().index(yearago):]

        # If you have more than 10 data points OR all net flows are positive, then perform linear regression
        if len(flow) >= 10 or len(list(filter(lambda x: (x < 0), flow['amounts'].tolist())))==0 :
            # Perform Linear Regression using numpy.polyfit() 
            x = range(len(flow['amounts']))
            y = flow['amounts']
            a,b = np.polyfit(x, y, 1)
            # Plot regression line
            plt.plot(x, y, '.')
            plt.plot(x, a*x +b)
            score = grid_log[np.digitize(a, slope_checking, right=True)]

        # If you have < 10 data points, then calculate the score by taking the product of two rations
        else:
            # Multiply two ratios by each other
            neg= list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
            pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))
            r = len(pos)/len(neg)*abs(sum(pos)/sum(neg))  # output in range [0, 2+]
            score = grid_log[np.digitize(r, product_checking, right=True)]

        return score

    except Exception as e:
        print('Error in slope(()')




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
        balance = balance_now(tx)
        score = grid_double[np.digitize(balance, cum_balance, right=True)]
        return score

    except Exception as e:
        print('Error in tot_balance_now()')




def min_running_balance(tx):
    """
    returns score based on the minimum balance maintained for 12 months
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): for volume of minimum balance and duration
    """
    try:
        # Calculate net flow each month for past 12 months i.e, |income-expenses|
        nets = flows(tx)['amounts'].tolist()
        # Calculate current balance now
        balance = balance_now(tx)

        # Subtract net flow from balancenow to calculate the running balance for the past 12 months
        running_balances = []
        for n in reversed(nets):
            balance = balance + n
            running_balances.append(balance)
        volume = np.mean(running_balances)
        duration = len(running_balances)*30

        # Compute the score
        m = np.digitize(duration, cred_length, right=True)
        n = np.digitize(volume, volume_min_run, right=True)
        score = e4x4sd1[m][n] -0.05*len(list(filter(lambda x: (x < 0), running_balances))) #add 0.05 score penalty for each overdrafts
        return score

    except Exception as e:
        print('Error in min_running_balance()')


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

