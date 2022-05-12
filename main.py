from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv
from os import getenv
from icecream import ic

from testing.performance import *
from market.coinmarketcap import *
from validator.coinbase import *
from validator.plaid import *
from support.feedback import *
from support.score import *

load_dotenv()


def create_feedback_plaid():
    return {'fetch': {}, 'credit': {}, 'velocity': {}, 'stability': {}, 'diversity': {}}


def create_feedback_coinbase():
    return {'kyc': {}, 'history': {}, 'liquidity': {}, 'activity': {}}


class Plaid_Item(BaseModel):
    plaid_access_token: str
    plaid_client_id: str
    plaid_client_secret: str
    coinmarketcap_key: str


class Coinbase_Item(BaseModel):
    coinbase_access_token: str
    coinbase_refresh_token: str
    coinmarketcap_key: str


app = FastAPI()


# @measure_time_and_memory
@app.post('/credit_score/plaid')
async def credit_score_plaid(item: Plaid_Item):

    try:
        # client connection
        client = plaid_client(
            getenv('ENV'), item.plaid_client_id, item.plaid_client_secret)
        ic(client)

        # data fetching and formatting
        plaid_txn = plaid_transactions(item.plaid_access_token, client, 360)
        if 'error' in plaid_txn:
            raise Exception(plaid_txn['error']['message'])

        plaid_txn = {k: v for k, v in plaid_txn.items(
        ) if k in ['accounts', 'item', 'transactions']}
        plaid_txn['transactions'] = [
            t for t in plaid_txn['transactions'] if not t['pending']]

        # compute score
        feedback = create_feedback_plaid()
        feedback = plaid_bank_name(
            client, plaid_txn['item']['institution_id'], feedback)
        score, feedback = plaid_score(plaid_txn, feedback)
        message = qualitative_feedback_plaid(
            score, feedback, item.coinmarketcap_key)
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
        timestamp = datetime.now(timezone.utc).strftime(
            '%m-%d-%Y %H:%M:%S GMT')
        output = {
            'endpoint': '/credit_score/plaid',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            'feedback': feedback,
            'message': message
        }

        if score == 0:
            output.pop('score', None)
            output.pop('feedback', None)

        ic(output)

        return output


# @measure_time_and_memory
@app.post('/credit_score/coinbase')
async def credit_score_coinbase(item: Coinbase_Item):

    try:
        # client connection
        client = coinbase_client(
            item.coinbase_access_token, item.coinbase_refresh_token)
        ic(client)

        # coinmarketcap
        # fetch top X cryptos from coinmarketcap API
        top_coins = coinmarketcap_coins(item.coinmarketcap_key, 25)
        ic(top_coins)
        currencies = coinbase_currencies(client)
        ic(currencies)
        if 'error' in currencies:
            raise Exception(currencies['error']['message'])

        odd_fiats = ['BHD', 'BIF', 'BYR', 'CLP', 'DJF', 'GNF', 'HUF', 'IQD', 'ISK', 'JOD', 'JPY', 'KMF', 'KRW',
                     'KWD', 'LYD', 'MGA', 'MRO', 'OMR', 'PYG', 'RWF', 'TND', 'UGX', 'VND', 'VUV', 'XAF', 'XOF', 'XPF']
        currencies = {k: 1 for (k, v) in currencies.items()
                      if v == 0.01 or k in odd_fiats}
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

        coinbase_txn = [coinbase_transactions(
            client, n['id']) for n in coinbase_acc]
        coinbase_txn = [x for n in coinbase_txn for x in n]

        # keep only certain transaction types
        txn_types = ['fiat_deposit', 'request', 'buy',
                     'fiat_withdrawal', 'vault_withdrawal', 'sell', 'send']
        coinbase_txn = [n for n in coinbase_txn if n['status']
                        == 'completed' and n['type'] in txn_types]
        for d in coinbase_txn:
            # If the txn is of 'send' type and is a credit, then relabel its type to 'send_credit'
            if d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == 1:
                d['type'] = 'send_credit'
            # If the txn is of 'send' type and is a debit, then relabel its type to 'send_debit'
            elif d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == -1:
                d['type'] = 'send_debit'

        # reset native currency
        set_native = coinbase_set_native_currency(client, native)
        ic(set_native)

        # compute score
        feedback = create_feedback_coinbase()
        score, feedback = coinbase_score(
            coinbase_acc, coinbase_txn, feedback)
        message = qualitative_feedback_coinbase(
            score, feedback, item.coinmarketcap_key)
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
        timestamp = datetime.now(timezone.utc).strftime(
            '%m-%d-%Y %H:%M:%S GMT')
        output = {
            'endpoint': '/credit_score/coinbase',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            'feedback': feedback,
            'message': message
        }

        if score == 0:
            output.pop('score', None)
            output.pop('feedback', None)

        ic(output)

        return output
