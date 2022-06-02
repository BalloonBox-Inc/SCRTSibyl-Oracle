from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv
from os import getenv
from icecream import ic

from validator.plaid import *
from validator.coinbase import *
from validator.binance import *
from market.coinmarketcap import *
from market.coinapi import *
from support.score import *
from support.feedback import *
from support.risk import *
from support.helper import *
from config.helper import *
from testing.performance import *


load_dotenv()


class Plaid_Item(BaseModel):
    plaid_access_token: str
    plaid_client_id: str
    plaid_client_secret: str
    coinmarketcap_key: str
    coinapi_key: str
    loan_request: int
    currencies: list[str] = []


class Coinbase_Item(BaseModel):
    coinbase_access_token: str
    coinbase_refresh_token: str
    coinmarketcap_key: str
    coinapi_key: str
    loan_request: int
    currencies: list[str] = []


class Binance_Item(BaseModel):
    binance_api_key: str
    binance_api_secret: str
    coinmarketcap_key: str
    coinapi_key: str
    loan_request: int
    currencies: list[str] = []


app = FastAPI()


# @measure_time_and_memory
@app.post('/credit_score/plaid')
async def credit_score_plaid(item: Plaid_Item):

    try:
        # configs
        configs = read_config_file(item.loan_request)

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['plaid']['thresholds']
        params = configs['minimum_requirements']['plaid']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['plaid']['scores']['models'])

        penalties = read_model_penalties(
            configs['minimum_requirements']['plaid']['scores']['models'])

        messages = configs['minimum_requirements']['plaid']['messages']
        feedback = create_feedback(models)
        feedback['fetch'] = {}

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)
        ic(thresholds)
        ic(params)
        ic(models)
        ic(metrics)
        ic(penalties)
        ic(messages)
        ic(feedback)

        # plaid client connection
        client = plaid_client(
            getenv('ENV'),
            item.plaid_client_id,
            item.plaid_client_secret
        )
        ic(client)

        # data fetching
        transactions = plaid_transactions(
            item.plaid_access_token,
            client,
            thresholds['transactions_period']
        )
        # ic(transactions)
        if isinstance(transactions, str):
            raise Exception(transactions)

        bank_name = plaid_bank_name(
            client,
            transactions['item']['institution_id'],
        )
        feedback['diversity']['bank_name'] = bank_name
        ic(bank_name)

        # compute score and feedback
        score, feedback = plaid_score(
            score_range,
            feedback,
            models,
            penalties,
            metrics,
            params,
            transactions
        )
        ic(score)
        ic(feedback)

        # compute risk
        risk = calc_risk(
            score,
            score_range,
            loan_range
        )

        # update feedback
        message = qualitative_feedback_plaid(
            messages,
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range,
            item.coinapi_key
        )

        feedback = interpret_score_plaid(
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range
        )
        ic(message)
        ic(feedback)

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
            'message': message,
            'feedback': feedback
        }

        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

        return output


# @measure_time_and_memory
@app.post('/credit_score/coinbase')
async def credit_score_coinbase(item: Coinbase_Item):

    try:
        # configs
        configs = read_config_file(item.loan_request)

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['coinbase']['thresholds']
        params = configs['minimum_requirements']['coinbase']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['coinbase']['scores']['models'])

        messages = configs['minimum_requirements']['coinbase']['messages']
        feedback = create_feedback(models)

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)
        ic(thresholds)
        ic(params)
        ic(models)
        ic(metrics)
        ic(messages)
        ic(feedback)

        # coinmarketcap
        top_marketcap = coinmarketcap_currencies(
            item.coinmarketcap_key,
            thresholds['coinmarketcap_currencies']
        )
        ic(top_marketcap)
        if isinstance(top_marketcap, str):
            raise Exception(top_marketcap)

        # coinbase client connection
        client = coinbase_client(
            item.coinbase_access_token,
            item.coinbase_refresh_token
        )
        ic(client)

        # coinbase supported currencies
        currencies = coinbase_currencies(client)
        ic(currencies)
        if 'error' in currencies:
            raise Exception(currencies['error']['message'])

        # add top coinmarketcap currencies and coinbase currencies
        top_currencies = aggregate_currencies(
            top_marketcap,
            currencies,
            thresholds['odd_fiats']
        )
        ic(top_currencies)

        # set native currency to USD
        native = coinbase_native_currency(client)
        if 'error' in native:
            raise Exception(native['error']['message'])
        if native != 'USD':
            set_native = coinbase_set_native_currency(client, 'USD')
        ic(native)

        # data fetching
        accounts, transactions = coinbase_accounts_and_transactions(
            client,
            top_currencies,
            thresholds['transaction_types']
        )
        ic(accounts)
        ic(transactions)
        if isinstance(accounts, str):
            raise Exception(accounts)

        # reset native currency
        set_native = coinbase_set_native_currency(client, native)
        ic(set_native)

        # compute score and feedback
        score, feedback = coinbase_score(
            score_range,
            feedback,
            models,
            metrics,
            params,
            accounts,
            transactions
        )
        ic(score)
        ic(feedback)

        # compute risk
        risk = calc_risk(
            score,
            score_range,
            loan_range
        )

        # update feedback
        message = qualitative_feedback_coinbase(
            messages,
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range,
            item.coinapi_key
        )

        feedback = interpret_score_coinbase(
            score,
            feedback,
            score_range,
            loan_range,
            qualitative_range
        )
        ic(message)
        ic(feedback)

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
            'message': message,
            'feedback': feedback
        }

        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

        ic(output)

        return output


# @measure_time_and_memory
@app.post('/credit_score/binance')
async def credit_score_binance(item: Binance_Item):

    try:
        # configs
        configs = read_config_file(item.loan_request)

        loan_range = configs['loan_range']
        score_range = configs['score_range']
        qualitative_range = configs['qualitative_range']

        thresholds = configs['minimum_requirements']['binance']['thresholds']
        params = configs['minimum_requirements']['binance']['params']

        models, metrics = read_models_and_metrics(
            configs['minimum_requirements']['binance']['scores']['models'])

        feedback = create_feedback(models)

        ic(loan_range)
        ic(score_range)
        ic(qualitative_range)

        ic(models)
        ic(metrics)

        ic(feedback)

        # client connection
        client = binance_client(
            item.binance_api_key,
            item.binance_api_secret,
        )

        ic(client)

        # data fetching
        # binance_balance = binance_spot_balance(client, item.coinapi_key)
        # ic(binance_balance)
        # if isinstance(binance_balance, str):
        #     raise Exception('Unable to connect with Binance')

        binance_balance = 0
        binance_wallet = 0
        binance_savings = 0
        binance_trades = 0
        binance_savings = 0
        binance_nfts = 0
        binance_swaps = 0

        # compute score and feedback
        score, feedback = binance_score(
            binance_balance,
            binance_wallet,
            binance_trades,
            binance_savings,
            binance_nfts,
            binance_swaps,
            feedback,
            models
        )

        # compute risk
        # risk = calc_risk(score, score_range, loan_range)

        # update feedback
        # message = qualitative_feedback_binance(
        #     score,
        #     feedback,
        #     item.coinapi_key
        # )

        # feedback = interpret_score_binance(score, feedback)

        # return success
        status_code = 200
        status = 'success'
        risk = {}
        feedback = {}
        message = {}

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
            'endpoint': '/credit_score/binance',
            'title': 'Credit Score',
            'status_code': status_code,
            'status': status,
            'timestamp': timestamp,
            'score': int(score),
            'risk': risk,
            'message': message,
            'feedback': feedback
        }

        if score == 0:
            output.pop('score', None)
            output.pop('risk', None)
            output.pop('feedback', None)

        ic(output)

        return output
