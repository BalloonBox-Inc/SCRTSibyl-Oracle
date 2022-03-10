import requests


def top_currencies(api_key, limit):
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
        
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        r = requests.get(url, headers=headers, params=params).json()
    
        output = dict([(n['symbol'], n['quote']['USD']['price']) for n in r['data']])
    
    except Exception as e:
        output = str(e)
    
    return output