# 🚀 SCRT SIBYL API
![scrt sibyl image](/SCRTSibyl-Oracle/images/logo_horizontal.png)

This documentation contains all APIs endpoints featured in our SCRTSibyl Dapp.

Imagine you are a user who owns a Keplr wallet and wants to be issued a micro-loan.
Public APIs allow users to:
+ integrate their existing Plaid and Coinbase accounts with the SCRTSibyl Credit Score model, 
+ undergo a credit score check,
+ validate their credibility to lenders issuing them a loan. 

When using the SCRTSibyl API you agree with our [Terms and Conditions](https://) :copyright:.

---


### Beware 

:clock4: All times provided are in UTC timezone.

### Authentication 

:electric_plug: Every endpoint is secured by either a User Oauth token or by the pair Oauth Client key & secret key.

### Help Us 

:bellhop_bell: Have you spotted a mistake in our API docs? Help us improve it by [letting us know](https://www.balloonbox.io/contact).

### Caution 

:warning: The API is in active development and we are changing things rapdily. Once we are ready to release a stable version of API we will notify the existing API owners.




## Resources

---
[<span>**COINBASE**</span>](https://coinmarketcap.com/) : credit score model based on Coinbase account.
---

```
    POST {base_url}/credit_score/coinbase
```

Headers
```
    {"Content-Type": "application/json"}
```

Body
```
    {
        "keplr_token": "YOUR_KEPLER_TOKEN",
        "coinbase_access_token": "YOUR_COINBASE_ACCESS_TOKEN",
        "coinbase_refresh_token": "YOUR_COINBASE_REFRESH_TOKEN",
        "coinmarketcap_key": "YOUR_COINMARKETCAP_KEY"
    }
```

Response: **200**

Generalized Typescript response
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
        points: number;  // integer in range [300, 900]
        quality: ScoreQuality;
        score_exist: boolean;
        wallet_age(days): number;
        };
    };
    message: string[];
    score: number;
    status: 'success' | 'error';
    status_code: 200 | 400;
    timestamp: string[];
    title: 'Credit Score';
    }
```

Sample response from a Coinbase test account
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

---
[<span>**PLAID**</span>](https://plaid.com/) : credit score model based on Plaid account.
---

```
    POST {base_url}/credit_score/plaid
```

Headers
```
    {"Content-Type": "application/json"}
```

Body
```
    {
        "keplr_token": "YOUR_KEPLER_TOKEN"
        "plaid_token": "YOUR_PLAID_TOKEN",
        "plaid_client_id": "YOUR_PLAID_CLIENT_ID",
        "plaid_client_secret": "YOUR_CLIENT_SECRET",
        "coinmarketcap_key": "YOUR_COINMARKETCAP_KEY"
    }
```

Response: **200**

+ Typescript response
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
        card_names: list(string[]);
        cum_balance: number;
        loan_amount: 500 | 1000 | 5000 | 10000 | 15000 | 20000 | 25000;
        loan_duedate: 3 | 4 | 5 | 6;
        points: number; // integer in range [300, 900]
        quality: ScoreQuality;
        score_exist: boolean;
        };
    };
    message: string[];
    score: number;
    status: 'success' | 'error';
    status_code: 200 | 400;
    timestamp: string[];
    title: 'Credit Score';
    }
```

+ Sample response from Plaid Sandbox environment
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
                "bank_accounts": 9,
                "card_names": [
                    "Plaid diamond 12.5% apr interest credit card"
                ],
                "cum_balance": 44520,
                "loan_amount": 5000,
                "loan_duedate": 6,
                "points": 639,
                "quality": "fair",
                "score_exist": true
            }
        },
        "message": "Your SCRTSibyl score is FAIR - 639 points. This score qualifies you for a short term loan of up to $5,000 USD (1,011 SCRT) over a recommended pay back period of 6 monthly installments. Part of your score is based on the transaction history of your Plaid diamond 12.5% apr interest credit card. Your total current balance is $44,520 USD across all accounts. An error occurred while computing the score metric called velocity. As a result, your score was rounded down. Try again later or select an alternative bank account if you have one.",
        
        "score": 639,
        "status": "success",
        "status_code": 200,
        "timestamp": "03-24-2022 17:34:52 GMT",
        "title": "Credit Score"
    }
```

## **Errors**

Note that error returns do not have `score` or `feedback` keys. The error description will appear under the message key.

Sample error response from Plaid Sandbox environment
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
