# :trident: SCRT SYBIL - Credit Score Model

![scrt sybil image](./public/images/readmeImage.png)

SCRTSibyl is an oracle for credit score checks developed for the Secret Network. Our oracle returns a numerical, private, and encrypted credit score affirming users' credibility and trustworthiness within the Secret network ecosystem. We designed this dapp with one specific use case in mind: P2P micro-lending, which is facilitating lending and borrowing of microloans ranging between $1-25K USD. Running a credit score check on a user you are considering lending money to or borrowing money from, will inform you whether and how much a user can pay back upon loan issuance. The dapp works as follow: it acquires user's financial data by integrating with two validators (Plaid & Coinbase); it runs an algorithm on given data to compute a score representing the financial health of a user; it writes the score to the Secret blockchain via a CosmWasm smart contract; it makes the score available to service providers (i.e., loan issuers) by releasing permission/viewing Secret keys. 
Ultimately, this will incentivize on-chain traffic, it will affirm the reputation of those users requesting a credit score, and it will execute a credit score check to validate their credibility, while also preserving their privacy. 

This Git Repo specifically focuses on the credit scoring algorithm of our SCRTSibyl oracle. 


---

### Executing Locally


### Credentials Required :lock: :key:
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


## Credit Score Model

### Algorithm Architecture :page_facing_up:
Undertsand the credit score model at a glance. We developed two distinct models, one for each of our chosen validators, namely Plaid & Coinbase.

#### Plaid
![](https://github.com/BalloonBox-Inc/scrt-network-oracle/blob/dev/pix/credit_score_logic_plaid.png)

#### Coinbase
![](https://github.com/BalloonBox-Inc/scrt-network-oracle/blob/dev/pix/credit_score_logic_coinbase.png)



---

## Interpreting Your Score
![](https://github.com/BalloonBox-Inc/scrt-network-oracle/blob/dev/pix/credit_score_range.png)

 

### Timeline 🏁
2022/1 and 2022/2

|Mon|Tue|Wed|Thu|Fri|Sat|Sun|
|:----:|:----:|:----:|:----:|:----:|:----:|:----:|
|17<br/>  `milestone#1 start date`|18<br/> `Access Plaid Quiskstart&Sandbox` |19|20<br/> `Plaid Algo design`|21<br/> `Plaid Algo Team brainstorm`|22|23|
|24<br/>  `get 10PlaidDev items`|25<br/> `Understand Plaid data`|26<br/> `Plaid Algo`|27<br/> `Plaid Algo`|28<br/> `📌 Plaid Algo draft due` |29|30|
|31<br/> `Plaid Algo`|1<br/> `Plaid Algo`|2<br/> `Plaid Algo`|3<br/> `Plaid Algo wiring. Run it on test data`|4<br/> `📌  finish building Plaid Algo` **due**|5|6|
|7<br/> `Coinbase Algo`|8<br/> `Coinbase Algo`|9<br/> `Coinbase Algo` |10<br/> `Coinbase Algo`|11<br/> `📌 finish building Coinbase Algo` **due**|12|13|
|14<br/> `Algos testing`|15<br/> `Algos testing`|16<br/> `Algos testing`|17<br/> `Algo deployment & wiring`|18<br/> `📌  Anticipated Milestone 1` **due**|19|20|
|21|22|23|24|25|26|27| 
|🔥 28 🔥 <bd/>  `milestone#1` **due**|29|30|31||||






