from flask import request, make_response
from dotenv import load_dotenv
from os import getenv

from feedback.qualitative_score import *
from validator_api.coinmarketcap import *
from validator_api.coinbase import *
from validator_api.plaid import *
from support.score import *

from optimization.performance import *
from app import *

load_dotenv()


def create_feedback_plaid():
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


def create_feedback_coinbase():
    return {'fetch': [], 'kyc': [], 'history': [], 'liquidity': [], 'activity': []}


# @app.route('/credit_score/plaid', methods=['POST'])
@measure_time_and_memory
def credit_score_plaid():

    try:
        # plaid_token = request.json.get('plaid_public_token', None)
        # keplr_token = request.json.get('keplr_token', None)
        plaid_token = getenv('PLAID_ACCESS_TOKEN')
        plaid_client_id = getenv('PLAID_CLIENT_ID')
        plaid_client_secret = getenv('PLAID_CLIENT_SECRET')
    
    except Exception as e:
        return str(e)

    try:
        # client connection
        client = plaid_client('sandbox', plaid_client_id, plaid_client_secret)
        # client = plaid_client('production', plaid_client_id, plaid_client_secret)
        
        # data fetching and formatting
        plaid_txn = plaid_transactions(plaid_token, client, 360)
        plaid_txn = {k:v for k,v in plaid_txn.items() if k in ['accounts','transactions']}
        plaid_txn['transactions'] = [t for t in plaid_txn['transactions'] if not t['pending']]
        
        # compute score
        feedback = create_feedback_plaid()
        score, feedback = plaid_score(plaid_txn, feedback)
        msg = qualitative_feedback_plaid(score, feedback)

        return score, feedback, msg
    
    except Exception as e:
        return 'Error', str(e)


# @app.route('/credit_score/coinbase', methods=['POST'])
@measure_time_and_memory
def credit_score_coinbase():

    try:
        # coinbase_token = request.json.get('coinbase_public_token', None)
        # coinmarketcap_key = request.json.get('coinmarketcap_key', None)
        # keplr_token = request.json.get('keplr_token', None)
        coinbase_token = getenv('COINBASE_CLIENT_ID')
        coinbase_secret = getenv('COINBASE_CLIENT_SECRET')
        coinmarketcap_key = getenv('COINMARKETCAP_KEY')
    
    except Exception as e:
        return str(e)
    
    try:
        # client connection
        client = coinbase_client(coinbase_token, coinbase_secret)

        # coinmarketcap
        top_coins = coinmarketcap_coins(coinmarketcap_key, 30)
        currencies = coinbase_currencies(client)
        odd_fiats = ['BHD', 'BIF', 'BYR', 'CLP', 'DJF', 'GNF', 'HUF', 'IQD', 'ISK', 'JOD', 'JPY', 'KMF', 'KRW', 'KWD', 'LYD', 'MGA', 'MRO', 'OMR', 'PYG', 'RWF', 'TND', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']
        currencies = {k:1 for (k,v) in currencies.items() if v == 0.01 or k in odd_fiats}
        top_coins.update(currencies)
        coins = list(top_coins.keys())

        # coinbase native currency
        native = coinbase_native_currency(client)
        if native != 'USD':
            coinbase_set_native_currency(client, 'USD')
        
        # data fetching and formatting
        coinbase_acc = coinbase_accounts(client)
        coinbase_acc = [n for n in coinbase_acc if n['currency'] in coins]
        
        coinbase_txn = [coinbase_transactions(client, n['id']) for n in coinbase_acc]
        coinbase_txn = [x for n in coinbase_txn for x in n]
        txn_types = ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
        coinbase_txn = [n for n in coinbase_txn if n['status'] == 'completed' and n['type'] in txn_types]
        for d in coinbase_txn:
            if d['type']=='send' and np.sign(float(d['amount']['amount']))==1:
                d['type'] = 'send_credit'
            elif d['type']=='send' and np.sign(float(d['amount']['amount']))==-1:
                d['type'] = 'send_debit'
            
        # reset native currency
        coinbase_set_native_currency(client, native)

        # compute score
        feedback = create_feedback_coinbase()
        score, feedback = coinbase_score(coinbase_acc, coinbase_txn, feedback)

        return score, feedback
    
    except Exception as e:
        return 'Error', str(e)
