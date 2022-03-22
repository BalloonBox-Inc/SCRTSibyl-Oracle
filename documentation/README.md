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
    POST {base_url}/credit_score/coinbase
```

Headers
```
    "Content-Type": "application/json"
```

Body
```
    {
        "keplr_token": your_keplr_token,
        "coinbase_access_token": your_coinbase_access_token,
        "coinbase_refresh_token": your_coinbase_refresh_token,
        "coinmarketcap_key": your_coinmarketcap_key
    }
```

Response: **200**
```
enum ScoreQuality {
  'very poor',
  'poor',
  'fair',
  'good',
  'very good',
  'excellent',
  'exceptional',
}

export interface IScoreResponseCoinbase {
  endpoint: '/credit_score/coinbase';
  feedback: {
    advice: {
      activity_error: boolean;
      history_error: boolean;
      kyc_error: boolean;
      liquidity_error: boolean;
    };
    score: {
      current_balance: number;
      loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
      loan_duedate: 3 | 4 | 5 | 6;
      points: number;
      quality: ScoreQuality;
      score_exist: boolean;
      wallet_age(days): number;
    };
  };
  message: string[];
  score: number;
  status_code: 200 | 400;
  status: 'success' | 'error';
  timestamp: string;
  title: 'Credit Score';
}
```


A Sample Response for Coinbase test account
```
{
    "endpoint": "/credit_score/coinbase",
    "feedback": {
        "advice": {
            "activity_error": false,
            "history_error": false,
            "kyc_error": false,
            "liquidity_error": false
        },
        "score": {
            "current_balance": null,
            "loan_amount": null,
            "loan_duedate": null,
            "points": null,
            "quality": null,
            "score_exist": false,
            "wallet_age(days)": null
        }
    },
    "message": "SCRTSibyl could not calculate your credit score because there is no active wallet nor transaction history in your Coinbase account. Try to log into Coinbase with a different account.",
    "score": 300.0,
    "status": "success",
    "status_code": 200,
    "timestamp": "03-22-2022 18:44:19 GMT",
    "title": "Credit Score"
}            
```

+ <span style="color:blue">**PLAID**</span> : credit score model based on Plaid account.

```
    POST {base_url}/credit_score/plaid
```

Headers
```
    "Content-Type": "application/json"
```

Body
```
    {
        "keplr_token": your_keplr_token
        "plaid_token": your_plaid_token,
        "plaid_client_id": your_plaid_client_id,
        "plaid_client_secret": your_plaid_client_secret
    }
```
Response: **200** (typescript)
```
enum ScoreQuality {
  'very poor',
  'poor',
  'fair',
  'good',
  'very good',
  'excellent',
  'exceptional',
}

export interface IScoreResponsePlaid {
  endpoint: '/credit_score/plaid';
  feedback: {
    advice: {
      credit_error: boolean;
      credit_exist: boolean;
      diversity_error: boolean;
      stability_error: boolean;
      velocity_error: boolean;
    };
    score: {
      bank_accounts: number;
      card_names: string[];
      cum_balance: number;
      loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
      loan_duedate: 3 | 4 | 5 | 6;
      points: number;
      quality: ScoreQuality;
      score_exist: boolean;
    };
  };
  message: string;
  score: number;
  status_code: 200 | 400;
  status: 'success' | 'error';
  title: 'Credit Score';
}
```



A Sample Response for Plaid Sandbox data
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
        "status": "good",
        "status_code": 200,
        "timestamp": "03-14-2022 19:04:12 GMT",
        "title": "Credit Score"
    }
```

---
## **Errors**
---
Note that error returns do not have score or feedback keys.
```
    {
        'endpoint': '/credit_score/plaid',
        'message': 'invalid client_id or secret provided',
        'status': 'error',
        'status_code': 400,
        'timestamp': '03-22-2022 17:56:19 GMT',
        'title': 'Credit Score'
    }
```
