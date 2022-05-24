import requests


def coinexchange_rate(coin_in, coin_out, api_key):
    url = f'https://rest.coinapi.io/v1/exchangerate/{coin_in}/{coin_out}'
    headers = {'X-CoinAPI-Key': api_key}

    try:
        r = requests.get(url, headers=headers).json()['rate']

    except Exception as e:
        r = str(e)

    return r
