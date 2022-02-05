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

e3x3sd1 = np.array([
                        [0.0, 0.4, 0.8], 
                        [0.4, 0.8, 1.0], 
                        [0.8, 1.0, 1.0]], dtype=float) #generous
o3x4a = np.array([   
                        [0.0, 0.1, 0.3, 0.7],
                        [0.0, 0.1, 0.7, 0.9],
                        [0.0, 0.3, 0.9, 1.0]], dtype=float) #asymmetric
o4x4sd1 = np.array([
                        [0.0, 0.1, 0.3, 0.3], 
                        [0.1, 0.1, 0.3, 0.5], 
                        [0.3, 0.3, 0.5, 0.7], 
                        [0.3, 0.5, 0.7, 1.0]], dtype=float)  #moderate
e4x4sd1 = np.array([
                        [0.0, 0.1, 0.2, 0.4], 
                        [0.1, 0.2, 0.6, 0.8], 
                        [0.2, 0.6, 0.8, 1.0], 
                        [0.4, 0.8, 1.0, 1.0]], dtype=float)  #lenient
o4x4a = np.array([
                        [0.0, -0.1, -0.3, -0.5], 
                        [0.1, 0.3, 0.5, 0.7], 
                        [0.3, 0.5, 0.7, 0.9], 
                        [0.7, 0.9, 1.0, 1.0]], dtype=float) #asymmetric




duration = np.array([30, 90, 180])                          #bins: 0-30 | 31-90 | 91-180 | >180 days

count0 = np.array([1, 2])                                   #bins: 0-1 | 2 | >=3
count1 = np.array([1, 2, 3])                                #bins: <=1 | (1,2] | (2,3] | >=3 
count_products = np.array([1, 2, 4, 5])                     #bins: ...
count_lively = np.array([5, 10, 15, 25])  
count_txn_month = np.array([5, 15, 25, 40])

volume_withdraw = np.array([500, 1000, 3000])
volume_deposit = np.array([1000, 4000, 8000])
volume_flow = np.array([1000, 2000, 4000])
volume_cred_limit = np.array([1000, 8000, 20000])
volume_min_run = np.array([10000, 20000, 50000])
volume_balance_now = np.array([5000, 10000, 30000, 75000]) 

grid_double = np.array([0, 0.125, 0.25, 0.50, 1]) 
grid_triple = np.array([0, 0.3, 0.6, 0.9, 1])  
grid_log = np.array([-0.3, -0.2, -0.1, 0.2, 0.4, 0.9, 1])

percent_cred_util = np.array([0.7, 0.55, 0.35])
frequency_interest  = np.array([0.5, 0.33, 0.125, 0])
slope_linregression = np.array([-1.5, -0.5, 0, 1, 3, 15])
slope_product = np.array([0, 0.25, 0.5, 1, 1.5, 2])
ratio_flows = np.array([1, 2.5, 4])





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
                tx (dict of lists): with transactions of all user's bank accoutns (credit, checking, saving, loan, etc.) in chronological order (newest to oldest)
    """

    # Iterate through all files in a directory
    directory = os.fsencode(path_dir)
    mobi_plaid = list()
    for f in os.listdir(directory):
        filename = os.fsdecode(f)
        if filename.endswith(".json"): #filter by .json files
            mobi_plaid.append(filename) #append file names to list
    mobi_plaid =  sorted(mobi_plaid) 


    # Select one user and retrieve their transaction history
    lol = list()
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
                tx (dict): Plaid 'Transactions' product 
                acc_name (str): acccepts 'credit' or 'checking'
        
            Returns: 
                best (str or dict): Plaid account_id of best credit account 
    """
    try:
        acc = tx['accounts']
        txn = tx['transactions']

        info = list()
        matrix =  []
        for a in acc:
            if acc_name in "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower():
                id = a['account_id']
                type = "{1}{0}{2}{0}{3}".format('_', str(a['type']), str(a['subtype']), str(a['official_name'])).lower()
                limit = int(a['balances']['limit'] or 0)
                transat = [t for t in txn if t['account_id']==id]
                txn_count = len(transat)
                if len(transat)!=0:
                    length = (datetime.today().date() - datetime.strptime(transat[-1]['date'], '%Y-%m-%d').date()).days
                else:
                    length=0
                info.append([id, type, limit, txn_count, length])
                matrix.append([limit, txn_count, length])

        if len(info)!=0:
            # Build a matrix where each column is a different account. Choose the one performing best among the 3 categories
            m = np.array(matrix).T
            m[0] = m[0]*1    #assign 1pt to credit limit
            m[1] = m[1]*10   #assign 10pt to txn count
            m[2] = m[2]*3    #assign 3pt to account length
            cols = [sum(m[:,i]) for i in range(m.shape[1])]
            index_best_acc = cols.index(max(cols))
            best = {'id': info[index_best_acc][0], 'limit': info[index_best_acc][2]} 
        else:
            best = {'id': 'inexistent', 'limit': 0}
        return best

    except Exception as e:
        print(str(e))




def get_acc(tx, acc_type):
    """
    returns list of all accounts owned by the user

            Parameters:
                tx (dict): Plaid 'Transactions' product 
                acc_type (str): accepts 'credit', 'depository', 'all'
        
            Returns: 
                info (list of lists): all account owned by the user
    """
    try: 
        acc = tx['accounts']
        txn = tx['transactions'] 

        info = list()
        for a in acc:
            id = a['account_id']
            type = "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower()
            mask = a['mask']
            limit = int(a['balances']['limit'] or 0)
            transat = [x for x in txn if x['account_id']==id]
            if len(transat)!=0:
                length = (datetime.today().date() - datetime.strptime(transat[-1]['date'], '%Y-%m-%d').date()).days
            else:
                length=0

            if acc_type == 'all':
                info.append({'id':id, 'type':type, 'mask':mask, 'limit':limit, 'alltxn_count':len(transat), 'duration(days)':length})
            else:
                if acc_type in type:
                    info.append({'id':id, 'type':type, 'mask':mask, 'limit':limit, 'alltxn_count':len(transat), 'duration(days)':length})
        return info

    except Exception as e:
        print(str(e))




def flows(tx, how_many_months):
    """
    returns monthly net flow

            Parameters:
                tx (dict): Plaid 'Transactions' product 
                how_many_month (float): how many months of transaction history are you considering? 
        
            Returns: 
                flow (df): pandas dataframe with amounts for net monthly flow and datetime index
    """
    try: 
        acc = tx['accounts']
        txn = tx['transactions']

        dates = list()
        amounts = list()
        deposit_acc = list()

        # Keep only deposit->checking accounts
        for a in acc:
            id = a['account_id']
            type = "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                deposit_acc.append(id)

        # Keep only txn in deposit->checking accounts
        transat = [t for t in txn if t['account_id'] in deposit_acc]

        # Keep only income and expense transactions
        for t in transat:
            if not t['category']:
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
        yearago = lastmonth - pd.offsets.DateOffset(months=how_many_months)
        if yearago in flow.index:
            flow = flow[flow.index.tolist().index(yearago):]

        return flow

    except Exception as e:
        print(str(e))




def balance_now(tx):
    """
    returns total balance available now across ALL accounts owned by the user
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

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
        print(str(e))

# -------------------------------------------------------------------------- #
#                               Metric #1 Credit                             #
# -------------------------------------------------------------------------- #    

def credit_mix(tx):
    """
    returns score based on composition and status of user's credits accounts

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): gained based on number of credit accounts owned and duration
    """
    try: 
        # How many credit products does the user own?
        acc = tx['accounts']
        credit_acc = list()
        credit_ids = list()
        
        for a in acc:
            if 'credit' in a['type']:
                name = '{}_{}_{}'.format(a['type'], a['subtype'], a['official_name'])
                credit_acc.append(name)
                credit_ids.append(a['account_id'])
                
        how_many = len(credit_acc)
        feedback['credit'].append('User owns {} credit account(s), named {}'.format(str(how_many), credit_acc))
        
        if credit_acc:
            # How long has the user owned their credit accounts for?
            txn = tx['transactions']
            credit_txn = [t for t in txn if t['account_id'] in credit_ids]

            oldest_credit_txn = datetime.strptime(credit_txn[-1]['date'], '%Y-%m-%d').date()
            date_today = datetime.today().date() 
            how_long = (date_today - oldest_credit_txn).days # credit length = date today - date of oldest credit transaction
           
            m = np.digitize(how_many, count0, right=True)
            n = np.digitize(how_long, duration, right=True)
            score = o3x4a[m][n]
        
        else:
            score = 0

        return score

    except Exception as e:
        print(str(e))


def credit_limit(tx):
    """
    returns score for the cumulative credit limit of a user across ALL of his credit accounts

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): gained based on the cumulative credit limit across all credit accounts
    """
    try: 
        # Fetch all 'credit' accounts
        cred_acc = get_acc(tx, 'credit')

        if cred_acc:
            # Calculate cumulative limit and time passed from credit account issuance
            limit = 0
            length = list()

            for a in cred_acc:
                limit += a['limit']
                length.append(a['duration(days)'])

            m = np.digitize(max(length), duration, right=True)
            n = np.digitize(limit, volume_cred_limit, right=True)
            score = o4x4sd1[m][n]

        else:
            score = 0
            
        return score

    except Exception as e:
        print(str(e))


def credit_util_ratio(tx):
    """
    returns a score reflective of the user's credit utilization ratio, that is credit_used/credit_limit
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

            Returns:
                score (float): score for avg percent of credit limit used
    """
    try:
        txn = tx['transactions']

        # Dynamically select best credit account
        dynamic = dynamic_select(tx, 'credit')

        if dynamic['id'] == 'inexistent' or dynamic['limit'] == 0:
            score = 0

        else:
            id = dynamic['id']
            limit = dynamic['limit']

            # Keep ony transactions in best credit account
            transat = [x for x in txn if x['account_id']==id]

            if transat:
                dates = list()
                amounts = list()
                for t in transat:
                    date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                    dates.append(date)
                    amount = t['amount']
                    amounts.append(amount) 
                df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

                # Bin by month credit card 'purchases' and 'paybacks'
                util = df.groupby(pd.Grouper(freq='M'))['amounts'].agg([
                    ('payback', lambda x: x[x < 0].sum()),
                    ('purchases', lambda x: x[x > 0].sum())
                ])
                util['cred_util'] = [x/limit for x in util['purchases']]

                # Exclude current month
                if util.iloc[-1,].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
                    util = util[:-1] 

                avg_util = np.mean(util['cred_util'])
                m = np.digitize(len(util)*30, duration, right=True)
                n = np.digitize(avg_util, percent_cred_util, right=True)
                score = o4x4sd1[m][n]

            else:
                score = 0
                
        return score

    except Exception as e:
        print(str(e))


def credit_interest(tx):
    """
    returns score based on number of times user was charged credit card interest fees in past 24 months
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): gained based on interest charged
    """
    try:
        id = dynamic_select(tx, 'credit')['id']

        if id == 'inexistent':
            score = 0
        
        else:
            txn = tx['transactions']
            alltxn = [t for t in txn if t['account_id']==id]

            interests = list()

            if alltxn:
                length = min(24, round((datetime.today().date() - datetime.strptime(alltxn[-1]['date'], '%Y-%m-%d').date()).days/30, 0))
                for t in alltxn:

                    # keep only txn of type 'interest on credit card'
                    if 'Interest Charged' in t['category']:
                        date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                    
                        # keep only txn of last 24 months
                        if date > datetime.now().date() - timedelta(days=2*365): 
                            interests.append(t)

                frequency = len(interests)/length
                score = grid_double[np.digitize(frequency, frequency_interest, right=True)]
            
            else:
                score = 0
                
        return score
    
    except Exception as e:
        print(str(e))


def credit_length(tx):
    """
    returns score based on length of user's best credit account
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): gained because of credit account duration
    """
    try:
        id = dynamic_select(tx, 'credit')['id']
        txn = tx['transactions']
        alltxn = [t for t in txn if t['account_id']==id]

        if alltxn:
            oldest_txn = datetime.strptime(alltxn[-1]['date'], '%Y-%m-%d').date()
            date_today = datetime.today().date() 
            how_long = (date_today - oldest_txn).days # date today - date of oldest credit transaction
            score = grid_double[np.digitize(how_long, duration, right=True)]

        else:
            score = 0

        return score
    
    except Exception as e:
        print(str(e))


def credit_livelihood(tx):
    """
    returns score quantifying the avg monthly txn count for your best credit account

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): based on avg monthly txn count
    """
    try:
        id = dynamic_select(tx, 'credit')['id']
        txn = tx['transactions']
        alltxn = [t for t in txn if t['account_id']==id]

        if alltxn:
            dates = list()
            amounts = list()

            for i in range(len(alltxn)):
                date = datetime.strptime(alltxn[i]['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = alltxn[i]['amount']
                amounts.append(amount)

            df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))
            d = df.groupby(pd.Grouper(freq="M")).count()

            if len(d['amounts']) >= 2:
                if d['amounts'][0] < 5: # exclude initial and final month with < 5 txn
                    d = d[1:]
                if d['amounts'][-1] < 5:
                    d = d[:-1]

            mean = d['amounts'].mean()
            score = grid_double[np.digitize(mean, count_lively, right=True)]
        
        else:
            score = 0
        
        return score
        
    except Exception as e:
        print(str(e))

# -------------------------------------------------------------------------- #
#                            Metric #2 Velocity                              #
# -------------------------------------------------------------------------- #   

def velocity_withdrawals(tx):
    """
    returns score based on count and volumne of monthly automated withdrawals

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): score associated with reccurring monthly withdrawals
    """
    try: 
        txn = tx['transactions']
        withdraw = [['Service', 'Subscription'], ['Service', 'Financial', 'Loans and Mortgages'], ['Service', 'Insurance'], ['Payment', 'Rent']]
        dates = list()
        amounts = list()

        for t in txn:
            if t['category'] in withdraw and t['amount'] > 15:
                date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = abs(t['amount'])
                amounts.append(amount)

        df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

        if len(df.index) > 0:
            how_many = np.mean(df.groupby(pd.Grouper(freq='M')).count().iloc[:,0].tolist())
            volume = np.mean(df.groupby(pd.Grouper(freq='M')).sum().iloc[:,0].tolist())

            m = np.digitize(how_many, count1*2, right=True)
            n = np.digitize(volume, volume_withdraw, right=True)
            score = e4x4sd1[m][n]

        else:
            score = 0
            
        return score

    except Exception as e:
        print(str(e))


def velocity_deposits(tx):
    """
    returns score based on count and volumne of monthly automated deposits

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): score associated with direct deposits
    """
    try: 
        txn = tx['transactions']
        dates = list()
        amounts = list()

        for t in txn:
            if t['amount'] < -200 and 'payroll' in [c.lower() for c in t['category']]:
                date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                dates.append(date)
                amount = abs(t['amount'])
                amounts.append(amount)

        df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

        if len(df.index) > 0:
            how_many = np.mean(df.groupby(pd.Grouper(freq='M')).count().iloc[:,0].tolist())
            volume = np.mean(df.groupby(pd.Grouper(freq='M')).sum().iloc[:,0].tolist())

            m = np.digitize(how_many, count1, right=True)
            n = np.digitize(volume, volume_deposit, right=True)
            score = e4x4sd1[m][n]

        else:
            score = 0
        
        return score

    except Exception as e:
        print(str(e))


def velocity_month_net_flow(tx):
    """
    returns score for monthly net flow

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): score associated with monthly new flow
    """
    try: 
        flow = flows(tx, 12)

        # Calculate magnitude of flow (how much is flowing monthly?)
        cum_flow = [abs(x) for x in flow['amounts'].tolist()] 
        magnitude = np.mean(cum_flow)

        # Calculate direction of flow (is money coming in or oing out?)
        neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
        pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))

        if neg:
            direction = len(pos)/len(neg)  # output in range [0, ...)
        else:
            direction = 10

        # Calculate score
        m = np.digitize(magnitude, volume_flow, right=True)
        n = np.digitize(direction, ratio_flows, right=True)
        score = o4x4a[m][n]

        return score

    except Exception as e:
        print(str(e))


def velocity_month_txn_count(tx):
    """
    returns score based on count of mounthly transactions

            Parameters:
                tx (dict): Plaid 'Transactions' product 
        
            Returns: 
                score (float): the larget the monthly count the larger the score
    """
    try: 
        acc = tx['accounts']
        txn = tx['transactions']

        dates = list()
        amounts = list()
        mycounts = list()
        deposit_acc = list()

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
                if abs(t['amount']) > 5:
                    date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                    dates.append(date)
                    amount = t['amount']
                    amounts.append(amount)
                    
            df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

            # Calculate avg count of monthly transactions for one checking account at a time
            if len(df.index) > 0:
                cnt = df.groupby(pd.Grouper(freq='M')).count().iloc[:,0].tolist()
            else:
                score = 0
            
            mycounts.append(cnt)

        mycounts = [x for y in mycounts for x in y]
        how_many = np.mean(mycounts) 
        score = grid_triple[np.digitize(how_many, count_txn_month, right=True)]

        return score

    except Exception as e:
        print(str(e))


def velocity_slope(tx):
    """
    returns score for the historical behavior of the net monthly flow for past 24 months
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

            Returns:
                score (float): score for flow net behavior over past 24 months
    """
    try:
        flow = flows(tx, 24)

        # If you have > 10 data points OR all net flows are positive, then perform linear regression
        if len(flow) >= 10 or len(list(filter(lambda x: (x < 0), flow['amounts'].tolist()))) == 0:
            # Perform Linear Regression using numpy.polyfit() 
            x = range(len(flow['amounts']))
            y = flow['amounts']
            a,b = np.polyfit(x, y, 1)
            
            # Plot regression line
            plt.plot(x, y, '.')
            plt.plot(x, a*x +b)
            score = grid_log[np.digitize(a, slope_linregression, right=True)]

        # If you have < 10 data points, then calculate the score by taking the product of two ratios
        else:
            # Multiply two ratios by each other
            neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
            pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))
            r = len(pos) / len(neg) * abs(sum(pos)/sum(neg))  # output in range [0, 2+]
            score = grid_log[np.digitize(r, slope_product, right=True)]

        return score

    except Exception as e:
        print(str(e))

# -------------------------------------------------------------------------- #
#                            Metric #3 Stability                             #
# -------------------------------------------------------------------------- #  

def stability_tot_balance_now(tx):
    """
    returns score based on total balance now across ALL accounts owned by the user
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

            Returns:
                score (float): for cumulative current balance
    """
    try:
        balance = balance_now(tx)
        score = grid_double[np.digitize(balance, volume_balance_now, right=True)]

        return score

    except Exception as e:
        print(str(e))


def stability_min_running_balance(tx):
    """
    returns score based on the minimum balance maintained for 12 months
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): for volume of minimum balance and duration
    """
    try:
        # Calculate net flow each month for past 12 months i.e, |income-expenses|
        nets = flows(tx, 12)['amounts'].tolist()

        # Calculate total current balance now
        balance = balance_now(tx)

        # Subtract net flow from balancenow to calculate the running balance for the past 12 months
        running_balances = list()

        for n in reversed(nets):
            balance = balance + n
            running_balances.append(balance)

        # Calculate volume using a weighted average
        weights = np.linspace(0, 1, len(running_balances)).tolist() # define your weights
        volume = sum([x*w for x in running_balances for w in reversed(weights)]) / sum(weights) 
        length = len(running_balances)*30

        # Compute the score
        m = np.digitize(length, duration, right=True)
        n = np.digitize(volume, volume_min_run, right=True)
        score = e4x4sd1[m][n] -0.05*len(list(filter(lambda x: (x < 0), running_balances))) # add 0.05 score penalty for each overdrafts
        
        return score

    except Exception as e:
        print(str(e))

# -------------------------------------------------------------------------- #
#                            Metric #4 Diversity                             #
# -------------------------------------------------------------------------- #

def diversity_acc_count(tx):
    """
    returns score based on count of accounts owned by the user
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

            Returns:
                score (float): score for accounts count
    """
    try:
        score = grid_triple[np.digitize(len(tx['accounts']), count_products, right=True)]

        return score
        
    except Exception as e:
        print(str(e))


def diversity_profile(tx):
    """
    returns score for number of saving and investment accounts owned
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): points scored for accounts owned
    """
    try:
        save = list()
        loan = list()
        invest = list()

        acc = [x for x in tx['accounts'] if x['type']=='loan' or int(x['balances']['available'] or 0) != 0] # exclude $0 balance accounts

        for a in acc:
            id = a['account_id']
            type = "{}_{}".format(a['type'], str(a['subtype']))

            if 'saving' in type:
                save.append(id)
            
            if 'loan' in type.split('_')[0]:
                loan.append(id)
            
            if type.split('_')[0] in ['investment', 'brokerage']:
                invest.append(id)

        m = np.digitize(len(invest), count0, right=False)
        n = np.digitize(len(save), count0, right=False)
        score = e3x3sd1[m][n]
        
        return score

    except Exception as e:
        print(str(e))