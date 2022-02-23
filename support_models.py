from support_metrics_plaid import *


def plaid_credit(txn, feedback):

    mix, feedback = credit_mix(txn, feedback)
    limit, feedback = credit_limit(txn, feedback)
    util_ratio, feedback = credit_util_ratio(txn, feedback)
    interest, feedback = credit_interest(txn, feedback)
    length, feedback = credit_length(txn, feedback)
    livelihood, feedback = credit_livelihood(txn, feedback)

    score = 0.05*mix \
        + 0.15*limit \
        + 0.80*0.35*util_ratio \
        + 0.80*0.15*interest \
        + 0.80*0.40*length \
        + 0.80*0.10*livelihood \

    return score, feedback


def plaid_velocity(txn, feedback):

    withdrawals, feedback = velocity_withdrawals(txn, feedback)
    deposits, feedback = velocity_deposits(txn, feedback)
    net_flow, feedback = velocity_month_net_flow(txn, feedback)
    txn_count, feedback = velocity_month_txn_count(txn, feedback)
    slope, feedback = velocity_slope(txn, feedback)

    score = 0.05*withdrawals \
        + 0.15*deposits \
        + 0.40*net_flow \
        + 0.10*txn_count \
        + 0.30*slope \

    return score, feedback


def plaid_stability(txn, feedback):

    balance, feedback = stability_tot_balance_now(txn, feedback)
    run_balance, feedback = stability_min_running_balance(txn, feedback)

    score = 0.65*balance + 0.35*run_balance

    return score, feedback


def plaid_diversity(txn, feedback):

    acc_count, feedback = diversity_acc_count(txn, feedback)
    profile, feedback = diversity_profile(txn, feedback)

    score = 0.60*acc_count + 0.40*profile

    return score, feedback