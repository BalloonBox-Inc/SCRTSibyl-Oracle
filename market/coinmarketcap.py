import requests


def coinmarketcap_currencies(api_key, limit):
    '''
    Description:
        returns a dict of top-ranked currencies on coinmarketcap

    Parameters:
        api_key (str): bearer token to authenticate into coinmarketcap API
        limit (float): number of top currencies you want to keep

    Returns:
        top_currencies (dict): ticker-value pairs for top coinmarketcap currencies
    '''
    try:
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }

        params = {
            'start': '1',
            'limit': str(limit),
            'convert': 'USD'
        }

        r = requests.get(url, headers=headers, params=params).json()

        top_currencies = dict(
            [(n['symbol'], n['quote']['USD']['price']) for n in r['data']])

    except Exception as e:
        top_currencies = str(e)

    return top_currencies
