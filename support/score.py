from support.models import *
from support.helper import *


def plaid_score(score_range, feedback, model_weights, model_penalties, metric_weigths, params, txn):
    '''
    params = [
        due_date, duration, count_zero, count_invest, volume_credit, volume_invest,
        volume_balance, flow_ratio, slope, slope_lr, activity_vol_mtx,
        activity_cns_mtx, credit_mix_mtx, diversity_velo_mtx, fico_medians, count_lively,
        count_txn, volume_flow, volume_withdraw, volume_deposit, volume_min, 
        credit_util_pct, frequency_interest
    ]
    '''
    params = plaid_params(params, score_range)

    credit, feedback = credit_mix(
        txn, feedback, params[1], params[2], params[12])

    if credit == 0:
        velocity, feedback = plaid_velocity(
            txn, feedback, metric_weigths, params)
        stability, feedback = plaid_stability(
            txn, feedback, metric_weigths, params)
        diversity, feedback = plaid_diversity(
            txn, feedback, metric_weigths, params)

        a = list(model_penalties.values())

    else:
        credit, feedback = plaid_credit(
            txn, feedback, metric_weigths, params)
        velocity, feedback = plaid_velocity(
            txn, feedback, metric_weigths, params)
        stability, feedback = plaid_stability(
            txn, feedback, metric_weigths, params)
        diversity, feedback = plaid_diversity(
            txn, feedback, metric_weigths, params)

        a = list(model_weights.values())

    b = [credit, velocity, stability, diversity]

    head, tail = head_tail_list(score_range)
    score = tail + (head-tail)*(dot_product(a, b))

    return score, feedback


def coinbase_score(score_range, feedback, model_weights, metric_weigths, params, acc, txn):
    '''
    params = [
        due_date, duration, volume_balance, volume_profit, count_txn, activity_vol_mtx, 
        activity_cns_mtx, fico_medians
    ]
    '''
    params = coinbase_params(params, score_range)

    kyc, feedback = coinbase_kyc(
        acc, txn, feedback)
    history, feedback = coinbase_history(
        acc, feedback, params)
    liquidity, feedback = coinbase_liquidity(
        acc, txn, feedback, metric_weigths, params)
    activity, feedback = coinbase_activity(
        acc, txn, feedback, metric_weigths, params)

    a = list(model_weights.values())
    b = [kyc, history, liquidity, activity]

    head, tail = head_tail_list(score_range)
    score = tail + (head-tail)*(dot_product(a, b))

    return score, feedback
