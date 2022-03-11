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

def nested_dict(d, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def net_flow(txn, timeframe, feedback):
    '''
    Description:
        Returns monthly net flow (income - expenses)
    
    Parameters:
        txn (list): transactions history of above-listed accounts
        timeframe (str): length in months of transaction history
        feedback (dict): score feedback

    Returns:
        flow (dataframe): net monthly flow by datetime
    '''

    try:
        accepted_types = {
                'income': ['fiat_deposit', 'request', 'sell', 'send_credit'],
                'expense': ['fiat_withdrawal', 'vault_withdrawal', 'buy', 'send_debit']
                }
        
        income = [(datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ'), abs(float(d['native_amount']['amount']))) for d in txn if d['type'] in accepted_types['income']]
        expense = [(datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ'), -abs(float(d['native_amount']['amount']))) for d in txn if d['type'] in accepted_types['expense']]
        net_flow = income + expense

        df = pd.DataFrame(net_flow, columns=['created_at','amount'])
        df = df.set_index('created_at')
        
        if len(df.index) > 0:
            df = df.groupby(pd.Grouper(freq='M')).sum()

            # exclude current month
            if df.iloc[-1,].name.strftime('%Y-%m') == now.strftime('%Y-%m'):
                df = df[:-1]
            
            # filter by timeframe (months)
            df = df[-timeframe:]

        else:
            raise Exception('No consistent net flow')
    
    except Exception as e:
        df = pd.DataFrame()
        feedback['liquidity']['error'] = str(e)
        
    finally:
        return df, feedback

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
        # Assign max score as long as the user owns some credible non-zero balance accounts with some transaction history
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
        # Retrieve creation date of oldest user account
        if acc:
            oldest = min([d['created_at'] for d in acc])
            # age (in days) of longest standing Coinbase account
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
        # Calculate tot balance now
        if acc:
            balance = sum([d['native_balance']['amount'] for d in acc])
            # Calculate score
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
    '''
    Description:
        A score based on the average running balance maintained for the past 12 months
    
    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        txn (list): transactions history of above-listed accounts

    Returns:
        score (float): score gained for mimimum running balance
        feedback (dict): score feedback
    '''

    try:
        if txn:
            balance = sum([d['native_balance']['amount'] for d in acc])
            
            # Calculate net flow (i.e, |income-expenses|) each month for past 12 months
            net, feedback = net_flow(txn, 12, feedback)

            # Iteratively subtract net flow from balancenow to calculate the running balance for the past 12 months
            net = net['amount'].tolist()[::-1]
            net = [n+balance for n in net]
            size = len(net)

            # Calculate volume using a weighted average
            weights = np.linspace(0.1, 1, len(net)).tolist()[::-1]
            volume = sum([x*w for x,w in zip(net, weights)]) / sum(weights)
            length = size*30
            
            # Compute the score
            if volume < 500:
                score = 0.01
            else:
                m = np.digitize(volume, volume_balance_now, right=True) 
                n = np.digitize(length, duration, right=True)
                # Get the score and add 0.025 score penalty for each 'overdraft'
                score = m7x7_85_55[m][n] -0.025 * len(list(filter(lambda x: (x < 0), net))) 
                
            feedback['liquidity']['avg_running_balance'] = round(volume, 2)
            feedback['liquidity']['balance_timeframe(months)'] = size
        
        else:
            # If the account has no transaction history, get a score = 0, and raise exception
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
    '''
    Description:
        A score based on the count and volume of credit OR debit transactions across user's Coinbase accounts
    
    Parameters:
        txn (list): transactions history of non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        type (str): accepts 'credit' or 'debit'

    Returns:
        score (float): score gained for count and volume of credit transactions
        feedback (dict): score feedback
    '''

    try:
        # Calculate total volume of credit OR debit and txn counts
        if txn:
            accepted_types = {
                'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'],
                'debit': ['fiat_withdrawal', 'vault_withdrawal', 'sell', 'send_debit']
                }
            
            typed_txn = [float(d['native_amount']['amount']) for d in txn if d['type'] in accepted_types[type]]
            balance = sum(typed_txn)

            m = np.digitize(len(typed_txn), count_cred_deb_txn, right=True)
            n = np.digitize(balance, volume_balance_now, right=True)
            score = m7x7_03_17[m][n]

            nested_dict(feedback, ['activity', type, 'balance'], balance)
        
        else:
            raise Exception('no transaction history')
    
    except Exception as e:
        score = 0
        feedback['activity']['error'] = str(e)
        
    finally:
        return score, feedback

@measure_time_and_memory
def activity_consistency(txn, type, feedback):
    '''
    Description:
        A score based on the the weigthed monthly average credit OR debit volume over time
    
    Parameters:
        txn (list): transactions history of non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        type (str): accepts 'credit' or 'debit'

    Returns:
        score (float): score for consistency of credit OR debit weighted avg monthly volume
        feedback (dict): score feedback
    '''

    try:
        if txn:
            # Declate accepted transaction types
            accepted_types = {
                'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'],
                'debit': ['fiat_withdrawal', 'vault_withdrawal', 'sell', 'send_debit']
                }

            # Filter by transaction type and keep txn amounts and dates
            typed_txn = [(datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ'), float(d['native_amount']['amount'])) for d in txn if d['type'] in accepted_types[type]]
            df = pd.DataFrame(typed_txn, columns=['created_at','amount'])
            df = df.set_index('created_at')
            df = df.groupby(pd.Grouper(freq='M')).sum()
            df = df[-12:]
            df = df[df['amount']!=0]
            
            if len(df.index) > 0:
                weights = np.linspace(0.1, 1, len(df))
                w_avg = sum(np.multiply(df['amount'], weights)) / sum(weights)
                length = len(df.index)*30

                m = np.digitize(w_avg, volume_profit*1.5, right=True)
                n = np.digitize(length, duration, right=True)
                score = m7x7_85_55[m][n]

                nested_dict(feedback, ['activity', type, 'weighted_avg_volume'], w_avg)
                nested_dict(feedback, ['activity', type, 'timeframe(days)'], length)

            else:
                # If the account has no transaction history, get a score = 0, and raise exception
                raise Exception('no transaction history')
        
        else:
            raise Exception('no transaction history')

    except Exception as e:
        score = 0
        feedback['activity']['error'] = str(e)
        
    finally:
        return score, feedback

@measure_time_and_memory
def activity_profit_since_inception(acc, txn, feedback):
    '''
    Description:
        A score based on total user profit since account inception. We define net profit as:
            net profit = (tot withdrawals) + (tot Coinbase balance now) - (tot injections into your wallet)
    
    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        txn (list): transactions history of above-listed accounts

    Returns:
        score (int): for user total net profit thus far
        feedback (dict): score feedback
    '''

    try:
        accepted_types = {
                'credit': ['fiat_deposit', 'request', 'buy', 'send_credit'],
                'debit': ['fiat_withdrawal', 'vault_withdrawal', 'send_debit']
                }                                                        

        # Calculate total credited volume and withdrawn volume
        balance = sum([d['native_balance']['amount'] for d in acc])
        credits = sum([float(d['native_amount']['amount']) for d in txn if d['type'] in accepted_types['credit']])
        debits = sum([float(d['native_amount']['amount']) for d in txn if d['type'] in accepted_types['debit']])
        
        profit = (balance - credits) + debits
        
        if profit == 0:
            raise Exception('no net profit')
        else:
            score = fico_medians[np.digitize(profit, volume_profit, right=True)]

            feedback['activity']['total_net_profit'] = round(profit, 2)

    except Exception as e:
        score = 0
        feedback['activity']['error'] = str(e)
        
    finally:
        return score, feedback
