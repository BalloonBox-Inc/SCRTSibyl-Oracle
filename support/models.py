from support.metrics_plaid import *
from support.metrics_coinbase import *
from support.metrics_binance import *
from config.params import *
from support.helper import *

# -------------------------------------------------------------------------- #
#                                Plaid Model                                 #
# -------------------------------------------------------------------------- #


def plaid_credit(txn, feedback):

    limit, feedback = credit_limit(txn, feedback)
    util_ratio, feedback = credit_util_ratio(txn, feedback)
    interest, feedback = credit_interest(txn, feedback)
    length, feedback = credit_length(txn, feedback)
    livelihood, feedback = credit_livelihood(txn, feedback)

    a = plaid_credit_model_weights()
    b = [limit, util_ratio, interest, length, livelihood]

    score = dot_product(a, b)

    return score, feedback


def plaid_velocity(txn, feedback):

    withdrawals, feedback = velocity_withdrawals(txn, feedback)
    deposits, feedback = velocity_deposits(txn, feedback)
    net_flow, feedback = velocity_month_net_flow(txn, feedback)
    txn_count, feedback = velocity_month_txn_count(txn, feedback)
    slope, feedback = velocity_slope(txn, feedback)

    a = plaid_velocity_model_weights()
    b = [withdrawals, deposits, net_flow, txn_count, slope]

    score = dot_product(a, b)

    return score, feedback


def plaid_stability(txn, feedback):

    balance, feedback = stability_tot_balance_now(txn, feedback)
    feedback = stability_loan_duedate(txn, feedback)
    run_balance, feedback = stability_min_running_balance(txn, feedback)

    a = plaid_stability_model_weights()
    b = [balance, run_balance]

    score = dot_product(a, b)

    return score, feedback


def plaid_diversity(txn, feedback):

    acc_count, feedback = diversity_acc_count(txn, feedback)
    profile, feedback = diversity_profile(txn, feedback)

    a = plaid_diversity_model_weights()
    b = [acc_count, profile]

    score = dot_product(a, b)

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
    feedback = liquidity_loan_duedate(txn, feedback)
    run_balance, feedback = liquidity_avg_running_balance(acc, txn, feedback)

    a = coinbase_liquidity_model_weights()
    b = [balance, run_balance]

    score = dot_product(a, b)

    return score, feedback


def coinbase_activity(acc, txn, feedback):

    credit_volume, feedback = activity_tot_volume_tot_count(
        txn, 'credit', feedback)
    debit_volume, feedback = activity_tot_volume_tot_count(
        txn, 'debit', feedback)
    credit_consistency, feedback = activity_consistency(
        txn, 'credit', feedback)
    debit_consistency, feedback = activity_consistency(txn, 'debit', feedback)
    inception, feedback = activity_profit_since_inception(acc, txn, feedback)

    a = coinbase_activity_model_weights()
    b = [credit_volume, debit_volume,
         credit_consistency, debit_consistency, inception]

    score = dot_product(a, b)

    return score, feedback

# -------------------------------------------------------------------------- #
#                               Binance Model                                #
# -------------------------------------------------------------------------- #
