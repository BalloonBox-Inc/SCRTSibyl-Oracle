from flask import request, make_response
from dotenv import load_dotenv
from datetime import datetime
from datetime import timezone
from icecream import ic
from os import getenv

from optimization.performance import *
from feedback.qualitative_score import *
from validator_api.coinmarketcap import *
from validator_api.coinbase import *
from validator_api.plaid import *
from support.score import *
from app import *

load_dotenv()

if getenv('ENV') == 'production':
    ic.disable()


def create_feedback_plaid():
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


def create_feedback_coinbase():
    return {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}}


# @measure_time_and_memory
@app.route('/credit_score/plaid', methods=['POST'])
def credit_score_plaid():

    if request.method == 'POST':
        try:
            keplr_token = request.json.get('keplr_token', None)
            plaid_token = request.json.get('plaid_token', None)
            plaid_client_id = request.json.get('plaid_client_id', None)
            plaid_client_secret = request.json.get('plaid_client_secret', None)
        except Exception as e:
            timestamp = datetime.now(timezone.utc).strftime('%m-%d-%Y %H:%M:%S GMT')
            output = {
                'endpoint': '/credit_score/plaid',
                'title': 'Credit Score',
                'status_code': 400,
                'status': 'error',
                'timestamp': timestamp,
                'message': str(e)
                }
            ic(output)
            return make_response(output, output['status_code'])
        
        try:
            # client connection
            client = plaid_client(getenv('ENV'), plaid_client_id, plaid_client_secret)
            ic(client)

            # data fetching and formatting
            plaid_txn = plaid_transactions(plaid_token, client, 360)
            if 'error' in plaid_txn:
                raise Exception(plaid_txn['error']['message'])
            
            plaid_txn = {k:v for k,v in plaid_txn.items() if k in ['accounts','transactions']}
            plaid_txn['transactions'] = [t for t in plaid_txn['transactions'] if not t['pending']]
            
            # compute score
            feedback = create_feedback_plaid()
            score, feedback = plaid_score(plaid_txn, feedback)
            message = qualitative_feedback_plaid(score, feedback)
            feedback = interpret_score_plaid(score, feedback)

            status_code = 200
            status = 'success'
        
        except Exception as e:
            status_code = 400
            status = 'error'
            score = 0
            feedback = {}
            message = str(e)
        
        finally:
            timestamp = datetime.now(timezone.utc).strftime('%m-%d-%Y %H:%M:%S GMT')
            output = {
                'endpoint': '/credit_score/plaid',
                'title': 'Credit Score',
                'status_code': status_code,
                'status': status,
                'timestamp': timestamp,
                'score': int(round(score,0)),
                'feedback': feedback,
                'message': message
                }
            if score == 0:
                output.pop('score', None)
                output.pop('feedback', None)
            ic(output)
            return make_response(output, output['status_code'])


# @measure_time_and_memory
@app.route('/credit_score/coinbase', methods=['POST'])
def credit_score_coinbase():

    if request.method == 'POST':
        try:
            keplr_token = request.json.get('keplr_token', None)
            coinbase_access_token = request.json.get('coinbase_access_token', None)
            coinbase_refresh_token = request.json.get('coinbase_refresh_token', None)
            coinmarketcap_key = request.json.get('coinmarketcap_key', None)
        except Exception as e:
            timestamp = datetime.now(timezone.utc).strftime('%m-%d-%Y %H:%M:%S GMT')
            output = {
                'endpoint': '/credit_score/coinbase',
                'title': 'Credit Score',
                'status_code': 400,
                'status': 'error',
                'timestamp': timestamp,
                'message': str(e)
                }
            ic(output)
            return make_response(output, output['status_code'])
        
        try:
            # client connection
            client = coinbase_client(coinbase_access_token, coinbase_refresh_token)
            ic(client)

            # coinmarketcap
            # fetch top X cryptos from coinmarketcap API
            top_coins = coinmarketcap_coins(coinmarketcap_key, 50)
            currencies = coinbase_currencies(client)
            if 'error' in currencies:
                raise Exception(currencies['error']['message'])

            odd_fiats = ['BHD', 'BIF', 'BYR', 'CLP', 'DJF', 'GNF', 'HUF', 'IQD', 'ISK', 'JOD', 'JPY', 'KMF', 'KRW', 'KWD', 'LYD', 'MGA', 'MRO', 'OMR', 'PYG', 'RWF', 'TND', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']
            currencies = {k:1 for (k,v) in currencies.items() if v == 0.01 or k in odd_fiats}
            top_coins.update(currencies)
            coins = list(top_coins.keys())

            # change coinbase native currency to USD
            native = coinbase_native_currency(client)
            ic(native)
            if 'error' in native:
                raise Exception(native['error']['message'])
            if native != 'USD':
                set_native = coinbase_set_native_currency(client, 'USD')
                ic(set_native)

            # fetch and format data from user's Coinbase account
            coinbase_acc = coinbase_accounts(client)
            if 'error' in coinbase_acc:
                raise Exception(coinbase_acc['error']['message'])
            coinbase_acc = [n for n in coinbase_acc if n['currency'] in coins]
            
            coinbase_txn = [coinbase_transactions(client, n['id']) for n in coinbase_acc]
            coinbase_txn = [x for n in coinbase_txn for x in n]
            
            # keep only certain transaction types
            txn_types = ['fiat_deposit', 'request', 'buy', 'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
            coinbase_txn = [n for n in coinbase_txn if n['status'] == 'completed' and n['type'] in txn_types]
            for d in coinbase_txn:
                # If the txn is of 'send' type and is a credit, then relabel its type to 'send_credit'
                if d['type']=='send' and np.sign(float(d['amount']['amount']))==1:
                    d['type'] = 'send_credit'
                # If the txn is of 'send' type and is a debit, then relabel its type to 'send_debit' 
                elif d['type']=='send' and np.sign(float(d['amount']['amount']))==-1:
                    d['type'] = 'send_debit'
            
            # reset native currency
            set_native = coinbase_set_native_currency(client, native)
            ic(set_native)
            
            # compute score
            feedback = create_feedback_coinbase()
            score, feedback = coinbase_score(coinbase_acc, coinbase_txn, feedback)
            message = qualitative_feedback_coinbase(score, feedback)
            feedback = interpret_score_coinbase(score, feedback)

            status_code = 200
            status = 'success'
        
        except Exception as e:
            status_code = 400
            status = 'error'
            score = 0
            feedback = {}
            message = str(e)
        
        finally:
            timestamp = datetime.now(timezone.utc).strftime('%m-%d-%Y %H:%M:%S GMT')
            output = {
                'endpoint': '/credit_score/coinbase',
                'title': 'Credit Score',
                'status_code': status_code,
                'status': status,
                'timestamp': timestamp,
                'score': int(round(score,0)),
                'feedback': feedback,
                'message': message
                }
            if score == 0:
                output.pop('score', None)
                output.pop('feedback', None)
            ic(output)
            return make_response(output, output['status_code'])
