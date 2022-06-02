from testing.performance import *

from datetime import datetime
import pandas as pd
import numpy as np


now = datetime.now().date()

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

        # Store all transactions (income and expenses) in a pandas df
        income = [(datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ'), abs(float(
            d['native_amount']['amount']))) for d in txn if d['type'] in accepted_types['income']]
        expense = [(datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ'), -abs(float(
            d['native_amount']['amount']))) for d in txn if d['type'] in accepted_types['expense']]
        net_flow = income + expense

        df = pd.DataFrame(net_flow, columns=['created_at', 'amount'])
        df = df.set_index('created_at')

        if len(df.index) > 0:
            # bin by month
            df = df.groupby(pd.Grouper(freq='M')).sum()

            # exclude current month
            if df.iloc[-1, ].name.strftime('%Y-%m') == now.strftime('%Y-%m'):
                df = df[:-1]

            # keep only past X-many months. If longer, then crop
            df = df[-timeframe:]

        else:
            raise Exception('no consistent net flow')

    except Exception as e:
        df = pd.DataFrame()
        feedback['liquidity']['error'] = str(e)

    finally:
        return df, feedback

# -------------------------------------------------------------------------- #
#                                 Metric #1 KYC                              #
# -------------------------------------------------------------------------- #


# @measure_time_and_memory
def kyc(acc, txn, feedback):
    '''
    Description:
        A score based on Coinbase KYC verification process

    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        txn (list): transactions history of above-listed accounts
        feedback (dict): score feedback

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


# @measure_time_and_memory
def history_acc_longevity(acc, feedback, duration, fico_medians):
    '''
    Description:
        A score based on the longevity of user's best Coinbase accounts

    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        feedback (dict): score feedback

    Returns:
        score (float): score gained based on account longevity
        feedback (dict): score feedback
    '''

    try:
        # Retrieve creation date of oldest user account
        if acc:
            oldest = min([d['created_at'] for d in acc if d['created_at']])
            # age (in days) of longest standing Coinbase account
            history_acc_longevity.age = (now - oldest).days
            score = fico_medians[np.digitize(
                history_acc_longevity.age, duration, right=True)]

            feedback['history']['wallet_age(days)'] = history_acc_longevity.age
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


# @measure_time_and_memory
def liquidity_tot_balance_now(acc, feedback, volume_balance, fico_medians):
    '''
    Description:
        A score based on cumulative balance of user's accounts

    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        feedback (dict): score feedback

    Returns:
        score (float): score gained based on cumulative balance across accounts
        feedback (dict): score feedback
    '''

    try:
        # Calculate tot balance now
        if acc:
            balance = sum([float(d['native_balance']['amount']) for d in acc])
            # Calculate score
            if balance == 0:
                score = 0

            elif balance < 500 and balance != 0:
                score = 0.01

            else:
                score = fico_medians[np.digitize(
                    balance, volume_balance, right=True)]

            feedback['liquidity']['current_balance'] = round(balance, 2)
        else:
            raise Exception('no balance')

    except Exception as e:
        score = 0
        feedback['liquidity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def liquidity_loan_duedate(txn, feedback, due_date):
    '''
    Description:
        returns how many months it'll take the user to pay back their loan

    Parameters:
        txn (list): transactions history of above-listed accounts
        feedback (dict): score feedback

    Returns:
        feedback (dict): score feedback with a new key-value pair 'loan_duedate':float (# of months in range [3,6])
    '''

    try:
        # Read in the date of the oldest txn
        first_txn = datetime.strptime(
            txn[-1]['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
        txn_length = int((now - first_txn).days/30)  # months

        # Loan duedate is equal to the month of txn history there are
        due = np.digitize(txn_length, due_date, right=True)
        how_many_months = np.append(due_date, 6)

        feedback['liquidity']['loan_duedate'] = how_many_months[due]

    except Exception as e:
        feedback['liquidity']['error'] = str(e)

    finally:
        return feedback


# @measure_time_and_memory
def liquidity_avg_running_balance(acc, txn, feedback, duration, volume_balance, m7x7_85_55):
    '''
    Description:
        A score based on the average running balance maintained for the past 12 months

    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        txn (list): transactions history of above-listed accounts
        feedback (dict): score feedback

    Returns:
        score (float): score gained for mimimum running balance
        feedback (dict): score feedback
    '''

    try:
        if txn:
            balance = sum([float(d['native_balance']['amount']) for d in acc])

            # Calculate net flow (i.e, |income-expenses|) each month for past 12 months
            net, feedback = net_flow(txn, 12, feedback)

            # Iteratively subtract net flow from balance now to calculate the running balance for the past 12 months
            net = net['amount'].tolist()[::-1]
            net = [n+balance for n in net]
            size = len(net)

            # Calculate volume using a weighted average
            weights = np.linspace(0.1, 1, len(net)).tolist()[::-1]
            volume = sum([x*w for x, w in zip(net, weights)]) / sum(weights)
            length = size*30

            # Compute the score
            if volume < 500:
                score = 0.01
            else:
                m = np.digitize(volume, volume_balance, right=True)
                n = np.digitize(length, duration, right=True)
                # Get the score and add 0.025 score penalty for each 'overdraft'
                score = m7x7_85_55[m][n] - 0.025 * \
                    len(list(filter(lambda x: (x < 0), net)))

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


# @measure_time_and_memory
def activity_tot_volume_tot_count(txn, type, feedback, volume_balance, count_txn, m7x7_03_17):
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

            typed_txn = [float(d['native_amount']['amount'])
                         for d in txn if d['type'] in accepted_types[type]]
            balance = sum(typed_txn)

            m = np.digitize(len(typed_txn), count_txn, right=True)
            n = np.digitize(balance, volume_balance, right=True)
            score = m7x7_03_17[m][n]

            nested_dict(feedback, ['activity', type,
                        'tot_volume'], round(balance, 2))

        else:
            raise Exception('no transaction history')

    except Exception as e:
        score = 0
        feedback['activity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def activity_consistency(txn, type, feedback, duration, volume_profit, m7x7_85_55):
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
            activity_consistency.typed_txn = [(datetime.strptime(d['created_at'], '%Y-%m-%dT%H:%M:%SZ'), float(
                d['native_amount']['amount'])) for d in txn if d['type'] in accepted_types[type]]
            df = pd.DataFrame(activity_consistency.typed_txn,
                              columns=['created_at', 'amount'])
            df = df.set_index('created_at')
            activity_consistency.frame = df
            df = df.groupby(pd.Grouper(freq='M')).sum()
            df = df[-12:]
            df = df[df['amount'] != 0]

            if len(df.index) > 0:
                weights = np.linspace(0.1, 1, len(df))
                w_avg = sum(np.multiply(df['amount'], weights)) / sum(weights)
                length = len(df.index)*30

                m = np.digitize(w_avg, volume_profit*1.5, right=True)
                n = np.digitize(length, duration, right=True)
                score = m7x7_85_55[m][n]

                nested_dict(feedback, ['activity', type,
                            'weighted_avg_volume'], round(w_avg, 2))
                nested_dict(feedback, ['activity', type,
                            'timeframe(days)'], length)

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


# @measure_time_and_memory
def activity_profit_since_inception(acc, txn, feedback, volume_profit, fico_medians):
    '''
    Description:
        A score based on total user profit since account inception. We define net profit as:
            net profit = (tot withdrawals) + (tot Coinbase balance now) - (tot injections into your wallet)

    Parameters:
        acc (list): non-zero balance Coinbase accounts owned by the user in currencies of trusted reputation
        txn (list): transaction history of above-listed accounts

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
        balance = sum([float(d['native_balance']['amount']) for d in acc])
        credits = sum([float(d['native_amount']['amount'])
                      for d in txn if d['type'] in accepted_types['credit']])
        debits = sum([float(d['native_amount']['amount'])
                     for d in txn if d['type'] in accepted_types['debit']])

        profit = (balance - credits) + debits
        activity_profit_since_inception.profit = profit

        if profit == 0:
            raise Exception('no net profit')
        else:
            score = fico_medians[np.digitize(
                profit, volume_profit, right=True)]

            feedback['activity']['total_net_profit'] = round(profit, 2)

    except Exception as e:
        score = 0
        feedback['activity']['error'] = str(e)

    finally:
        return score, feedback
