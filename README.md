# 🚀 SCRT SIBYL

![scrt sibyl image](./images/logo_horizontal.png)

## This Repo
This GitHub repo contains the codebase of the SCRTSibyl credit score algorithm. The code features 2 validators, 3 API integrations, 10 score metrics, and 25+ functions to calculate users' credit scores. The front end of the SCRTSibyl DApp, after fetching the user's data, passes it to the algorithm to execute and return a score. The Rust smart contract is stored at the [SCRTSibyl-Oracle](https://github.com/BalloonBox-Inc/SCRTSibyl-Contract) repo, whereas the Next.js frontend is found at [scrt-network-oracle-client](https://github.com/BalloonBox-Inc/scrt-network-oracle-client). The tree for the repo is:

```
.
├── LICENSE
├── Procfile
├── README.md
├── app.py
├── app_route.py
├── data
│   ├── README.md
│   ├── test_user_coinbase.json
│   └── test_user_plaid.json
├── demo.py
├── documentation
│   └── README.md
├── feedback
│   └── message.py
├── images
│   ├── README.md
│   ├── logic_coinbase.png
│   ├── logic_plaid.png
│   ├── logo_horizontal.png
│   └── ranges.png
├── interpret.ipynb
├── metrics_coinbase.ipynb
├── metrics_plaid.ipynb
├── optimization
│   └── performance.py
├── requirements.txt
├── runtime.py
├── support
│   ├── __init__.py
│   ├── metrics_coinbase.py
│   ├── metrics_plaid.py
│   ├── models.py
│   ├── score.py
│   └── tests
│       ├── README.md
│       ├── __init__.py
│       ├── test_coinbase.py
│       └── test_plaid.py
├── unit_tests.py
├── validator_api
│   ├── coinbase.py
│   ├── coinmarketcap.py
│   └── plaid.py
└── wsgi.py
```


## At a Glance
SCRTSibyl is an oracle for credit scoring developed for the Secret Network. The oracle returns a numerical, private, and encrypted credit score affirming users' credibility and trustworthiness within the Secret Network ecosystem. The DApp was designed with one specific use case in mind: unsecured P2P micro-lending, which is facilitating lending and borrowing of microloans ranging between $1-25K USD. The Sibyl does not require any type of collaterals -hence unsecured-, but rather the lender approves the loans based on a borrower's creditworthiness affirmed by the SCRTsibyl oracle. Running a credit score check on a user you are considering lending money to or borrowing money from, will inform you whether and how much a user can pay back upon loan issuance. 

The DApp works as follow: 
 - it acquires user's financial data by integrating with two validators ([Plaid](https://dashboard.plaid.com/overview) & [Coinbase](https://developers.coinbase.com/))
 - it runs an algorithm on given data to compute a score representing the financial health of a user
 - it writes the score to the Secret blockchain via a CosmWasm smart contract
 - it makes the score available to service providers (i.e., loan issuers) by releasing Secret [permission keys](https://github.com/SecretFoundation/SNIPs/blob/master/SNIP-24.md#secretd). 

Ultimately, this will incentivize on-chain traffic, it will affirm the reputation of those users requesting a credit score, and it will execute a credit score check to validate their credibility, while also preserving their privacy. 

 ---

## Execute Locally
 * download or clone the repo to your machine
 * install dependancies 
 * set up ```.env``` file 
 * execute 


### Package Manager Required :package:
pip or conda

Run in local terminal the following command:
```bash
git clone  ... my-project-name
cd my-project-name
```

Run *either* of the command below to install dependencies:
```bash
pip install -r requirements.txt                                 # using pip
conda create --name <env_name> --file requirements.txt          # using Conda
```


### Credentials Required :old_key: :lock:

If you want to spin up the entire DApp on your local machine, then follow the guideline found [here](https://github.com/BalloonBox-Inc/scrt-network-oracle-client#readme).

If you want to test the algorithm alone (independently from the DApp frontend), then continue reading this page and follow the step-by-step guide below. You'll need to create a Developer CoinMarketCap API Key, following the CoinMarketCap Developers guide [here](https://coinmarketcap.com/api/documentation/v1/#section/Introduction). In addition, you'll need either a Plaid or Coinbase account or (ideally) both. If you don't own one yet, you can create an account [here](https://dashboard.plaid.com/signin) and [here](https://www.coinbase.com/signup), respectively and then retrieve your Plaid [keys](https://dashboard.plaid.com/team/keys) and your Coinbase [keys](https://www.coinbase.com/settings/api). For Coinbase, you'll need to generate a new set of API keys. Do so, following this flow: `Coinbase` -> `settings` -> `API` -> `New API Key`.

Next, create a ```.env``` local file in your root folder: 

```bash
PLAID_CLIENT_ID=your_client_id
PLAID_CLIENT_SECRET=your_secret_sandbox_key
PLAID_ACCESS_TOKEN=your_unique_access_token

OINBASE_CLIENT_ID=your_coinbase_id
OINBASE_CLIENT_SECRET=your_coinbase_secret_key

COINMARKETCAP_KEY=your_coinmarketcap_key
```

### Run Locally
`cd` into the local directory where you cloned SCRTSibyl_Oracle. To run the credit score algorithm locally as a stand-alone Python project execute this command in terminal. Ensure you are in your project root

```bash
cd my-project-name
python demo.py
```

> :warning: the oracle will execute properly, only if you set up a correct and complete `.env` file.


## Credit Score Model 

### Algorithm Architecture :page_facing_up:
Understand the credit score model at a glance. 

There are two distinct models, one for each of our chosen validators, namely Plaid & Coinbase.

[**Plaid model**](./images/logic_plaid.png) diagram and features:
- :curling_stone: analyze 5 years of transaction history
- :gem: dynamically select user's best credit card products
- :dart: detect recurring deposits and withdrawals (monthly)
- :hammer_and_wrench: deploy linear regression on minimum running balance over the past 24 months
- :magnet: auto-filter & discard micro transactions
- :pushpin: inspect loan, investment, and saving accounts

[**Coinbase model**](./images/logic_coinbase.png) diagram and features:
- :bell: check for user KYC status
- :key: live fetch of top 25 cryptos by market cap via [CoinMarketCap](https://coinmarketcap.com/) API
- :fire: dynamically select user's best crypto wallets
- :closed_lock_with_key: auto-convert any currency to USD in real-time
- :bulb: analyze all transactions since Coinbase account inception
- :moneybag: compute user's net profit
 
 
  
## Interpret Your Score :mag:

SCRTSibyl returns to the user a numerical score ranging from 300-900 points. The score is partitioned into categorical bins (very poor | poor | fair | good | very good | excellent | exceptional), which describe the score qualitatively (see fuel gauge in the diagram below). Every bin is associated with a USD equivalent, which represents the maximum loan amount in USD that a user qualifies for, based on SCRTSibyl oracle calculation. Lastly, the SCRTSibyl also returns the estimated payback period, namely the expected time it will take for the user to pay back the loan. The loan terms (loan amount, qualitative descriptor, and payback period) are algorithmic recommendations, and, therefore, they are not prescriptive. Although we strongly advise lenders and borrowers to consider the SCRTSibyl Oracle's parameters, we also encourage them to stipulate loan terms to best suit their needs. 
![](./images/ranges.png) 


### Data Privacy

We developed SCRTSibyl with data privacy and security in mind. That's why our DApp is not storing any Plaid banking data or Coinbase data at all (no on-premise, neither remote database nor cloud storage). The API access the data to run it through the algorithm in the backend so that the frontend never interacts with raw and confidential data. Furthermore, the DApp only writes to the Secret Network blockchain -via a Rust smart contract- only your numerical score and a qualitative descriptor about the score. This ensures both lightweight (hence low gas fee) of the smart contract as well as data confidentiality so that the user is in charge of his own data from start to end.  

### Unit tests :pencil2: :black_nib: :page_facing_up:

The algorithm has undergone extensive unit testing. To execute these tests yourself, run the following command in terminal, from the root folder of this Git repo:

```bash
python -m unittest -v unit_tests                # for both Coinbase & Plaid
```

> :warning: both Coinbase and Plaid `unittest` relies on imported test data (_json_ files). We crafted two fake and anonimized test data-sets with the explicit goal of executing unit tests. Find these two data sets in the `data` directory, under the names of `test_user_coinbase.json` and `test_user_plaid.json`, respectively. 







