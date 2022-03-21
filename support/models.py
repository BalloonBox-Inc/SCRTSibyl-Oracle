from support.metrics_plaid import *
from support.metrics_coinbase import *

# -------------------------------------------------------------------------- #
#                                Plaid Model                                 #
# -------------------------------------------------------------------------- #

def plaid_credit(txn, feedback):

    limit, feedback = credit_limit(txn, feedback)
    util_ratio, feedback = credit_util_ratio(txn, feedback)
    interest, feedback = credit_interest(txn, feedback)
    length, feedback = credit_length(txn, feedback)
    livelihood, feedback = credit_livelihood(txn, feedback)

    score = 0.45*limit \
        + 0.12*util_ratio \
        + 0.05*interest \
        + 0.26*length \
        + 0.12*livelihood 

    return score, feedback


def plaid_velocity(txn, feedback):

    withdrawals, feedback = velocity_withdrawals(txn, feedback)
    deposits, feedback = velocity_deposits(txn, feedback)
    net_flow, feedback = velocity_month_net_flow(txn, feedback)
    txn_count, feedback = velocity_month_txn_count(txn, feedback)
    slope, feedback = velocity_slope(txn, feedback)

    score = 0.16*withdrawals \
        + 0.25*deposits \
        + 0.25*net_flow \
        + 0.16*txn_count \
        + 0.18*slope 

    return score, feedback


def plaid_stability(txn, feedback):

    balance, feedback = stability_tot_balance_now(txn, feedback)
    feedback = stability_loan_duedate(txn, feedback)
    run_balance, feedback = stability_min_running_balance(txn, feedback)

    score = 0.70*balance + 0.30*run_balance

    return score, feedback


def plaid_diversity(txn, feedback):

    acc_count, feedback = diversity_acc_count(txn, feedback)
    profile, feedback = diversity_profile(txn, feedback)

    score = 0.40*acc_count + 0.60*profile

    return score, feedback

# -------------------------------------------------------------------------- #
#                               Coinbase Model                               #
# -------------------------------------------------------------------------- #

def coinbase_kyc(acc, txn, feedback):

    score, feedback = kyc(acc, txn, feedback)

    return score, feedback


def coinbase_history(acc, feedback):

    score, feedback = history_acc_longevity(acc, feedback)

    return score, feedback


def coinbase_liquidity(acc, txn, feedback):

    balance, feedback = liquidity_tot_balance_now(acc, feedback)
    run_balance, feedback = liquidity_avg_running_balance(acc, txn, feedback)

    score = 0.60*balance + 0.40*run_balance

    return score, feedback


def coinbase_activity(acc, txn, feedback):

    credit_volume, feedback = activity_tot_volume_tot_count(txn, 'credit', feedback)
    debit_volume, feedback = activity_tot_volume_tot_count(txn, 'debit', feedback)
    credit_consistency, feedback = activity_consistency(txn, 'credit', feedback)
    debit_consistency, feedback = activity_consistency(txn, 'debit', feedback)
    inception, feedback = activity_profit_since_inception(acc, txn, feedback)

    score = 0.2*credit_volume \
        + 0.2* debit_volume \
        + 0.2*credit_consistency \
        + 0.2*debit_consistency \
        + 0.2*inception 
    
    return score, feedback 
