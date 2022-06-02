from operator import mul
import numpy as np


def dot_product(l1, l2):
    return sum(map(mul, l1, l2))


def head_tail_list(lst):
    return lst[-1], lst[0]


def aggregate_currencies(ccy1, ccy2, fiats):
    ccy2 = {k: 1 for (k, v) in ccy2.items()
            if v == 0.01 or k in fiats}

    ccy1.update(ccy2)
    ccy1 = list(ccy1.keys())
    return ccy1


def immutable_array(arr):
    arr.flags.writeable = False
    return arr


def build_2d_matrix(size, scalars):

    matrix = np.zeros(size)
    scalars = [1/n for n in scalars]

    for m in range(matrix.shape[0]):
        for n in range(matrix.shape[1]):
            matrix[m][n] = round(scalars[0]*np.log10(m+1) +
                                 scalars[1]*np.log10(n+1), 2)
    return matrix


def plaid_params(params, score_range):

    due_date = immutable_array(
        np.array(params['metrics']['due_date']))
    duration = immutable_array(
        np.array(params['metrics']['duration']))
    count_zero = immutable_array(
        np.array(params['metrics']['count_zero']))
    count_invest = immutable_array(
        np.array(params['metrics']['count_invest']))
    volume_credit = immutable_array(
        np.array(params['metrics']['volume_credit'])*1000)
    volume_invest = immutable_array(
        np.array(params['metrics']['volume_invest'])*1000)
    volume_balance = immutable_array(
        np.array(params['metrics']['volume_balance'])*1000)
    flow_ratio = immutable_array(
        np.array(params['metrics']['flow_ratio']))
    slope = immutable_array(
        np.array(params['metrics']['slope']))
    slope_lr = immutable_array(
        np.array(params['metrics']['slope_lr']))
    activity_vol_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_volume']['shape']),
        tuple(params['matrices']['activity_volume']['scalars'])
    ))
    activity_cns_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_consistency']['shape']),
        tuple(params['matrices']['activity_consistency']['scalars'])
    ))
    credit_mix_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['credit_mix']['shape']),
        tuple(params['matrices']['credit_mix']['scalars'])
    ))
    diversity_velo_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['diversity_velocity']['shape']),
        tuple(params['matrices']['diversity_velocity']['scalars'])
    ))

    head, tail = head_tail_list(score_range)
    fico = (np.array(score_range[:-1])-tail) / (head-tail)
    fico_medians = [round(fico[i]+(fico[i+1]-fico[i]) / 2, 2)
                    for i in range(len(fico)-1)]
    fico_medians.append(1)
    fico_medians = immutable_array(np.array(fico_medians))

    count_lively = immutable_array(
        np.array([round(x, 0) for x in fico*25])[1:])
    count_txn = immutable_array(
        np.array([round(x, 0) for x in fico*40])[1:])
    volume_flow = immutable_array(
        np.array([round(x, 0) for x in fico*1500])[1:])
    volume_withdraw = immutable_array(
        np.array([round(x, 0) for x in fico*1500])[1:])
    volume_deposit = immutable_array(
        np.array([round(x, 0) for x in fico*7000])[1:])
    volume_min = immutable_array(
        np.array([round(x, 0) for x in fico*10000])[1:])
    credit_util_pct = immutable_array(
        np.array([round(x, 2) for x in reversed(fico*0.9)][:-1]))
    frequency_interest = immutable_array(
        np.array([round(x, 2) for x in reversed(fico*0.6)][:-1]))

    r = [due_date, duration, count_zero, count_invest, volume_credit, volume_invest, volume_balance, flow_ratio, slope, slope_lr, activity_vol_mtx, activity_cns_mtx,
         credit_mix_mtx, diversity_velo_mtx, fico_medians, count_lively, count_txn, volume_flow, volume_withdraw, volume_deposit, volume_min, credit_util_pct, frequency_interest]
    return r


def coinbase_params(params, score_range):

    due_date = immutable_array(
        np.array(params['metrics']['due_date']))
    duration = immutable_array(
        np.array(params['metrics']['duration']))
    volume_balance = immutable_array(
        np.array(params['metrics']['volume_balance'])*1000)
    volume_profit = immutable_array(
        np.array(params['metrics']['volume_profit'])*1000)
    count_txn = immutable_array(
        np.array(params['metrics']['count_txn']))
    activity_vol_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_volume']['shape']),
        tuple(params['matrices']['activity_volume']['scalars'])
    ))
    activity_cns_mtx = immutable_array(build_2d_matrix(
        tuple(params['matrices']['activity_consistency']['shape']),
        tuple(params['matrices']['activity_consistency']['scalars'])
    ))

    head, tail = head_tail_list(score_range)
    fico = (np.array(score_range[:-1])-tail) / (head-tail)
    fico_medians = [round(fico[i]+(fico[i+1]-fico[i]) / 2, 2)
                    for i in range(len(fico)-1)]
    fico_medians.append(1)
    fico_medians = immutable_array(np.array(fico_medians))

    r = [due_date, duration, volume_balance, volume_profit,
         count_txn, activity_vol_mtx, activity_cns_mtx, fico_medians]
    return r
