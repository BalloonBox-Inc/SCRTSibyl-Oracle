# 🚀 SCRT SYBIL

![scrt sybil image](./images/logo_horizontal.png)

## Credit Score Model

SCRTSibyl is an oracle for credit score checks developed for the Secret Network. Our oracle returns a numerical, private, and encrypted credit score affirming users' credibility and trustworthiness within the Secret network ecosystem. We designed this dapp with one specific use case in mind: P2P micro-lending, which is facilitating lending and borrowing of microloans ranging between $1-25K USD. Running a credit score check on a user you are considering lending money to or borrowing money from, will inform you whether and how much a user can pay back upon loan issuance. The dapp works as follow: it acquires user's financial data by integrating with two validators ([Plaid](https://dashboard.plaid.com/overview) & [Coinbase](https://developers.coinbase.com/)); it runs an algorithm on given data to compute a score representing the financial health of a user; it writes the score to the Secret blockchain via a CosmWasm smart contract; it makes the score available to service providers (i.e., loan issuers) by releasing permission/viewing Secret keys. 
Ultimately, this will incentivize on-chain traffic, it will affirm the reputation of those users requesting a credit score, and it will execute a credit score check to validate their credibility, while also preserving their privacy. 

This Git Repo specifically focuses on the credit scoring algorithm of our SCRTSibyl oracle. 


### Executing Locally


### Credentials Required :key: :lock:

You'll need to create a Developer Coinmarket Cap API Key, following the CoinMarketCap Developers guide [here.](https://coinmarketcap.com/api/documentation/v1/#section/Introduction)

Create a .env.local file in your root folder: 

```
PLAID_CLIENT_ID=your_client_id
PLAID_CLIENT_SECRET=your_sandbox_key
PLAID_ACCESS_TOKEN=your_unique_access_token
PLAID_URL_SANDBOX="sandbox.plaid.com"

COINBASE_CLIENT_ID=your_client_Id
COINBASE_CLIENT_SECRET=your_client_secret

COINMARKETCAP_KEY=your_coinmarketcap_key
```

---


## Credit Score Model :shipit:

### Algorithm Architecture :page_facing_up:
Undertsand the credit score model at a glance. We developed two distinct models, one for each of our chosen validators, namely Plaid & Coinbase.

 -  :dollar: [**Plaid**](./images/logic_plaid.png) model

 -  :moneybag: [**Coinbase**](./images/logic_coinbase.png) model 

 
## Interpreting Your Score :mag:

![](./images/ranges.png)

 





