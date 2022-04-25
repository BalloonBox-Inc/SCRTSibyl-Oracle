import os
import json
import numpy as np
from datetime import datetime


# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                 -local data-                               #
#                                    Plaid                                   #
# -------------------------------------------------------------------------- #

# Remove this function eventually. It's used only to fetch local data for testing purposes.
def get_tx(path_dir, userid, feedback):
    '''
    returns the Plaid 'Transaction' product for one user

            Parameters:
                path_dir (str): path to the directory where the transaction files are stored
                userid (str): number of the user you want to retrieve transaction data for
        
            Returns: 
                data (dict of lists): with transactions of all user's bank accoutns (credit, checking, saving, loan, etc.) in chronological order (newest to oldest)
    '''
    try:
        # Iterate through all files in a directory
        directory = os.fsencode(path_dir)
        mobi_plaid = list()
        for f in os.listdir(directory):
            filename = os.fsdecode(f)
            if filename.endswith('.json'): #filter by .json files
                mobi_plaid.append(filename) #append file names to list
        mobi_plaid =  sorted(mobi_plaid) 

        # Select one user and retrieve their transaction history
        lol = list()
        for f in mobi_plaid:
            if f.startswith('{}-tx_'.format(userid)): #choose your user
                tx_one_page = json.load(open(path_dir+f)) #open json
                acc = tx_one_page['accounts']
                item = tx_one_page['item']
                lol.append(tx_one_page['transactions']) #append txn data only
        txn = list(np.concatenate(lol).flat) #flatten list 
        data = {'accounts':acc, 'item':item, 'transactions':txn}
        return data

    except Exception as e:
        feedback['kyc'][get_tx.__name__] = str(e)
        


def str_to_datetime(plaid_txn, feedback):
    """
    serialize a Python data structure converting string instances into datetime objects
            Parameters:
                plaid_txn (list): locally stored Plaid data used for testing purposes
            Returns:
                tx (dict): serialized dict containing user accounts and transactions. String dates are converted to datetime objects
     """
    try:
        # Keep only completed transactions (filter out pending transactions)
        all_txn = []
        for t in plaid_txn['transactions']:
            if t['pending'] == False:
                t['date'] = datetime.strptime(t['date'], '%Y-%m-%d').date()
                all_txn.append(t)

        # Prettify and write to json
        tx = {'accounts':plaid_txn['accounts'],  'transactions':all_txn}
        return tx

    except Exception as e:
        feedback['fetch'][str_to_datetime.__name__] = str(e)




# -------------------------------------------------------------------------- #
#                               Helper Functions                             #
#                                 -local data-                               #
#                                   Coinbase                                 #
# -------------------------------------------------------------------------- #
# Eventually remove this next function, which is merely used to import local json data to test the Coinbase model during development phase. 
def refactor_test_data(path_dir, userid, top_coins):
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
    txn_types = ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
    filtered_tx = [n for n in tx if n['status'] == 'completed' and n['type'] in txn_types]
    for d in filtered_tx:
        # If the txn is of 'send' type and is a credit, then relabel its type to 'send_credit'
        if d['type']=='send' and np.sign(float(d['amount']['amount']))==1:
            d['type'] = 'send_credit'
        # If the txn is of 'send' type and is a debit, then relabel its type to 'send_debit' 
        elif d['type']=='send' and np.sign(float(d['amount']['amount']))==-1:
            d['type'] = 'send_debit'

    return filtered_acc, filtered_tx



def str_to_date(acc, feedback):
    """
    serialize a Python data structure converting string instances into datetime objects
            Parameters:
                tx (list): locally stored Coinbase data. Either account OR transactions data
            Returns:
                all_txn (list): serialized list containing user accounts OR transactions. String dates are converted to datetime objects
     """
    try:
        converted = []
        for x in acc:
            if x['created_at']:
                x['created_at'] = datetime.strptime(x['created_at'], '%Y-%m-%dT%H:%M:%SZ').date()
                converted.append(x)

        return converted

    except Exception as e:
        feedback['kyc'][str_to_date.__name__] = str(e)