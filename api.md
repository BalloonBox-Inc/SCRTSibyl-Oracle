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
        
    }
```

+ <span style="color:blue">**PLAID**</span> : credit score model based on Plaid account.

```
    POST /credit_score/plaid
```

Headers
```
    Content-Type: application/json
```

Body
```
    {
        "plaid_token": PLAID_ACCESS_TOKEN,
        "plaid_client_id": PLAID_CLIENT_ID,
        "plaid_client_secret": PLAID_CLIENT_SECRET,
        "keplr_token": KEPLER_TOKEN
    }
```

Response: **200**
```
    {
        
    }
```

---
## **Errors**
---
