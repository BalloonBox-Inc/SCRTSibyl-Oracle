# Import libraries
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from coinbase.wallet.client import Client
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

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
# We encourage developers who fork this project to alter both scoring grids and categorical bins to best suit their use case
# The SCRTSybil Credit Score Oracle returns 2 outputs:
# 1. score (float): a numerical score 
# 2. feedback (dict): a qualitative description of the score


# Initialize our qualitative score feedback (dict).
# feedback = {'data_fetch': [], 'kyc': [], 'history': [], 'liquidity': [], 'activity': []}
warning = 'WARNING: Error occured during computation. Your score was rounded down for error handling. Retry later.'


# Categorical bins
duration = np.array([90, 120, 150, 180, 210, 270])                               #bins: 0-90 | 91-120 | 121-150 | 151-180 | 181-270 | >270 days
volume_balance_now = np.array([5000, 6500, 8500, 11000, 13000, 15000])
volume_profit = np.array([500, 1000, 2000, 2500, 3000, 4000])
count_cred_deb_txn = np.array([10, 20, 30, 35, 40, 50])

# Scoring grids
# naming convention: shape+denominator, m7x7+Scalars+1.3+1.17 -> m7x7_03_17
# naming convention: shape+denominator, m7x7+Scalars+1.85+1.55 -> m7x7_85_55
m7x7_03_17 = build_2D_matrix_by_rule((7,7), (1/3.03, 1/1.17))
m7x7_85_55 = build_2D_matrix_by_rule((7,7), (1/1.85, 1/1.55))
fico = (np.array([300, 500, 560, 650, 740, 800, 870])-300)/600  # Fico score binning - normalized
fico_medians = [round(fico[i]+(fico[i+1]-fico[i])/2, 2) for i in range(len(fico)-1)] # Medians of Fico scoring bins
fico_medians.append(1)
fico_medians = np.array(fico_medians)


# Make all scoring grids immutable
# (i.e., you can append new elements to the array but you can't rewrite its data, because the array is now read-only)
duration.flags.writeable = False
volume_balance_now.flags.writeable = False
volume_profit.flags.writeable = False
count_cred_deb_txn.flags.writeable = False
m7x7_03_17.flags.writeable = False
m7x7_85_55.flags.writeable = False
fico_medians.flags.writeable = False




# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #
def top_currencies(coinmarketcap_key, coinbase_api_key, coinbase_api_secret, feedback):
    """
    returns a list of all fiat currencies and top 15 cryptos. The functions uses 2 APIs:
    - a Coinmarketcap API to get top 15 cryptos by market capitalization
    - a Coinbase API to get all fiat currencies supported for trading on Coinbase
    This function merges the fetched results in a unified dictionary
    
            Parameters:
                coinmarketcap_key (str): bearer token to authenticate into c|oinmarketcap API
                coinbase_api_key (str): user's Coinbase APIKey
                coinbase_api_secret (str): user's Coinbase APISecretKey
               
            Returns:
                 top_coins (dict): ticker-value pairs for top 15 cryptos and ALL Coinbase fiat currencies         
    """
    try:
        # COINMARKETCAP
        # Define agrs for coinmarketcap API
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        
        parameters = {
        'start':'1',
        'limit':'15',
        'convert':'USD'
        }
        headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': coinmarketcap_key, # You'll need to create our own user API + Secret
        }
        
        session = Session()
        session.headers.update(headers)

        # Run GET task to fetch best cryptos from coinmarketcap API
        response = session.get(url, params=parameters)
        data = json.loads(response.text)

        # Keep top 15 cryptos (ticker and USD-value)
        top_coins = {}
        for t in data['data']:
            top_coins[t['symbol']]=t['quote']['USD']['price']



        # COINBASE
        # Get all coinbase fiat currencies
        client = Client(coinbase_api_key, coinbase_api_secret)
        currencies = client.get_currencies() 
        # List tickers of fiat currencies whose minimum size is ≠ than 1 cent
        odd_fiats = ['BHD', 'BIF', 'BYR', 'CLP', 'DJF', 'GNF', 'HUF', 'IQD', 'ISK', 'JOD', 'JPY', 'KMF', 'KRW', \
            'KWD', 'LYD', 'MGA', 'MRO', 'OMR', 'PYG', 'RWF', 'TND', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']
        
        # Keep only fiat currencies
        fiat_only = {}
        for c in currencies['data']:
            #hack for getting fiat-only types, including some fiat currencies whose smallest unit is ≠ than 1 cent
            if c['min_size']=='0.01000000' or c['id'] in odd_fiats: 
                fiat_only[c['id']]=1

        # Append all fiat currencies to dictionary of top cryptocurrencies
        top_coins.update(fiat_only)
        return top_coins

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, top_currencies.__name__, e))
        




def filter_acc(coinbase_api_key, coinbase_api_secret, top_coins, feedback):
   """
   returns list of accounts with balance > $0 and with currency type in the top 15.
   Current balances are reported both in native currency and in USD for each account.

         Parameters:
            coinbase_api_key (str): user's Coinbase APIKey
            coinbase_api_secret (str): user's Coinbase APISecretKey
            top_coins (dict): lits of top 15 Coinmarketcap crypto plus ALL fiat currencies supported by Coinbase

         Returns:
            user_top_acc (list of dict): list of all accounts with positive balance in USD and holding a well-established currency
   """
   try:
      # Check what currency is currently set as default 'native currency' in the user's Coinbase account
      client = Client(coinbase_api_key, coinbase_api_secret)
      native_currency = client.get_current_user()['native_currency']
      
      # If the 'native curreny' is set to something other than USD, 
      # then change that setting temporarily
      # Get your filtered accounts
      if native_currency != 'USD':
         client.update_current_user(native_currency='USD')
         accounts = client.get_accounts()
         # Reset native_currency to its original setting
         client.update_current_user(native_currency=native_currency) 

      # If the 'native curreny' is already set to USD, 
      # then simply fetch the account data
      else:
         accounts = client.get_accounts()

      # Keep only accounts with non-zero balance AND accounts 
      # whose currency is in the list of top_coins
      user_top_acc = list()
      for a in accounts['data']:
         if (float(a['native_balance']['amount'])!=0) & (a['currency'] in list(top_coins.keys())):
         #if a['currency'] in list(top_coins.keys()):  #REMOVE this line eventually
            user_top_acc.append(a)
      return user_top_acc

   except Exception as e:
      feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, filter_acc.__name__, e))





def filter_tx(coinbase_api_key, coinbase_api_secret, user_top_acc, feedback):
   """
   returns list of transactions occurred in the user's best Coinbase accounts

         Parameters:
            coinbase_api_key (str): user's Coinbase APIKey
            coinbase_api_secret (str): user's Coinbase APISecretKey
            user_top_accounts (list): lits of user's top accounts holding reputable currencies 

         Returns:
            txs (list of dict): list of chronologically ordered transactions in user accounts (from most recent to oldest)
   """
   try:
      client = Client(coinbase_api_key, coinbase_api_secret)
      native_currency = client.get_current_user()['native_currency']

      txs = list()
      # Loop through all Coinbase accounts owned by the user
      # Get your filtered transactions for each of those accounts
      
      if native_currency != 'USD':
         client.update_current_user(native_currency='USD')
         for id in [x['id'] for x in user_top_acc]: 
            tx = client.get_transactions(id) 
            txs.append(tx['data'])
         # Reset native_currency to its original setting 
         client.update_current_user(native_currency=native_currency)  

      else:
         for id in [x['id'] for x in user_top_acc]:
            tx = client.get_transactions(id)        
            txs.append(tx['data'])
      transactions = [t for acc in txs for t in acc]


      # Filter for completed transactions and accepted transaction types
      filtered_tx = list()
      accepted_types = ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
      for t in transactions:
         if (t['status']=='completed') & (t['type'] in accepted_types):
            filtered_tx.append(t)

      return filtered_tx

   except Exception as e:
      feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, filter_tx.__name__, e))





def refactor_send_tx(tx, feedback):
   """
   returns list of transactions after re-labeling all 'send' type transactions either into 'send_credit' or into 'send_debit'

         Parameters:
            tx (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts

         Returns:
            tx (list of dict): list of chronologically ordered transactions in user accounts (from most recent to oldest)
   """
   try:
      new_tx = list()
      for t in tx:

         # If the txn is of 'send' type and is a credit, then relabel its type to 'send_credit'
         if (t['type'] == 'send') & (np.sign(float(t['amount']['amount'])) == 1):
            t['type'] = 'send_credit'

         # If the txn is of 'send' type and is a debit, then relabel its type to 'send_debit'   
         elif (t['type'] == 'send') & (np.sign(float(t['amount']['amount'])) == -1):
            t['type'] = 'send_debit'
            
         # If it's not a 'send' transaction, then move on
         else:
            pass

         new_tx.append(t)

      return new_tx
      
   except Exception as e:
      feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, refactor_send_tx.__name__, e))





def net_flow(tx, how_many_months, feedback):
    """
    returns monthly net flow (income-expenses)

            Parameters:
                tx (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts
                how_many_month (float): how many months of transaction history are you considering? 
        
            Returns: 
                flow (df): pandas dataframe with amounts for net monthly flow and datetime index
    """
    try: 
        # If the account has no transaction history, return an empty flow
        # Otherwise, compute the net flow
        if not tx:
            flow = pd.DataFrame(data={'amounts':[]})
            feedback['liquidity'].append('no txn history')

        else:
            dates = list()
            amounts = list()
            types = {'income': ['fiat_deposit', 'request', 'sell', 'send_credit'],
                        'expense': ['fiat_withdrawal', 'vault_withdrawal', 'buy', 'send_debit']} 
            # Store all transactions (income and expenses) in a pandas df
            for t in tx:

                if t['type'] in types['income']:
                    amount = abs(float(t['native_amount']['amount']))
                    amounts.append(amount)
                    date = datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    dates.append(date)

                elif t['type'] in types['expense']:
                    amount = -abs(float(t['native_amount']['amount']))
                    amounts.append(amount)
                    date = datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    dates.append(date)

                else:
                    pass

            df = pd.DataFrame(data={'amounts':amounts}, index=pd.DatetimeIndex(dates))

            if len(df.index) > 0 :
                # Bin by month
                flow = df.groupby(pd.Grouper(freq='M')).sum()

                # Exclude current month
                if flow.iloc[-1,].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
                    flow = flow[:-1] 

                # Keep only past X-many months. If longer, then crop
                daytoday = datetime.today().date().day
                lastmonth = datetime.today().date() - pd.offsets.DateOffset(days=daytoday)
                yearago = lastmonth - pd.offsets.DateOffset(months=how_many_months)
                if yearago in flow.index:
                    flow = flow[flow.index.tolist().index(yearago):]
            else:
                feedback['history'].append('No throughput data in fn {}()'.format(net_flow.__name__))
                flow = pd.DataFrame({'amounts':[]})

        return flow

    except Exception as e:
        feedback['liquidity'].append("{} in {}(): {}".format(e.__class__, net_flow.__name__, e))




# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                 -local data-                               #
# -------------------------------------------------------------------------- #
# Eventually remove this next function, which is merely used to import local json data to test the Coinbase model during development phase. 
def local_get_data(path_dir, userid, top_coins, feedback):
    """
    returns the Coinbase json data for the accounts and the transactions of one user

            Parameters:
                path_dir (str): path to the local directory where the Coinbase files are stored
                userid (str): number of the user you want to retrieve account and transaction data for
                top_coins (dict): dictionary of ticker-nominalvalue pairs of the top cryptos and fiat currencies featured on Coinmarketcap and Coinbase
        
            Returns: 
                acc (dict): all accounts owned by the user
                tx (dict): with transactions of all user's accoutns in chronological order (newest to oldest)
    """
    try:
        # Iterate through all files in a directory
        directory = os.fsencode(path_dir)
        coinbase_files = list()
        for f in os.listdir(directory):
            filename = os.fsdecode(f)
            coinbase_files.append(filename) #append file names to list
        coinbase_files =  sorted(coinbase_files) 

        # Select one user and retrieve the lits of their accounts and their transaction history
        for f in coinbase_files:
            if f.startswith("{}_acc".format(userid)): #choose your user
                acc = json.load(open(path_dir+f))['data'] #open json
            if f.startswith("{}_tx".format(userid)): #choose your user
                tx = json.load(open(path_dir+f))['data'] #open json
                
        # Filter accounts        
        filtered_acc = list()
        for a in acc:
            # Keep only accounts with non-zero balance AND accounts whose currency is in the list of top_coins
            if float(a['balance']['amount'])!=0 and a['currency'] in list(top_coins.keys()):
                filtered_acc.append(a)

        # Filter transactions
        filtered_tx = list()
        accepted_types = ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
        for t in tx:
            if (t['amount']['currency'] in list(top_coins.keys())) & (t['status']=='completed') & (t['type'] in accepted_types):
                filtered_tx.append(t)

        return filtered_acc, filtered_tx
    
    except Exception as e:
        feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, local_get_data.__name__, e))




    
def unfiltered_acc(coinbase_api_key, coinbase_api_secret, feedback):
   """
   returns list of accounts with balance > $0 and ANY currency type.
   Current balances are reported both in native currency and in USD for each account.

         Parameters:
            coinbase_api_key (str): user's Coinbase APIKey
            coinbase_api_secret (str): user's Coinbase APISecretKey

         Returns:
            user_top_acc (list of dict): list of all accounts with positive balance in USD and holding a well-established currency
   """
   try:
      # Check what currency is currently set as default 'native currency' in the user's Coinbase account
      client = Client(coinbase_api_key, coinbase_api_secret)
      native_currency = client.get_current_user()['native_currency']
      
      # If the 'native curreny' is set to something other than USD, 
      # then change that setting temporarily
      # Get your filtered accounts
      if native_currency != 'USD':
         client.update_current_user(native_currency='USD')
         accounts = client.get_accounts()
         # Reset native_currency to its original setting
         client.update_current_user(native_currency=native_currency) 

      # If the 'native curreny' is already set to USD, 
      # then simply fetch the account data
      else:
         accounts = client.get_accounts()

      # Keep only accounts with non-zero balance
      user_top_acc = list()
      for a in accounts['data']:
         if (float(a['native_balance']['amount'])!=0):
            user_top_acc.append(a)
      return user_top_acc

   except Exception as e:
      feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, unfiltered_acc.__name__, e))





def unfiltered_tx(coinbase_api_key, coinbase_api_secret, user_top_acc, feedback):
   """
   returns list of transactions occurred in ALL of user's accounts

         Parameters:
            coinbase_api_key (str): user's Coinbase APIKey
            coinbase_api_secret (str): user's Coinbase APISecretKey
            user_top_accounts (list): lits of ALL user's accounts

         Returns:
            tsx (list of dict): list of chronologically ordered transactions in user accounts (from most recent to oldest)
   """
   try:
      client = Client(coinbase_api_key, coinbase_api_secret)
      native_currency = client.get_current_user()['native_currency']

      txs = list()
      # Loop through all Coinbase accounts owned by the user
      # Get your filtered transactions for each of those accounts
      
      if native_currency != 'USD':
         client.update_current_user(native_currency='USD')
         for id in [x['id'] for x in user_top_acc]: 
            tx = client.get_transactions(id) 
            txs.append(tx['data'])
         # Reset native_currency to its original setting 
         client.update_current_user(native_currency=native_currency)  

      else:
         for id in [x['id'] for x in user_top_acc]:
            tx = client.get_transactions(id)        
            txs.append(tx['data'])
      transactions = [t for acc in txs for t in acc]


      # Filter for completed transactions and accepted transaction types
      filtered_tx = list()
      accepted_types = ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
      for t in transactions:
         if (t['status']=='completed') & (t['type'] in accepted_types):
            filtered_tx.append(t)

      return filtered_tx

   except Exception as e:
      feedback['data_fetch'].append("{} in {}(): {}".format(e.__class__, unfiltered_tx.__name__, e))



# -------------------------------------------------------------------------- #
#                                 Metric #1 KYC                              #
# -------------------------------------------------------------------------- #  

def kyc(acc, tx, feedback):
    """
    checks whether user got correctly kyc'ed on Coinbase and assign binary score appropriately

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)
                tx (list): historical of user transactions for his above-listed best accounts

            Returns:
                score (float): binary value 0-1 based on whether user is kyc'ed or not
    """
    try:
        # Assign max score as long as the user owns some credible non-zero balance accounts with some transaction history
        if acc and tx: 
            score = 1
            feedback['kyc'].append('yes kyc!')
        else: 
            score = 0
            feedback['kyc'].append('no kyc')
        return score, feedback
        
    except Exception as e:
        score = 0
        feedback['kyc'].append("{} {} in {}(): {}".format(warning, e.__class__, kyc.__name__, e))
        return score, feedback


# -------------------------------------------------------------------------- #
#                               Metric #2 History                            #
# -------------------------------------------------------------------------- #  

def history_acc_longevity(acc, feedback):
    """
    returns a score dependent on the longevity of user's best Coinbase accounts

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)

            Returns:
                score (float): score gained based on account longevity
    """
    try:    
        # Retrieve creation date of oldest user account
        issuance_dates = []
        if acc:
            for a in acc:
                if a['created_at']:
                    d = datetime.strptime(a['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
                    issuance_dates.append(d)
                else:
                    pass

            now = datetime.now().date()
            if len(issuance_dates) == 1:
                oldest = issuance_dates[0]
            else:
                oldest = min(issuance_dates)
            length = (now-oldest).days #duration (in days) of longest standing Coinbase account
            score = fico_medians[np.digitize(length, duration, right=True)]
            feedback['history'].append('duration of longest standing wallet = {} days'.format(length))

        else:
            score = 0
            feedback['history'].append('unknown account longevity')

        return score, feedback

    except Exception as e:
        score = 0
        feedback['history'].append("{} {} in {}(): {}".format(warning, e.__class__, history_acc_longevity.__name__, e))
        return score, feedback



# -------------------------------------------------------------------------- #
#                             Metric #3 Liquidity                            #
# -------------------------------------------------------------------------- #  

def liquidity_tot_balance_now(acc, feedback):
    """
    returns the cumulative current balance of a user across ALL his accounts

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)

            Returns:
                score (float): score gained based on the cumulative balance now
    """
    try:
        # Calculate tot balance now
        balance = 0
        for a in acc:
            balance += float(a['native_balance']['amount'])

        # Calculate score
        if balance == 0:
            score = 0

        elif balance < 500 and balance !=0:
            score = 0.01

        else:
            score = fico_medians[np.digitize(balance, volume_balance_now, right=True)]
            
        feedback['liquidity'].append('tot balance now = ${}'.format(round(balance, 2)))


        return score, feedback
        
    except Exception as e:
        score = 0
        feedback['liquidity'].append("{} {} in {}(): {}".format(warning, e.__class__, liquidity_tot_balance_now.__name__, e))
        return score, feedback


        
def liquidity_avg_running_balance(acc, tx, feedback):
    """
    returns score based on the average running balance maintained for the past 12 months

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)
                tx (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts

            Returns:
                score (float): score gained for mimimum running balance
    """
    try:
        # If the account has no transaction history, get a score = 0
        if not tx:
            score = 0
            feedback['liquidity'].append('no transaction history , hence cannot calculate avg_running_balance')
        else:
            # Calculate net flow (i.e, |income-expenses|) each month for past 12 months 
            nets = net_flow(tx, 12, feedback)['amounts'].tolist()

            # Calculate tot current balance now
            balance = 0
            for a in acc:
                balance += float(a['native_balance']['amount'])

            # Iteratively subtract net flow from balancenow to calculate the running balance for the past 12 months
            running_balances = list()
            for n in reversed(nets):
                balance = balance + n
                running_balances.append(round(balance, 2)) 

            # Calculate volume using a weighted average
            weights = np.linspace(0.1, 1, len(running_balances)).tolist() # Define your weights
            volume = sum([x*w for x,w in zip(running_balances, reversed(weights))]) / sum(weights) 
            length = len(running_balances) * 30

            # Compute the score
            if volume < 500:
                score = 0.01
            else:
                m = np.digitize(volume, volume_balance_now, right=True) 
                n = np.digitize(length, duration, right=True)
                # Get the score and add 0.025 score penalty for each 'overdraft'
                score = m7x7_85_55[m][n] -0.025 * len(list(filter(lambda x: (x < 0), running_balances))) 
                feedback['liquidity'].append('avg running balance for last {} months = ${}'.format(len(running_balances), round(volume, 2)))

        return score, feedback

    except Exception as e:
        score = 0
        feedback['liquidity'].append("{} {} in {}(): {}".format(warning, e.__class__, liquidity_avg_running_balance.__name__, e))
        return score, feedback


# -------------------------------------------------------------------------- #
#                             Metric #4 Activity                             #
# -------------------------------------------------------------------------- #  

def activity_tot_volume_tot_count(tx, type, feedback):
    """
    returns score for count and volume of credit OR debit transactions across the user's best Coinbase accounts

            Parameters:
                tx (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts
                type (str): accepts 'credit' or 'debit'

            Returns:
                score (float): score gained for count and volume of credit transactions 
    """
    try:
        accepted_types = {'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'], \
            'debit': ['fiat_withdrawal', 'vault_withdrawal', 'sell', 'send_debit']}

        # Calculate total volume of credit OR debit and txn counts    
        volume = 0
        count = 0
        for t in tx:
            if t['type'] in accepted_types[type]:
                volume += float(t['native_amount']['amount'])
                count += 1

        # Calculate score
        m = np.digitize(count, count_cred_deb_txn, right=True)
        n = np.digitize(volume, volume_balance_now, right=True)
        score = m7x7_03_17[m][n]
        return score, feedback
        
    except Exception as e:
        score = 0
        feedback['activity'].append("{} {} in {}(): {}".format(warning, e.__class__, activity_tot_volume_tot_count.__name__, e))
        return score, feedback




def activity_consistency(tx, type, feedback):
    """
    returns score for the weigthed monthly average credit OR debit volume over time

            Parameters:
                tx (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts
                type (str): accepts 'credit' or 'debit'

            Returns:
                score (float): score for consistency of credit OR debit weighted avg monthly volume
    """
    try:
        # If the account has no transaction history, get a score = 0
        if not tx:
            score = 0
        else:
            # Declate accepted transaction types (account for 'send' transactions separately)
            accepted_types = {'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'], \
                'debit': ['fiat_withdrawal', 'vault_withdrawal', 'sell', 'send_debit']}

            # Filter by transaction type and keep txn amounts and dates
            dates = list()
            amounts = list()
            for t in tx:
                if t['type'] in accepted_types[type]:
                    amount = float(t['native_amount']['amount'])
                    amounts.append(amount)
                    date = datetime.strptime(t['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    dates.append(date)
            df = pd.DataFrame(data={'amount':amounts}, index=pd.DatetimeIndex(dates))

            if len(df.index) > 0 :
                # Bin transactions by month and aggregate by sum()
                df1 = df.groupby(pd.Grouper(freq='M')).sum()
                df1 = df1[df1['amount']!=0]
                if len(df1) > 12:  # Keep last 12 months
                    df1 = df1[-12:]

                # Generate an array of given length containing monotonically increasing weights in range [0.1, 1]
                weights = np.linspace(0.1, 1, len(df1))
                # Calculate the weighted average of credit OR debit volume
                w_avg = sum(np.multiply(df1['amount'], weights)) / sum(weights)
                length = len(df1) * 30 # number of months * 30 days/month

                # Calculate the score
                m = np.digitize(w_avg, volume_profit*1.5, right=True)
                n = np.digitize(length, duration, right=True)
                score = m7x7_85_55[m][n]
            else:
                score = 0

        return score, feedback

    except Exception as e:
        score = 0
        feedback['activity'].append("{} {} in {}(): {}".format(warning, e.__class__, activity_consistency.__name__, e))
        return score, feedback




def activity_profit_since_inception(acc, tx, feedback):
    """
    returns score for total user profit since account inception. We define net profit as:
    net profit = (tot withdrawals) + (tot Coinbase balance now) - (tot injections into your wallet)

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)
                tx (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts

            Returns:
                score (float): score for user total net profit thus far
    """
    try:
        types = {'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'], 
                'withdrawals': ['fiat_withdrawal', 'vault_withdrawal', 'send_debit']} 
                                                                         

        # Calculate total credited volume and withdrawn volume   
        credits = 0
        withdrawals = 0
        for t in tx:
            if t['type'] in types['credit']:
                credits += float(t['native_amount']['amount'])
            if t['type'] in types['withdrawals']:
                withdrawals += float(t['native_amount']['amount'])

        # Calculate total available balance now
        balance = 0
        for a in acc:
            balance += float(a['native_balance']['amount'])

        # Calculate net profit since account issuance
        profit = withdrawals + balance - credits

        # Compute the score
        if profit == 0:
            score = 0
        else:
            score = fico_medians[np.digitize(profit, volume_profit, right=True)]
            feedback['activity'].append('net profit since inception = ${}'.format(round(profit, 2)))
        return score, feedback

    except Exception as e:
        score = 0
        feedback['activity'].append("{} {} in {}(): {}".format(warning, e.__class__, activity_profit_since_inception.__name__, e))
        return score, feedback
