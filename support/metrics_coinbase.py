from datetime import datetime
import pandas as pd
import numpy as np

from optimization.performance import *

now = datetime.now().date()

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

def net_flow(txn, how_many_months, feedback):
    """
    returns monthly net flow (income-expenses)

            Parameters:
                txn (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts
                how_many_month (float): how many months of transaction history are you considering? 
        
            Returns: 
                flow (df): pandas dataframe with amounts for net monthly flow and datetime index
    """
    try: 
        # If the account has no transaction history, return an empty flow
        # Otherwise, compute the net flow
        if not txn:
            flow = pd.DataFrame(data={'amounts':[]})
            feedback['liquidity'].append('no txn history')

        else:
            dates = list()
            amounts = list()
            types = {'income': ['fiat_deposit', 'request', 'sell', 'send_credit'],
                        'expense': ['fiat_withdrawal', 'vault_withdrawal', 'buy', 'send_debit']} 
            # Store all transactions (income and expenses) in a pandas df
            for t in txn:

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
#                                 Metric #1 KYC                              #
# -------------------------------------------------------------------------- #  
@measure_time_and_memory
def kyc(acc, txn, feedback):
    '''
    Description:
        A score based on Coinbase KYC verification process
    
    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        txn (list): transactions history of above-listed accounts

    Returns:
        score (int): binary kyc verification
        feedback (dict): score feedback
    '''

    try:
        if acc and txn: 
            score = 1
            feedback['kyc']['verified'] = True
        else:
            score = 0
            feedback['kyc']['verified'] = False
        
    except Exception as e:
        score = 0
        feedback['kyc']['error'] = str(e)
        
    finally:
        return score, feedback

# -------------------------------------------------------------------------- #
#                               Metric #2 History                            #
# -------------------------------------------------------------------------- #  
@measure_time_and_memory
def history_acc_longevity(acc, feedback):
    '''
    Description:
        A score based on the longevity of user's best Coinbase accounts
    
    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation

    Returns:
        score (float): score gained based on account longevity
        feedback (dict): score feedback
    '''

    try:
        if acc:
            oldest = min([datetime.strptime(d['created_at'],'%Y-%m-%dT%H:%M:%SZ').date() for d in acc])
            age = (now - oldest).days
            score = fico_medians[np.digitize(age, duration, right=True)]

            feedback['history']['wallet_age(days)'] = age
        else:
            raise Exception('unknown account longevity')
    
    except Exception as e:
        score = 0
        feedback['history']['error'] = str(e)
        
    finally:
        return score, feedback

# -------------------------------------------------------------------------- #
#                             Metric #3 Liquidity                            #
# -------------------------------------------------------------------------- #  
@measure_time_and_memory
def liquidity_tot_balance_now(acc, feedback):
    '''
    Description:
        A score based on cumulative balance of user's accounts
    
    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation

    Returns:
        score (float): score gained based on cumulative balance across accounts
        feedback (dict): score feedback
    '''
    
    try:
        if acc:
            balance = sum([float(d['native_balance']['amount']) for d in acc])
            if balance == 0:
                score = 0

            elif balance < 500 and balance !=0:
                score = 0.01

            else:
                score = fico_medians[np.digitize(balance, volume_balance_now, right=True)]
                
            feedback['liquidity']['current_balance'] = round(balance, 2)
        else:
            raise Exception('no balance')
        
    except Exception as e:
        score = 0
        feedback['liquidity']['error'] = str(e)
        
    finally:
        return score, feedback

@measure_time_and_memory
def liquidity_avg_running_balance(acc, txn, feedback):
    """
    returns score based on the average running balance maintained for the past 12 months

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)
                txn (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts

            Returns:
                score (float): score gained for mimimum running balance
    """
    try:
        if txn:
            # Calculate net flow (i.e, |income-expenses|) each month for past 12 months 
            nets = net_flow(txn, 12, feedback)['amounts'].tolist()
            
            balance = sum([float(d['native_balance']['amount']) for d in acc])

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

        else:
            raise Exception('no transaction history')

    except Exception as e:
        score = 0
        feedback['liquidity']['error'] = str(e)
        
    finally:
        return score, feedback

# -------------------------------------------------------------------------- #
#                             Metric #4 Activity                             #
# -------------------------------------------------------------------------- #  
@measure_time_and_memory
def activity_tot_volume_tot_count(txn, type, feedback):
    """
    returns score for count and volume of credit OR debit transactions across the user's best Coinbase accounts

            Parameters:
                txn (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts
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
        for t in txn:
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
        feedback['activity'].append("{} {} in {}(): {}".format(e.__class__, activity_tot_volume_tot_count.__name__, e))
        return score, feedback

@measure_time_and_memory
def activity_consistency(txn, type, feedback):
    """
    returns score for the weigthed monthly average credit OR debit volume over time

            Parameters:
                txn (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts
                type (str): accepts 'credit' or 'debit'

            Returns:
                score (float): score for consistency of credit OR debit weighted avg monthly volume
    """
    try:
        # If the account has no transaction history, get a score = 0
        if not txn:
            score = 0
        else:
            # Declate accepted transaction types (account for 'send' transactions separately)
            accepted_types = {'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'], \
                'debit': ['fiat_withdrawal', 'vault_withdrawal', 'sell', 'send_debit']}

            # Filter by transaction type and keep txn amounts and dates
            dates = list()
            amounts = list()
            for t in txn:
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
        feedback['activity'].append("{} {} in {}(): {}".format(e.__class__, activity_consistency.__name__, e))
        return score, feedback

@measure_time_and_memory
def activity_profit_since_inception(acc, txn, feedback):
    """
    returns score for total user profit since account inception. We define net profit as:
    net profit = (tot withdrawals) + (tot Coinbase balance now) - (tot injections into your wallet)

            Parameters:
                acc (list): list of non-zero balance accounts owned by the user in currencies of trusted reputation (Coinmarketcap top 15)
                txn (list): user's chronologically ordered transactions (newest to oldest) for user's best accounts

            Returns:
                score (float): score for user total net profit thus far
    """
    try:
        types = {'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'], 
                'withdrawals': ['fiat_withdrawal', 'vault_withdrawal', 'send_debit']} 
                                                                         

        # Calculate total credited volume and withdrawn volume   
        credits = 0
        withdrawals = 0
        for t in txn:
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
        feedback['activity'].append("{} {} in {}(): {}".format(e.__class__, activity_profit_since_inception.__name__, e))
        return score, feedback
