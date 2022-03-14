# SECRET-SIBYL API

This documentation contains all APIs endpoints available.

The intensions of the public API is to offer the possibility for the Secret Network community to integrate their existing Plaid and Coinbase accounts with Sibyl Credit Score model and offer seemless credibility to their lenders.

By using of this API you agree with our [Terms and Conditions](https://).

---
## **Caution**
---
The API is in active development and we are changing things rapdily. Once we are ready to release a stable version of API we will notify the existing API owners.

---
## **Help Us**
---
Have you spotted a mistake in our API docs? Help us improve it by [letting us know](https://).

---
## **General**
---

+ All times provided are in UTC timezone.
+ 
+ 

---
## **Authentication**
---

Every endpoint is secured by User Oauth token, except our authentication endpoints, which are secured by Oauth Client key and secret. Note that there are certain permissions required on nested endpoints, details will be specified per each endpoint.

User oauth tokens to be sent via Authorization Bearer header:

```
    Authorization
```

---
## **Resources**
---

+ <span style="color:blue">**COINBASE**</span> : credit score model based on Coinbase account.

```
    POST /credit_score/coinbase
```

Headers
```
    Content-Type: application/json
```

Body
```
    {
        "coinbase_client_id" = COINBASE_CLIENT_ID',
        "coinbase_client_secret" = COINBASE_CLIENT_SECRET,
        "coinmarketcap_key" = COINMARKETCAP_KEY
        "keplr_token": KEPLER_TOKEN
    }
```

Response: **200**
```
    {
        'endpoint': '/credit_score/coinbase',
        'title': 'Credit Score',
        'status_code': 200,
        'status': 'Good',
        'timestamp': timestamp object,
        'score': float object,
        'feedback': json object,
        'message': string object
    }
                
```

+ <span style="color:blue">**PLAID**</span> : credit score model based on Plaid account.

```
    POST {base_url}/credit_score/plaid
```

Headers
```
    Content-Type: application/json
```

Body
```
    {
        "keplr_token": "49v5hja7-11ed-44cc-8q9q-0b3g567hhild",
        "plaid_token": "access-sandbox-49v5hja7-11ed-44cc-8q9q-0b3g567hhild",
        "plaid_client_id": "55e873tf849309090mm12345",
        "plaid_client_secret": "1234a12345b12345c1234de1f1g1g1"
    }
```

Response: **200**
```
    {
        "endpoint": "/credit_score/plaid",
        "feedback": {
            "advice": {
                "credit_error": false,
                "credit_exist": true,
                "diversity_error": false,
                "stability_error": false,
                "velocity_error": true
            },
            "score": {
                "bank_accounts": 10,
                "card_names": [
                    "Plaid diamond 12.5% apr interest credit card"
                ],
                "cum_balance": 50000,
                "loan_amount": 5000,
                "points": 628,
                "quality": "fair",
                "score_exist": true
            }
        },
        "message": "Your SCRTSibyl score is FAIR, with a total of 628 points, which qualifies you for a loan of up to $5000 USD. SCRTSibyl computed your score accounting for your Plaid diamond 12.5% apr interest credit card credit card your total current balance of $50000 and your 9 different bank accounts. An error occurred during computation of the metrics: velocity, and your score was rounded down. Try again later or log in using a different account.",
        "score": 628.2132,
        "status": "Good",
        "status_code": 200,
        "timestamp": "03-14-2022 19:04:12 GMT",
        "title": "Credit Score"
    }
```

---
## **Errors**
---
