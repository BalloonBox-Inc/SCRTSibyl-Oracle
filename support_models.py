from support_metrics import *


# Account for first metric: 'Credit' 
def plaid_credit(tx):

    mix = credit_mix(tx)
    lim = credit_limit(tx)
    util = credit_util_ratio(tx)
    int = credit_interest(tx)
    leng = credit_length(tx)
    liv = credit_livelihood(tx)

    score = 0.05*mix       \
        + 0.15*lim         \
        + 0.80*0.40*util   \
        + 0.80*0.15*int    \
        + 0.80*0.35*leng   \
        + 0.80*0.10*liv    \

    return score



# Account for first metric: 'Velocity' 
def plaid_velocity(tx):

    wit = velocity_withdrawals(tx)
    dep = velocity_deposits(tx)
    flow = velocity_month_net_flow(tx)
    cnt = velocity_month_txn_count(tx)
    slo = velocity_slope(tx)

    score = 0.05*wit  \
        + 0.15*dep    \
        + 0.40*flow   \
        + 0.10*cnt    \
        + 0.30*slo    \

    return score



# Account for first metric: 'Stability' 
def plaid_stability(tx):

    bal = stability_tot_balance_now(tx)
    run = stability_min_running_balance(tx)

    score = 0.35*bal    \
        + 0.65*run      \

    return score



# Account for first metric: 'Diversity' 
def plaid_diversity(tx):

    acc = diversity_acc_count(tx)
    pro = diversity_profile(tx)

    score = 0.60*acc   \
        + 0.40*pro     \

    return score