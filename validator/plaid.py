from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.country_code import CountryCode

from plaid.api import plaid_api
from datetime import timedelta
from datetime import datetime
from icecream import ic

import plaid
import json


def plaid_environment(plaid_env):
    if plaid_env == 'sandbox':
        host = plaid.Environment.Sandbox

    if plaid_env == 'development':
        host = plaid.Environment.Development

    if plaid_env == 'production':
        host = plaid.Environment.Production

    return host


def plaid_client(plaid_env, client_id, secret):
    config = plaid.Configuration(
        host=plaid_environment(plaid_env),
        api_key={
            'clientId': client_id,
            'secret': secret
        }
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))


def format_error(e):
    r = json.loads(e.body)
    error = {'error': {
        'status_code': e.status,
        'message': r['error_message'],
        'error_code': r['error_code'],
        'error_type': r['error_type']
    }
    }
    ic(error)
    return error


def plaid_transactions(access_token, client, timeframe):

    start_date = (datetime.now() - timedelta(days=timeframe))
    end_date = datetime.now()

    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date(),
            options=TransactionsGetRequestOptions()
        )

        r = client.transactions_get(request).to_dict()
        if 'error' in r:
            raise Exception(r['error']['message'])

        txn = {k: v for k, v in r.items()
               if k in ['accounts', 'item', 'transactions']}

        txn['transactions'] = [t for t in txn['transactions']
                               if not t['pending']]

    except plaid.ApiException as e:
        txn = format_error(e)

    finally:
        return txn


def plaid_bank_name(client, bank_id):
    '''
        Description:
        returns the bank name where the user holds his bank account

    Parameters:
        client (plaid.api.plaid_api.PlaidApi): plaid client info (api key, secret key, palid environment)
        bank_id (str): the Plaid ID of the institution to get details about

    Returns:
        bank_name (str): name of the bank uwhere user holds their fundings
    '''
    try:
        request = InstitutionsGetByIdRequest(
            institution_id=bank_id,
            country_codes=list(map(lambda x: CountryCode(x), ['US']))
        )

        r = client.institutions_get_by_id(request)
        r = r['institution']['name']

    except:
        r = None

    finally:
        return r
