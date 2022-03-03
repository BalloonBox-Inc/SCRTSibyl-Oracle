
# Import libraries
import os
import json

import numpy as np
import pandas as pd
from datetime import datetime, date
from datetime import timedelta
from dotenv import dotenv_values

import matplotlib.pyplot as plt



# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                    -utils-                                 #
# -------------------------------------------------------------------------- #

def build_2D_matrix_by_rule(size, scalar):
    """
    returns a matrix of given size, built through a generalized rule. The matrix must be 2D

            Parameters:
                size (tuple): declare the matrix size in this format (m, n), where m = rows and n = columns
                scalar (tuple): scalars to multiply the log_10 by. Follow the format (m_scalar, n_scalar)
                    m_float: the current cell is equal to m_scalar * log_10(row #) 
                    n_float: the current cell is equal to n_scalar * log_10(column #) 

            Returns:
                a matrix of size m x n whose cell are given by m_float+n_float
    """
    # Initialize a zero-matrix of size = (m x n)
    matrix = np.zeros(size)
    for m in range(matrix.shape[0]):
        for n in range(matrix.shape[1]):
            matrix[m][n] = round(scalar[0]*np.log10(m+1) + scalar[1]*np.log10(n+1), 2)
            
    return matrix



# -------------------------------------------------------------------------- #
#                               Score Matrices                               #
# -------------------------------------------------------------------------- # 

# Initialize 'feedback' dict
# feedback = {'data fetch': [], 'credit': [], 'velocity': [], 'stability': [], 'diversity': []}
warning = 'WARNING: Error occured during computation. Your score was rounded down for error handling. Retry later.'

# Scoring grids
# naming convention: matrix+shape+rule, Matrix+6x6+Rule+row#**1*0.15_column#**1*0.05 -> m7x7_03_17.T
# naming convention: matrix+shape+rule, Matrix+6x6+Rule+row#**1*0.05_column#**2*0.03 -> m7x7_03_17
m7x7_03_17 = build_2D_matrix_by_rule((7,7), (1/3.03, 1/1.17))
m7x7_85_55 = build_2D_matrix_by_rule((7,7), (1/1.85, 1/1.55))
m3x7_2_4 = build_2D_matrix_by_rule((3,7), (1/1.2, 1/1.4))
m3x7_73_17 = build_2D_matrix_by_rule((3,7), (1/1.73, 1/1.17))

fico = (np.array([300, 500, 560, 650, 740, 800, 870])-300)/600  # Fico score binning - normalized
fico_medians = [round(fico[i]+(fico[i+1]-fico[i])/2, 2) for i in range(len(fico)-1)] # Medians of Fico scoring bins
fico_medians.append(1)
fico_medians = np.array(fico_medians)


# Categorical bins
duration = np.array([90, 120, 150, 180, 210, 270])          #bins: 0-90 | 91-120 | 121-150 | 151-180 | 181-270 | >270 days
count0 = np.array([1, 2])                                   #bins: 0-1 | 2 | >=3
count_lively = np.array([round(x, 0) for x in fico*25])[1:]
count_txn_month = np.array([round(x, 0) for x in fico*40])[1:]
count_invest_acc = np.array([1, 2, 3, 4, 5, 6])


volume_flow = np.array([round(x, 0) for x in fico*1500])[1:]
volume_cred_limit = np.array([0.5, 1, 5, 8, 13, 18])*1000
volume_withdraw = np.array([round(x, 0) for x in fico*1500])[1:]
volume_deposit = np.array([round(x, 0) for x in fico*7000])[1:]
volume_invest = np.array([0.5, 1, 2, 4, 6, 8])*1000
volume_balance_now = np.array([3, 5, 9, 12, 15, 18])*1000
volume_min_run = np.array([round(x, 0) for x in fico*10000])[1:]


percent_cred_util = np.array([round(x, 2) for x in reversed(fico*0.9)][:-1])
frequency_interest = np.array([round(x, 2) for x in reversed(fico*0.6)][:-1])
ratio_flows = np.array([0.7, 1, 1.4, 2, 3, 4])
slope_product = np.array([0.5, 0.8, 1, 1.3, 1.6, 2])
slope_linregression = np.array([-0.5, 0, 0.5, 1, 1.5, 2])




# -------------------------------------------------------------------------- #
#                         Helper Functions - local                           #
# -------------------------------------------------------------------------- #

# Remove this function eventually. It's used only to fetch local data for testing purposes.
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


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #

def datetime_to_str(o):
    """
    cast a datetime or date object into its string representation

            Parameters:
                o: datetime or date object

            Returns:
                string representation for its associated datetime or date object

    """
    if (isinstance(o, date)) | (isinstance(o, datetime)):
        return o.__str__()





def dict_to_json(plaid_txn):
    """
    serialize a Python data structure (dict) as JSON using the json.dumps method

            Parameters:
                plaid_txn (dict): data dictionary fetched through Plaid API

            Returns:
                tx (dict): serialized json file containing user accounts and transactions. Datetime objects are parsed into their string representation
     """
    try:
        # Write Plaid API data to json    
        with open('data_plaid.json', 'w') as fp:
            # Keep only compleetd ransactions (filter out pending transactions)
            all_txn = []
            for t in plaid_txn['transactions']:
                if t['pending'] == False:
                    all_txn.append(t)

            # Prettify and write to json
            tx = {'accounts':plaid_txn['accounts'], 'transactions':all_txn}
            json.dump(tx, fp,  indent=4, default=datetime_to_str)

        # Open json file
        tx = json.load(open('data_plaid.json'))
        return tx

    except Exception as e:
        feedback['data fetch'].append("{} in {}(): {}".format(e.__class__, dict_to_json.__name__, e))





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
        feedback['data fetch'].append("{} in {}(): {}".format(e.__class__, dynamic_select.__name__, e))




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
        feedback['data fetch'].append("{} in {}(): {}".format(e.__class__, get_acc.__name__, e))




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

        # Keep only past X months. If longer, then crop
        daytoday = datetime.today().date().day
        lastmonth = datetime.today().date() - pd.offsets.DateOffset(days=daytoday)
        yearago = lastmonth - pd.offsets.DateOffset(months=how_many_months)
        if yearago in flow.index:
            flow = flow[flow.index.tolist().index(yearago):]

        return flow

    except Exception as e:
        feedback['data fetch'].append("{} in {}(): {}".format(e.__class__, flows.__name__, e))




    
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
                balance += int(a['balances']['current'] or 0)
                
            else:
                balance += int(a['balances']['available'] or 0)

        return balance

    except Exception as e:
        feedback['stability'].append("{} in {}(): {}".format(e.__class__, balance_now.__name__, e))





def balance_now_checking_only(tx):
    """
    returns total balance available now in the user's checking accounts
    
            Parameters:
                tx (dict): Plaid 'Transactions' product

            Returns:
                balance (float): cumulative current balance in checking accounts
    """
    try:
        acc = tx['accounts']

        balance = 0
        for a in acc:
            type = "{1}{0}{2}".format('_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                balance += int(a['balances']['current'] or 0)
                
        return balance

    except Exception as e:
        feedback['stability'].append("{} in {}(): {}".format(e.__class__, balance_now.__name__, e))




# -------------------------------------------------------------------------- #
#                               Metric #1 Credit                             #
# -------------------------------------------------------------------------- #  

def credit_mix(tx, feedback):
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
                name = '{}_{}'.format(a['subtype'], a['official_name'])
                credit_acc.append(name)
                credit_ids.append(a['account_id'])
                
        how_many = len(credit_acc)
        feedback['credit'].append('User owns {} credit account(s)'.format(str(how_many)))
        feedback['credit'].append('{}'.format(credit_acc)) #print names of credit accoutns
        
        if credit_acc:
            # How long has the user owned their credit accounts for?
            txn = tx['transactions']
            credit_txn = [t for t in txn if t['account_id'] in credit_ids]

            oldest_credit_txn = datetime.strptime(credit_txn[-1]['date'], '%Y-%m-%d').date()
            date_today = datetime.today().date() 
            how_long = (date_today - oldest_credit_txn).days # credit length = date today - date of oldest credit transaction
           
            m = np.digitize(how_many, count0, right=True)
            n = np.digitize(how_long, duration, right=True)
            score = m3x7_2_4[m][n]
            feedback['credit'].append(score)
        
        else:
            score = 0

        return score, feedback

    except Exception as e:
        score = 0
        feedback['credit'].append("{} {} in {}(): {}".format(warning, e.__class__, credit_mix.__name__, e))
        return score, feedback




def credit_limit(tx, feedback):
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
            score = m7x7_03_17[m][n]
            feedback['credit'].append('Cumulative credit limit = ${}'.format(limit))

        else:
            score = 0
            feedback['credit'].append('no credit limit')
            
        return score, feedback

    except Exception as e:
        score = 0
        feedback['credit'].append("{} {} in {}(): {}".format(warning, e.__class__, credit_limit.__name__, e))
        return score, feedback





def credit_util_ratio(tx, feedback):
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
                score = m7x7_85_55[m][n]
                feedback['credit'].append('Credit util ratio (monthly avg) = {}'.format(round(avg_util, 2)))

            else:
                score = 0
                feedback['credit'].append('no credit history')
                
        return score, feedback

    except Exception as e:
        score = 0
        feedback['credit'].append("{} {} in {}(): {}".format(warning, e.__class__, credit_util_ratio.__name__, e))
        return score, feedback




def credit_interest(tx, feedback):
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
                score = fico_medians[np.digitize(frequency, frequency_interest, right=True)]
                feedback['credit'].append('Count interest charged (last 2 yrs) = {}'.format(round(frequency, 0)))
            
            else:
                score = 0
                
        return score, feedback
    
    except Exception as e:
        score = 0
        feedback['credit'].append("{} {} in {}(): {}".format(warning, e.__class__, credit_interest.__name__, e))
        return score, feedback




def credit_length(tx, feedback):
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
            score = fico_medians[np.digitize(how_long, duration, right=True)]
            feedback['credit'].append('Duration of best credit card = {} (days)'.format(how_long))

        else:
            score = 0

        return score, feedback
    
    except Exception as e:
        score = 0
        feedback['credit'].append("{} {} in {}(): {}".format(warning, e.__class__, credit_length.__name__, e))
        return score, feedback




def credit_livelihood(tx, feedback):
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
            score = fico_medians[np.digitize(mean, count_lively, right=True)]
            feedback['credit'].append('Avg cunt monthly txn = {}'.format(round(mean, 0)))
            
        else:
            score = 0
        
        return score, feedback
        
    except Exception as e:
        score = 0
        feedback['credit'].append("{} {} in {}(): {}".format(warning, e.__class__, credit_livelihood.__name__, e))
        return score, feedback
  



# -------------------------------------------------------------------------- #
#                            Metric #2 Velocity                              #
# -------------------------------------------------------------------------- # 

def velocity_withdrawals(tx, feedback):
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
            if how_many > 0 :
                volume = np.mean(df.groupby(pd.Grouper(freq='M')).sum().iloc[:,0].tolist())

                m = np.digitize(how_many, count0, right=True)
                n = np.digitize(volume, volume_withdraw, right=True)
                score = m3x7_73_17[m][n]
                feedback['velocity'].append('Monthly withdrawals: count = {}, volume = {}'.format(round(how_many, 0), round(volume, 0)))

        else:
            score = 0
            
        return score, feedback

    except Exception as e:
        score = 0
        feedback['velocity'].append("{} {} in {}(): {}".format(warning, e.__class__, velocity_withdrawals.__name__, e))
        return score, feedback




def velocity_deposits(tx, feedback):
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
            if how_many > 0 :
                volume = np.mean(df.groupby(pd.Grouper(freq='M')).sum().iloc[:,0].tolist())

                m = np.digitize(how_many, count0, right=True)
                n = np.digitize(volume, volume_deposit, right=True)
                score = m3x7_73_17[m][n]
                feedback['velocity'].append('Monthly deposits: count = {}, volume = {}'.format(round(how_many, 0), round(volume, 0)))

        else:
            score = 0
        
        return score, feedback

    except Exception as e:
        score = 0
        feedback['velocity'].append("{} {} in {}(): {}".format(warning, e.__class__, velocity_deposits.__name__, e))
        return score, feedback




def velocity_month_net_flow(tx, feedback):
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

        # Calculate direction of flow (is money coming in or going out?)
        neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
        pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))

        if neg:
            direction = len(pos)/len(neg)  # output in range [0, ...)
        else:
            direction = 10

        # Calculate score
        m = np.digitize(direction, ratio_flows, right=True)
        n = np.digitize(magnitude, volume_flow, right=True)
        score = m7x7_03_17[m][n]
        feedback['velocity'].append('Avg monthly net flow for last year = ${}'.format(round(magnitude, 2)))

        return score, feedback


    except Exception as e:
        score = 0
        feedback['velocity'].append("{} {} in {}(): {}".format(warning, e.__class__, velocity_month_net_flow.__name__, e))
        return score, feedback




def velocity_month_txn_count(tx, feedback):
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
        score = fico_medians[np.digitize(how_many, count_txn_month, right=True)]
        feedback['velocity'].append('Avg count monthly txn = {}'.format(round(how_many, 0)))

        return score, feedback


    except Exception as e:
        score = 0
        feedback['velocity'].append("{} {} in {}(): {}".format(warning, e.__class__, velocity_month_txn_count.__name__, e))
        return score, feedback




def velocity_slope(tx, feedback):
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
            score = fico_medians[np.digitize(a, slope_linregression, right=True)]
            feedback['velocity'].append('Slope of net monthly flow (last 2 yrs) = {}'.format(round(a, 2)))

        # If you have < 10 data points, then calculate the score accounting for two ratios
        else:
            # Multiply two ratios by each other
            neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
            pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))
            direction = len(pos) / len(neg) # output in range [0, 2+]
            magnitude = abs(sum(pos)/sum(neg))  # output in range [0, 2+]
            if direction >= 1:
                direct = '+'
            else:
                direct = '-'
            m = np.digitize(direction, slope_product, right=True)
            n = np.digitize(magnitude, slope_product, right=True)
            score = m7x7_03_17.T[m][n]
            feedback['velocity'].append('Magnitude of net monthly flow (< 2 yrs) = {}{}'.format(direct, round(magnitude, 4)))

        return score, feedback


    except Exception as e:
        score = 0
        feedback['velocity'].append("{} {} in {}(): {}".format(warning, e.__class__, velocity_slope.__name__, e))
        return score, feedback





# -------------------------------------------------------------------------- #
#                            Metric #3 Stability                             #
# -------------------------------------------------------------------------- #  

def stability_tot_balance_now(tx, feedback):
    """
    returns score based on total balance now across ALL accounts owned by the user
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

            Returns:
                score (float): for cumulative current balance
    """
    try:
        balance = balance_now(tx)

        # Reward only positive balances
        if balance > 0:
            score = fico_medians[np.digitize(balance, volume_balance_now, right=True)]
        else:
            score = 0

        feedback['stability'].append('Tot balance now = ${}'.format(balance))

        return score, feedback

    except Exception as e:
        score = 0
        feedback['stability'].append("{} {} in {}(): {}".format(warning, e.__class__, stability_tot_balance_now.__name__, e))
        return score, feedback




def stability_min_running_balance(tx, feedback):
    """
    returns score based on the average minimum balance maintained for 12 months
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): for volume of minimum balance and duration
    """
    try:
        # Calculate net flow each month for past 12 months i.e, |income-expenses|
        nets = flows(tx, 12)['amounts'].tolist()

        # Calculate total current balance now
        balance = balance_now_checking_only(tx)

        # Subtract net flow from balancenow to calculate the running balance for the past 12 months
        running_balances = list()

        for n in reversed(nets):
            balance = balance + n
            running_balances.append(balance)

        # Calculate volume using a weighted average
        weights = np.linspace(0.01, 1, len(running_balances)).tolist() # define your weights
        volume = sum([x*w for x,w in zip(running_balances, reversed(weights))]) / sum(weights) 
        length = len(running_balances)*30

        # Compute the score
        m = np.digitize(length, duration, right=True)
        n = np.digitize(volume, volume_min_run, right=True)
        score = m7x7_85_55[m][n] -0.025*len(list(filter(lambda x: (x < 0), running_balances))) # add 0.025 score penalty for each overdrafts
        feedback['stability'].append('Avg of min running balance for last {} days = ${}'.format(length, round(volume, 2)))
        
        return score, feedback

    except Exception as e:
        score = 0
        feedback['stability'].append("{} {} in {}(): {}".format(warning, e.__class__, stability_min_running_balance.__name__, e))
        return score, feedback




# -------------------------------------------------------------------------- #
#                            Metric #4 Diversity                             #
# -------------------------------------------------------------------------- #



def diversity_acc_count(tx, feedback):
    """
    returns score based on count of accounts owned by the user and account duration
    
            Parameters:
                tx (dict): Plaid 'Transactions' product 

            Returns:
                score (float): score for accounts count
    """
    try:
        oldest_tx = datetime.strptime(tx['transactions'][-1]['date'], '%Y-%m-%d').date()
        how_long = (datetime.today().date() - oldest_tx).days

        m = np.digitize(len(tx['accounts']), [i+2 for i in count0], right=False)
        n = np.digitize(how_long, duration, right=True)
        score =  m3x7_73_17[m][n]
        feedback['diversity'].append('User owns a tot of {} different bank accounts'.format(len(tx['accounts'])))

        return score, feedback

    except Exception as e:
        score = 0
        feedback['diversity'].append("{} {} in {}(): {}".format(warning, e.__class__, diversity_acc_count.__name__, e))
        return score, feedback




def diversity_profile(tx, feedback):
    """
    returns score for number of saving and investment accounts owned
    
            Parameters:
                tx (dic): Plaid 'Transactions' product 

            Returns:
                score (float): points scored for accounts owned
    """
    try:
        myacc = list()

        acc = [x for x in tx['accounts'] if x['type']=='loan' or int(x['balances']['current'] or 0) != 0] # exclude $0 balance accounts

        balance = 0
        for a in acc:
            id = a['account_id']
            type = "{}_{}".format(a['type'], str(a['subtype']))

            # Account for savings, hda, cd, money mart, paypal, prepaid, cash management, edt accounts
            if (type.split('_')[0]=='depository') & (type.split('_')[1]!='checking'): 
                balance += int(a['balances']['current'] or 0)
                myacc.append(id)

            # Account for ANY type of investment account
            if type.split('_')[0] == 'investment': 
                balance += int(a['balances']['current'] or 0)
                myacc.append(id)

        if balance != 0:
            score = fico_medians[np.digitize(balance, volume_invest, right=True)]
            feedback['diversity'].append('User owns {} saving accounts with cum balance now = ${}'.format(len(myacc), balance))
        else:
            score = 0
            feedback['diversity'].append('no investing nor saving accounts')

        return score, feedback

    except Exception as e:
        score = 0
        feedback['diversity'].append("{} {} in {}(): {}".format(warning, e.__class__, diversity_profile.__name__, e))
        return score, feedback
