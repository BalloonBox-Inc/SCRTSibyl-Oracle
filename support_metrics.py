#  << Build helper functions to retrieve user's transactions info from Plaid data and generate 5 basic metrics for the credit score algorithm >>


### Metric #1: Transactions count and volume


### Metric #1: Transactions count and volume
def txn(data):
    """
    Calculate tot txn count & tot txn volume
    
    Args:
        transaction data as a dict
        
    Returns:
        a tuple containing the cumulative number of transactions and the tot of inflow-outflow of transactions
    """
    try:
        cnt = data['total_transactions']
        date = []
        volume = []
        for i in range(len(data['transactions'])):
            txn = data['transactions'][i]
            v = txn['amount']
            volume.append(v)
        return (cnt, sum(volume))
        
    except Exception as e:
        return "Error:txn()"



def net_monthly(data):
    """
    What is the net monthly inflow across all accounts for a given user?
    This function outputs the monthly net flow of money in/out the user's bank accounts
     
    Args:
        transaction data as a dict
    
    Returns:
        list of list of dates and net monthly flow
    """
    try:
        date = []
        amount = []
        for i in range(len(data['transactions'])):
            txn = data['transactions'][i]
            date.append(txn['date'])
            amount.append(txn['amount'])

        df0 = pd.DataFrame(data={'amount': amount}, index=pd.DatetimeIndex(pd.to_datetime(date)))
        df1 = df0.groupby(pd.Grouper(freq='M', how='start')).sum()

        net_pair = []
        for i in range(len(df1)):
            dt = df1.index.to_list()[i].isoformat().split("T")[0]
            am = df1['amount'].to_list()[i]
            net_pair.append([dt,am])
        return net_pair
    except Exception as e:
        return "Error:net_monthly()"



### Metric #2: Length of credit history


### Metric #3: Avg age of borrower's credit accounts



### Metric #4: Composition or mix of borrower's accounts
def acc_mix(data):
    """
    returns composition and status of user's accounts
    
    Agrs:
        data as dict
    
    Returns:
        number of accounts, account types, balances, and currencies as a list of lists
    """
    try: 
        types = []
        balances = []
        currency = []

        account = data["accounts"]
        for i in range(len(account)):
            t = str(account[i]['type']) + "_" + str(account[i]['subtype'])
            b = account[i]['balances']['current']
            c = account[i]['balances']['iso_currency_code'] 
            types.append(t)
            balances.append(b)
            currency.append(c)
            acc_mix = [len(types), types, balances, currency]
        return acc_mix

    except Exception as e:
        return "Error:acc_mix()"
    




### Metric #5: Credit Utilization Ratio
def keep_credit(data):
    """
    Returns index of the user's credit accounts
    
    Args:
        transaction data as dict
    
    Return:
        list of indeces of all credit accounts 
    """
    credit_account = []
    try: 
        types = []

        account = data["accounts"]
        for i in range(len(account)):
            t = str(account[i]['type']) + "_" + str(account[i]['subtype'])
            if t in ['credit_credit card', 'depository_cd']:
                types.append(t)
                credit_account.append(i)
        return credit_account
    except Exception as e:
        return "Error:keep_credit()"


def credit_util_ratio(data):
    """
    Returns the credit utilization ratio = credit used/credit available
    
    Args:
    transaction datat as dict
    
    Returns:
    ratio as a float
    """
    try:
        tot_credit = []
        used_credit = []
        types = []

        account = data["accounts"]
        c = keep_credit(data)

        for i in c:
            tot = account[i]['balances']['current']
            t = str(account[i]['type']) + "_" + str(account[i]['subtype'])
            if account[i]['balances']['available'] != None:
                avail = account[i]['balances']['available']
            else: 
                avail = 0
            used = tot-avail
            tot_credit.append(tot)
            used_credit.append(used)
            types.append(t)
            r = sum(used_credit)/sum(tot_credit)
        return r
        
    except Exception as e:
        return "Error:credit_util_ratio()"
