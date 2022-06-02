from testing.performance import *

from datetime import timedelta
from datetime import datetime
import pandas as pd
import numpy as np

now = datetime.now().date()


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
# -------------------------------------------------------------------------- #

def dynamic_select(data, acc_name, feedback):
    '''
    dynamically pick the best credit account,
    i.e. the account that performs best in 2 out of these 3 categories:
    highest credit limit / largest txn count / longest txn history

            Parameters:
                data (dict): Plaid 'Transactions' product 
                acc_name (str): acccepts 'credit' or 'checking'
                feedback (dict): feedback describing the score

            Returns: 
                best (str or dict): Plaid account_id of best credit account 
    '''
    try:
        acc = data['accounts']
        txn = data['transactions']

        info = list()
        matrix = []
        for a in acc:
            if acc_name in '{1}{0}{2}'.format('_', str(a['type']), str(a['subtype'])).lower():
                id = a['account_id']
                type = '{1}{0}{2}{0}{3}'.format('_', str(a['type']), str(
                    a['subtype']), str(a['official_name'])).lower()
                limit = int(a['balances']['limit'] or 0)
                transat = [t for t in txn if t['account_id'] == id]
                txn_count = len(transat)
                if len(transat) != 0:
                    length = (now - transat[-1]['date']).days
                else:
                    length = 0
                info.append([id, type, limit, txn_count, length])
                matrix.append([limit, txn_count, length])

        if len(info) != 0:
            # Build a matrix where each column is a different account. Choose the one performing best among the 3 categories
            m = np.array(matrix).T
            m[0] = m[0]*1  # assign 1pt to credit limit
            m[1] = m[1]*10  # assign 10pt to txn count
            m[2] = m[2]*3  # assign 3pt to account length
            cols = [sum(m[:, i]) for i in range(m.shape[1])]
            index_best_acc = cols.index(max(cols))
            best = {'id': info[index_best_acc][0],
                    'limit': info[index_best_acc][2]}
        else:
            best = {'id': 'inexistent', 'limit': 0}

    except Exception as e:
        feedback['fetch'][dynamic_select.__name__] = str(e)
        best = {'id': 'inexistent', 'limit': 0}

    finally:
        return best


def flows(data, how_many_months, feedback):
    '''
    returns monthly net flow

            Parameters:
                data (dict): Plaid 'Transactions' product 
                how_many_month (float): how many months of transaction history are you considering? 
                feedback (dict): feedback describing the score

            Returns: 
                flow (df): pandas dataframe with amounts for net monthly flow and datetime index
    '''
    try:
        acc = data['accounts']
        txn = data['transactions']

        dates = list()
        amounts = list()
        deposit_acc = list()

        # Keep only deposit->checking accounts
        for a in acc:
            id = a['account_id']
            type = '{1}{0}{2}'.format(
                '_', str(a['type']), str(a['subtype'])).lower()
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

            # exclude micro txn and exclude internal transfers
            if abs(t['amount']) > 5 and 'internal account transfer' not in category:
                date = t['date']
                dates.append(date)
                amount = t['amount']
                amounts.append(amount)
        df = pd.DataFrame(data={'amounts': amounts},
                          index=pd.DatetimeIndex(dates))

        # Bin by month
        flow = df.groupby(pd.Grouper(freq='M')).sum()

        # Exclude current month
        if flow.iloc[-1, ].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
            flow = flow[:-1]

        # Keep only past X months. If longer, then crop
        flow.reset_index(drop=True, inplace=True)
        if how_many_months-1 in flow.index:
            flow = flow[-(how_many_months):]

        return flow

    except Exception as e:
        feedback['fetch'][flows.__name__] = str(e)


def balance_now_checking_only(data, feedback):
    '''
    returns total balance available now in the user's checking accounts

            Parameters:
                data (dict): Plaid 'Transactions' product
                feedback (dict): feedback describing the score

            Returns:
                balance (float): cumulative current balance in checking accounts
    '''
    try:
        acc = data['accounts']

        balance = 0
        for a in acc:
            type = '{1}{0}{2}'.format(
                '_', str(a['type']), str(a['subtype'])).lower()
            if type == 'depository_checking':
                balance += int(a['balances']['current'] or 0)

        return balance

    except Exception as e:
        feedback['fetch'][balance_now_checking_only.__name__] = str(e)


# -------------------------------------------------------------------------- #
#                               Metric #1 Credit                             #
# -------------------------------------------------------------------------- #


# @measure_time_and_memory
def credit_mix(data, feedback, duration, count_zero, m3x7_2_4):
    '''
    Description:
        A score based on user's credit accounts composition and status

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns: 
        score (float): gained based on number of credit accounts owned and duration
        feedback (dict): score feedback
    '''

    try:
        credit_mix.credit = [d for d in data['accounts']
                             if d['type'].lower() == 'credit']
        credit_mix.card_names = [d['name'].lower().replace('credit', '').title().strip() for d in credit_mix.credit if (
            isinstance(d['name'], str) == True) and (d['name'].lower() != 'credit card')]

        if credit_mix.credit:
            size = len(credit_mix.credit)

            credit_ids = [d['account_id'] for d in credit_mix.credit]
            credit_txn = [d for d in data['transactions']
                          if d['account_id'] in credit_ids]

            first_txn = credit_txn[-1]['date']
            date_diff = (now - first_txn).days

            m = np.digitize(size, count_zero, right=True)
            n = np.digitize(date_diff, duration, right=True)
            score = m3x7_2_4[m][n]

            feedback['credit']['credit_cards'] = size
            # card_names could be an empty list of the card name was a NoneType
            feedback['credit']['card_names'] = credit_mix.card_names
        else:
            raise Exception('no credit card')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def credit_limit(data, feedback, duration, volume_credit, m7x7_03_17):
    '''
    Description:
        A score for the cumulative credit limit of a user across ALL of his credit accounts

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns: 
        score (float): gained based on the cumulative credit limit across all credit accounts
        feedback (dict): score feedback
    '''

    try:
        credit = [d for d in data['accounts'] if d['type'].lower() == 'credit']

        if credit:
            credit_lim = sum(
                [int(d['balances']['limit']) if d['balances']['limit'] else 0 for d in credit])

            credit_ids = [d['account_id'] for d in credit]
            credit_txn = [d for d in data['transactions']
                          if d['account_id'] in credit_ids]

            first_txn = credit_txn[-1]['date']
            date_diff = (now - first_txn).days

            m = np.digitize(date_diff, duration, right=True)
            n = np.digitize(credit_lim, volume_credit, right=True)
            score = m7x7_03_17[m][n]

            feedback['credit']['credit_limit'] = credit_lim
        else:
            raise Exception('no credit limit')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def credit_util_ratio(data, feedback, duration, credit_util_pct, m7x7_85_55):
    '''
    Description:
        A score reflective of the user's credit utilization ratio, that is credit_used/credit_limit

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns:
        score (float): score for avg percent of credit limit used
        feedback (dict): score feedback
    '''

    try:
        txn = data['transactions']

        # Dynamically select best credit account
        dynamic = dynamic_select(data, 'credit', feedback)

        if dynamic['id'] == 'inexistent' or dynamic['limit'] == 0:
            score = 0

        else:
            id = dynamic['id']
            limit = dynamic['limit']

            # Keep ony transactions in best credit account
            transat = [x for x in txn if x['account_id'] == id]

            if transat:
                dates = list()
                amounts = list()
                for t in transat:
                    date = t['date']
                    dates.append(date)
                    amount = t['amount']
                    amounts.append(amount)
                df = pd.DataFrame(
                    data={'amounts': amounts}, index=pd.DatetimeIndex(dates))

                # Bin by month credit card 'purchases' and 'paybacks'
                util = df.groupby(pd.Grouper(freq='M'))['amounts'].agg([
                    ('payback', lambda x: x[x < 0].sum()),
                    ('purchases', lambda x: x[x > 0].sum())
                ])
                util['cred_util'] = [x/limit for x in util['purchases']]

                # Exclude current month
                if util.iloc[-1, ].name.strftime('%Y-%m') == datetime.today().date().strftime('%Y-%m'):
                    util = util[:-1]

                avg_util = np.mean(util['cred_util'])
                m = np.digitize(len(util)*30, duration, right=True)
                n = np.digitize(avg_util, credit_util_pct, right=True)
                score = m7x7_85_55[m][n]

                feedback['credit']['utilization_ratio'] = round(avg_util, 2)

            else:
                raise Exception('no credit history')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def credit_interest(data, feedback, fico_medians, frequency_interest):
    '''
    returns score based on number of times user was charged credit card interest fees in past 24 months

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns: 
                score (float): gained based on interest charged
                feedback (dict): feedback describing the score
    '''
    try:
        id = dynamic_select(data, 'credit', feedback)['id']

        if id == 'inexistent':
            score = 0

        else:
            txn = data['transactions']
            alltxn = [t for t in txn if t['account_id'] == id]

            interests = list()

            if alltxn:
                length = min(24, round((now - alltxn[-1]['date']).days/30, 0))
                for t in alltxn:

                    # keep only txn of type 'interest on credit card'
                    if 'Interest Charged' in t['category']:
                        date = t['date']

                        # keep only txn of last 24 months
                        if date > now - timedelta(days=2*365):
                            interests.append(t)

                frequency = len(interests)/length
                score = fico_medians[np.digitize(
                    frequency, frequency_interest, right=True)]

                feedback['credit']['count_charged_interest'] = round(
                    frequency, 0)

            else:
                raise Exception('no credit interest')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def credit_length(data, feedback, fico_medians, duration):
    '''
    returns score based on length of user's best credit account

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns: 
                score (float): gained because of credit account duration
                feedback (dict): feedback describing the score
    '''
    try:
        id = dynamic_select(data, 'credit', feedback)['id']
        txn = data['transactions']
        alltxn = [t for t in txn if t['account_id'] == id]

        if alltxn:
            oldest_txn = alltxn[-1]['date']
            # date today - date of oldest credit transaction
            how_long = (now - oldest_txn).days
            score = fico_medians[np.digitize(how_long, duration, right=True)]

            feedback['credit']['credit_duration_(days)'] = how_long

        else:
            raise Exception('no credit length')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def credit_livelihood(data, feedback, fico_medians, count_lively):
    '''
    returns score quantifying the avg monthly txn count for your best credit account

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns: 
                score (float): based on avg monthly txn count
                feedback (dict): feedback describing the score
    '''
    try:
        id = dynamic_select(data, 'credit', feedback)['id']
        txn = data['transactions']
        alltxn = [t for t in txn if t['account_id'] == id]

        if alltxn:
            dates = list()
            amounts = list()

            for i in range(len(alltxn)):
                date = alltxn[i]['date']
                dates.append(date)
                amount = alltxn[i]['amount']
                amounts.append(amount)

            df = pd.DataFrame(data={'amounts': amounts},
                              index=pd.DatetimeIndex(dates))
            d = df.groupby(pd.Grouper(freq='M')).count()
            credit_livelihood.d = d

            if len(d['amounts']) >= 2:
                if d['amounts'][0] < 5:  # exclude initial and final month with < 5 txn
                    d = d[1:]
                if d['amounts'][-1] < 5:
                    d = d[:-1]

            mean = d['amounts'].mean()
            score = fico_medians[np.digitize(mean, count_lively, right=True)]

            feedback['credit']['avg_count_monthly_txn'] = round(mean, 0)

        else:
            raise Exception('no credit transactions')

    except Exception as e:
        score = 0
        feedback['credit']['error'] = str(e)

    finally:
        return score, feedback

# -------------------------------------------------------------------------- #
#                            Metric #2 Velocity                              #
# -------------------------------------------------------------------------- #


# @measure_time_and_memory
def velocity_withdrawals(data, feedback, count_zero, volume_withdraw, m3x7_73_17):
    '''
    returns score based on count and volumne of monthly automated withdrawals

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns: 
                score (float): score associated with reccurring monthly withdrawals
                feedback (dict): feedback describing the score
    '''
    try:
        txn = data['transactions']
        withdraw = [['Service', 'Subscription'], ['Service', 'Financial',
                                                  'Loans and Mortgages'], ['Service', 'Insurance'], ['Payment', 'Rent']]
        dates = list()
        amounts = list()

        for t in txn:
            if t['category'] in withdraw and t['amount'] > 15:
                date = t['date']
                dates.append(date)
                amount = abs(t['amount'])
                amounts.append(amount)

        df = pd.DataFrame(data={'amounts': amounts},
                          index=pd.DatetimeIndex(dates))

        if len(df.index) > 0:
            how_many = np.mean(df.groupby(pd.Grouper(
                freq='M')).count().iloc[:, 0].tolist())
            if how_many > 0:
                volume = np.mean(df.groupby(pd.Grouper(
                    freq='M')).sum().iloc[:, 0].tolist())

                m = np.digitize(how_many, count_zero, right=True)
                n = np.digitize(volume, volume_withdraw, right=True)
                score = m3x7_73_17[m][n]

                feedback['velocity']['withdrawals'] = round(how_many, 0)
                feedback['velocity']['withdrawals_volume'] = round(volume, 0)

        else:
            raise Exception('no withdrawals')

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def velocity_deposits(data, feedback, count_zero, volume_deposit, m3x7_73_17):
    '''
    returns score based on count and volumne of monthly automated deposits

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns: 
                score (float): score associated with direct deposits
                feedback (dict): feedback describing the score
    '''
    try:
        txn = data['transactions']
        dates = list()
        amounts = list()

        for t in txn:
            if t['amount'] < -200 and 'payroll' in [c.lower() for c in t['category']]:
                date = t['date']
                dates.append(date)
                amount = abs(t['amount'])
                amounts.append(amount)

        df = pd.DataFrame(data={'amounts': amounts},
                          index=pd.DatetimeIndex(dates))

        if len(df.index) > 0:
            how_many = np.mean(df.groupby(pd.Grouper(
                freq='M')).count().iloc[:, 0].tolist())
            if how_many > 0:
                volume = np.mean(df.groupby(pd.Grouper(
                    freq='M')).sum().iloc[:, 0].tolist())

                m = np.digitize(how_many, count_zero, right=True)
                n = np.digitize(volume, volume_deposit, right=True)
                score = m3x7_73_17[m][n]

                feedback['velocity']['deposits'] = round(how_many, 0)
                feedback['velocity']['deposits_volume'] = round(volume, 0)

        else:
            raise Exception('no deposits')

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def velocity_month_net_flow(data, feedback, flow_ratio, volume_flow, m7x7_03_17):
    '''
    returns score for monthly net flow

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns: 
                score (float): score associated with monthly new flow
                feedback (dict): feedback describing the score
    '''
    try:
        flow = flows(data, 12, feedback)

        # Calculate magnitude of flow (how much is flowing monthly?)
        cum_flow = [abs(x) for x in flow['amounts'].tolist()]
        magnitude = np.mean(cum_flow)

        # Calculate direction of flow (is money coming in or going out?)
        neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
        pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))

        if neg:
            direction = len(pos)/len(neg)  # output in range [0, ...)
        else:
            direction = 10  # 10 is an arbitralkity chosen large positive inteegr

        # Calculate score
        m = np.digitize(direction, flow_ratio, right=True)
        n = np.digitize(magnitude, volume_flow, right=True)
        score = m7x7_03_17[m][n]

        feedback['velocity']['avg_net_flow'] = round(magnitude, 2)

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def velocity_month_txn_count(data, feedback, fico_medians, count_txn):
    '''
    returns score based on count of mounthly transactions

            Parameters:
                data (dict): Plaid 'Transactions' product
                feedback (dict): feedback describing the score 

            Returns: 
                score (float): the larger the monthly count the larger the score
                feedback (dict): feedback describing the score
    '''
    try:
        acc = data['accounts']
        txn = data['transactions']

        dates = list()
        amounts = list()
        mycounts = list()
        deposit_acc = list()

        # Keep only deposit->checking accounts
        for a in acc:
            id = a['account_id']
            type = '{1}{0}{2}'.format(
                '_', str(a['type']), str(a['subtype'])).lower()

            if type == 'depository_checking':
                deposit_acc.append(id)

        # Keep only txn in deposit->checking accounts
        for d in deposit_acc:
            transat = [x for x in txn if x['account_id'] == d]

            # Bin transactions by month
            for t in transat:
                if abs(t['amount']) > 5:
                    date = t['date']
                    dates.append(date)
                    amount = t['amount']
                    amounts.append(amount)

            df = pd.DataFrame(data={'amounts': amounts},
                              index=pd.DatetimeIndex(dates))

            # Calculate avg count of monthly transactions for one checking account at a time
            if len(df.index) > 0:
                cnt = df.groupby(pd.Grouper(freq='M')
                                 ).count().iloc[:, 0].tolist()
            else:
                score = 0

            mycounts.append(cnt)

        mycounts = [x for y in mycounts for x in y]
        how_many = np.mean(mycounts)
        score = fico_medians[np.digitize(
            how_many, count_txn, right=True)]

        feedback['velocity']['count_monthly_txn'] = round(how_many, 0)

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def velocity_slope(data, feedback, fico_medians, slope_lr, slope, m7x7_03_17):
    '''
    returns score for the historical behavior of the net monthly flow for past 24 months

            Parameters:
                data (dict): Plaid 'Transactions' product 
                feedback (dict): feedback describing the score

            Returns:
                score (float): score for flow net behavior over past 24 months
                feedback (dict): feedback describing the score
    '''
    try:
        flow = flows(data, 24, feedback)

        # If you have > 10 data points OR all net flows are positive, then perform linear regression
        if len(flow) >= 10 or len(list(filter(lambda x: (x < 0), flow['amounts'].tolist()))) == 0:
            # Perform Linear Regression using numpy.polyfit()
            x = range(len(flow['amounts']))
            y = flow['amounts']
            a, b = np.polyfit(x, y, 1)

            score = fico_medians[np.digitize(
                a, slope_lr, right=True)]

            feedback['velocity']['slope'] = round(a, 2)

        # If you have < 10 data points, then calculate the score accounting for two ratios
        else:
            # Multiply two ratios by each other
            neg = list(filter(lambda x: (x < 0), flow['amounts'].tolist()))
            pos = list(filter(lambda x: (x >= 0), flow['amounts'].tolist()))
            direction = len(pos) / len(neg)  # output in range [0, 2+]
            magnitude = abs(sum(pos)/sum(neg))  # output in range [0, 2+]
            if direction >= 1:
                pass
            else:
                magnitude = magnitude * -1
            m = np.digitize(direction, slope, right=True)
            n = np.digitize(magnitude, slope, right=True)
            score = m7x7_03_17.T[m][n]

            feedback['velocity']['monthly_flow'] = round(magnitude, 2)

    except Exception as e:
        score = 0
        feedback['velocity']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #3 Stability                             #
# -------------------------------------------------------------------------- #


# @measure_time_and_memory
def stability_tot_balance_now(data, feedback, fico_medians, volume_balance):
    '''
    Description:
        A score based on total balance now across ALL accounts owned by the user

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns:
        score (float): cumulative current balance
        feedback (dict): score feedback
    '''
    try:
        depository = [d for d in data['accounts']
                      if d['type'].lower() == 'depository']
        non_depository = [d for d in data['accounts']
                          if d['type'].lower() != 'depository']
        x = sum([int(d['balances']['current']) if d['balances']
                ['current'] else 0 for d in depository])
        y = sum([int(d['balances']['available']) if d['balances']
                ['available'] else 0 for d in non_depository])
        balance = x+y

        if balance > 0:
            score = fico_medians[np.digitize(
                balance, volume_balance, right=True)]
            feedback['stability']['cumulative_current_balance'] = balance
            stability_tot_balance_now.balance = balance

        else:
            raise Exception('no balance')

    except Exception as e:
        score = 0
        feedback['stability']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def stability_loan_duedate(data, feedback, due_date):
    '''
    Description:
        returns how many months it'll take the user to pay back their loan

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns:
        feedback (dict): score feedback with a new key-value pair 'loan_duedate':float (# of months in range [3,6])
    '''

    try:
        # Read in the date of the oldest txn
        first_txn = data['transactions'][-1]['date']
        txn_length = int((now - first_txn).days/30)  # months

        # Loan duedate is equal to the month of txn history there are
        due = np.digitize(txn_length, due_date, right=True)
        how_many_months = np.append(due_date, 6)

        feedback['stability']['loan_duedate'] = how_many_months[due]

    except Exception as e:
        feedback['stability']['error'] = str(e)

    finally:
        return feedback


# @measure_time_and_memory
def stability_min_running_balance(data, feedback, duration, volume_min, m7x7_85_55):
    '''
    Description:
        A score based on the average minimum balance maintained for 12 months

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns:
        score (float): volume of minimum balance and duration
        feedback (dict): score feedback
    '''

    try:
        # Calculate net flow each month for past 12 months i.e, |income-expenses|
        nets = flows(data, 12, feedback)['amounts'].tolist()

        # Calculate total current balance now
        balance = balance_now_checking_only(data, feedback)

        # Subtract net flow from balancenow to calculate the running balance for the past 12 months
        running_balances = [balance+n for n in reversed(nets)]

        # Calculate volume using a weighted average
        weights = np.linspace(0.01, 1, len(running_balances)
                              ).tolist()  # define your weights
        volume = sum([x*w for x, w in zip(running_balances,
                     reversed(weights))]) / sum(weights)
        length = len(running_balances)*30

        # Compute the score
        m = np.digitize(length, duration, right=True)
        n = np.digitize(volume, volume_min, right=True)
        # add 0.025 score penalty for each overdrafts
        score = round(
            m7x7_85_55[m][n] - 0.025*len(list(filter(lambda x: (x < 0), running_balances))), 2)

        feedback['stability']['min_running_balance'] = round(volume, 2)
        feedback['stability']['min_running_timeframe'] = length

    except Exception as e:
        score = 0
        feedback['stability']['error'] = str(e)

    finally:
        return score, feedback


# -------------------------------------------------------------------------- #
#                            Metric #4 Diversity                             #
# -------------------------------------------------------------------------- #


# @measure_time_and_memory
def diversity_acc_count(data, feedback, count_zero, duration, m3x7_73_17):
    '''
    Description:
        A score based on count of accounts owned by the user and account duration

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns:
        score (float): score for accounts count
        feedback (dict): score feedback
    '''

    try:
        size = len(data['accounts'])

        first_txn = data['transactions'][-1]['date']
        date_diff = (now - first_txn).days

        m = np.digitize(size, [i+2 for i in count_zero], right=False)
        n = np.digitize(date_diff, duration, right=True)
        score = m3x7_73_17[m][n]

        feedback['diversity']['bank_accounts'] = size

    except Exception as e:
        score = 0
        feedback['diversity']['error'] = str(e)

    finally:
        return score, feedback


# @measure_time_and_memory
def diversity_profile(data, feedback, fico_medians, volume_invest):
    '''
    Description:
        A score for number of saving and investment accounts owned

    Parameters:
        data (dict): Plaid 'Transactions' product
        feedback (dict): score feedback

    Returns:
        score (float): points scored for accounts owned
        feedback (dict): score feedback
    '''

    try:
        myacc = list()

        acc = [x for x in data['accounts'] if x['type'] == 'loan' or int(
            x['balances']['current'] or 0) != 0]  # exclude $0 balance accounts

        balance = 0
        for a in acc:
            id = a['account_id']
            type = '{}_{}'.format(a['type'], str(a['subtype']))

            # Consider savings, hda, cd, money mart, paypal, prepaid, cash management, edt accounts
            if (type.split('_')[0] == 'depository') & (type.split('_')[1] != 'checking'):
                balance += int(a['balances']['current'] or 0)
                myacc.append(id)

            # Consider ANY type of investment account
            if type.split('_')[0] == 'investment':
                balance += int(a['balances']['current'] or 0)
                myacc.append(id)

        if balance != 0:
            score = fico_medians[np.digitize(
                balance, volume_invest, right=True)]
            feedback['diversity']['investment_accounts'] = len(myacc)
            feedback['diversity']['investment_total_balance'] = balance

        else:
            raise Exception('no investing nor savings accounts')

    except Exception as e:
        score = 0
        feedback['diversity']['error'] = str(e)

    finally:
        return score, feedback
