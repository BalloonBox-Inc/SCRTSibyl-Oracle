import requests


def coinmarketcap_coins(api_key, limit):
    '''
    Description:
        returns a dict of top-ranked cryptos on coinmarketcap

    Parameters:
        api_key (str): bearer token to authenticate into coinmarketcap API
        limit (float): number of top cryptos you want to keep

    Returns:
        top_cryptos (dict): ticker-value pairs for top coinmarketcap cryptos
    '''
    try:
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }

        params = {
            'start': '1',
            'limit': str(limit),
            'convert': 'USD'
        }

        # Define url for coinmarketcap API
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        # Run GET task to fetch best cryptos from coinmarketcap API
        r = requests.get(url, headers=headers, params=params).json()

        # Keep only top cryptos (ticker and USD-value)
        top_cryptos = dict(
            [(n['symbol'], n['quote']['USD']['price']) for n in r['data']])

    except Exception as e:
        top_cryptos = str(e)

    return top_cryptos
