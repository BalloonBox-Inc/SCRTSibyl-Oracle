import numpy as np
from config.params import *


def calc_risk(score):

    # score array
    score_arr = score_range()
    score_arr = np.insert(score_arr, 0, 300)  # min
    score_arr = np.append(score_arr, 900)  # max

    # loan array
    loan_arr = loan_range()
    loan_arr = np.insert(loan_arr, 0, 0)  # min
    loan_arr = loan_arr.astype(int)

    # when score is equal to one of the bin separators, treat it as if it was in the lower bin
    if score in score_arr and score >= 301:
        score = score - 1

    # split score bin equally into three qualitative levels of risk
    lower_score = score_arr[score_arr <= score][-1]
    upper_score = score_arr[score_arr >= score][0]
    delta_score = upper_score - lower_score
    risk_split = delta_score / 3

    if score <= lower_score + risk_split:
        risk_level = 'high'

    elif score <= lower_score + 2*risk_split:
        risk_level = 'medium'

    else:
        risk_level = 'low'

    # loan amount is equal to the maximum amount of the loan bin
    index, = np.where(score_arr == lower_score)
    loan_amount = loan_arr[index+1][0]

    # format risk output
    return {'loan_amount': loan_amount, 'risk_level': risk_level}
