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


def plaid_transactions(client, access_token, timeframe):

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

    except plaid.ApiException as e:
        r = format_error(e)

    finally:
        return r


def plaid_bank_name(client, bank_id, feedback):
    '''
        Description:
        returns the bank name where the user holds his bank account

    Parameters:
        client (plaid.api.plaid_api.PlaidApi): plaid client info (api key, secret key, palid environment)
        bank_id (str): the Plaid ID of the institution to get details about 
        feedback (dict): to write the bank name to

    Returns:
        bank_name (str): name of the bank uwhere user holds their fundings
    '''
    try:
        request = InstitutionsGetByIdRequest(
            institution_id=bank_id,
            country_codes=list(map(lambda x: CountryCode(x), ['US']))
        )  # hard code 'US' to be the country_code parameter

        r = client.institutions_get_by_id(request)
        feedback['diversity']['bank_name'] = r['institution']['name']

    # Always return a bank_name. If the name does not exist then return a None type
    except:
        feedback['diversity']['bank_name'] = None

    finally:
        return feedback
