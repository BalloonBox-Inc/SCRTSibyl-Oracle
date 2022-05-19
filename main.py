from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv
from os import getenv
from icecream import ic

from testing.performance import *
from market.coinmarketcap import *
from market.coinapi import *
from validator.coinbase import *
from validator.plaid import *
from support.feedback import *
from support.score import *
from support.risk import *
from config.params import *

load_dotenv()


class Plaid_Item(BaseModel):
    plaid_access_token: str
    plaid_client_id: str
    plaid_client_secret: str
    coinmarketcap_key: str
    coinapi_key: str
    currencies: list[str] = []


class Coinbase_Item(BaseModel):
    coinbase_access_token: str
    coinbase_refresh_token: str
    coinmarketcap_key: str
    coinapi_key: str
    currencies: list[str] = []


app = FastAPI()


# @measure_time_and_memory
@app.post('/credit_score/plaid')
async def credit_score_plaid(item: Plaid_Item):

    try:
        # client connection
        client = plaid_client(
            getenv('ENV'),
            item.plaid_client_id,
            item.plaid_client_secret
        )
        ic(client)

        # data fetching
        plaid_txn = plaid_transactions(item.plaid_access_token, client, 360)

        if 'error' in plaid_txn:
            raise Exception(plaid_txn['error']['message'])

        # data formatting
        plaid_txn = {k: v for k, v in plaid_txn.items()
                     if k in ['accounts', 'item', 'transactions']}

        plaid_txn['transactions'] = [
            t for t in plaid_txn['transactions'] if not t['pending']]

        # create feedback
        feedback = plaid_bank_name(
            client,
            plaid_txn['item']['institution_id'],
            create_feedback_plaid()
        )

        # compute score and feedback
        score, feedback = plaid_score(plaid_txn, feedback)

        # compute risk
        risk = calc_risk(score)

        # update feedback
        message = qualitative_feedback_plaid(
            score,
            feedback,
            item.coinapi_key
        )

        feedback = interpret_score_plaid(score, feedback)

        # return success
        status_code = 200
        status = 'success'

    except Exception as e:
        status_code = 400
        status = 'error'
        score = 0
        risk = {}
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
            'risk': risk,
            'feedback': feedback,
            'message': message
        }

        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

        ic(output)

        return output


# @measure_time_and_memory
@app.post('/credit_score/coinbase')
async def credit_score_coinbase(item: Coinbase_Item):

    try:
        # client connection
        client = coinbase_client(
            item.coinbase_access_token,
            item.coinbase_refresh_token
        )
        ic(client)

        # coinbase currencies
        coinbase_currencies = coinbase_currencies(client)

        if 'error' in coinbase_currencies:
            raise Exception(coinbase_currencies['error']['message'])

        # coinmarketcap top X currencies
        top_currencies = coinmarketcap_currencies(item.coinmarketcap_key, 25)

        coinbase_currencies = {k: 1 for (k, v) in coinbase_currencies.items()
                               if v == 0.01 or k in coinbase_odd_fiats()}

        top_currencies.update(coinbase_currencies)
        top_currencies = list(top_currencies.keys())
        ic(top_currencies)

        # set native currency to USD
        native = coinbase_native_currency(client)
        ic(native)

        if 'error' in native:
            raise Exception(native['error']['message'])

        if native != 'USD':
            set_native = coinbase_set_native_currency(client, 'USD')
            ic(set_native)

        # data fetching
        coinbase_acc = coinbase_accounts(client)

        if 'error' in coinbase_acc:
            raise Exception(coinbase_acc['error']['message'])

        # data formatting
        coinbase_acc = [n for n in coinbase_acc
                        if n['currency'] in top_currencies]

        coinbase_txn = [coinbase_transactions(client, n['id'])
                        for n in coinbase_acc]

        coinbase_txn = [x for n in coinbase_txn for x in n]

        coinbase_txn = [n for n in coinbase_txn
                        if n['status'] == 'completed'
                        and n['type'] in coinbase_txn_types()]

        for d in coinbase_txn:  # relabel transaction types
            if d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == 1:
                d['type'] = 'send_credit'

            elif d['type'] == 'send' and np.sign(float(d['amount']['amount'])) == -1:
                d['type'] = 'send_debit'

        # reset native currency
        set_native = coinbase_set_native_currency(client, native)
        ic(set_native)

        # compute score and feedback
        score, feedback = coinbase_score(
            coinbase_acc,
            coinbase_txn,
            create_feedback_coinbase()
        )

        # compute risk
        risk = calc_risk(score)

        # update feedback
        message = qualitative_feedback_coinbase(
            score,
            feedback,
            item.coinapi_key
        )

        feedback = interpret_score_coinbase(score, feedback)

        # return success
        status_code = 200
        status = 'success'

    except Exception as e:
        status_code = 400
        status = 'error'
        score = 0
        risk = {}
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
            'risk': risk,
            'feedback': feedback,
            'message': message
        }

        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

        ic(output)

        return output
