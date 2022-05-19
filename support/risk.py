import numpy as np
from config.params import *


def calc_risk(score):

    # score
    score_arr = score_range()
    score_arr = np.insert(score_arr, 0, 300)  # min
    score_arr = np.append(score_arr, 900)  # max

    # loan
    loan_arr = loan_range()
    loan_arr = np.insert(loan_arr, 0, 0)  # min
    loan_arr = loan_arr.astype(int)

    # when score is equal to one of the bin separators
    if score in score_arr:
        index, = np.where(score_arr == score)[0]

        if index == 0:
            mid_risk = loan_arr[0]
            low_risk = mid_risk
            high_risk = mid_risk + (0.95 * ((loan_arr[1] - mid_risk) / 2))

        elif index == score_arr.size-1:
            mid_risk = loan_arr[-1]
            low_risk = mid_risk - (0.95 * ((mid_risk - loan_arr[-2]) / 2))
            high_risk = mid_risk

        else:
            mid_risk = loan_arr[index]
            low_risk = mid_risk - (0.95 * ((mid_risk - loan_arr[index-1]) / 2))
            high_risk = mid_risk + \
                (0.95 * ((loan_arr[index+1] - mid_risk) / 2))

    # when score is in between two bin separators
    else:
        lower_score = score_arr[score_arr <= score][-1]
        upper_score = score_arr[score_arr >= score][0]
        delta_score = upper_score - lower_score
        index, = np.where(score_arr == lower_score)

        lower_loan = loan_arr[index][0]
        upper_loan = loan_arr[index+1][0]
        delta_loan = upper_loan - lower_loan

        # mid-risk
        mid_risk = (((score - lower_score) * delta_loan) /
                    delta_score) + lower_loan

        # low and high risk
        arr = np.array([lower_loan, upper_loan])
        nearest = arr[np.abs(arr - mid_risk).argmin()]
        delta_risk = 0.95 * (abs(mid_risk - nearest))
        low_risk = mid_risk - delta_risk
        high_risk = mid_risk + delta_risk

    # format risk output
    risk = {'low_risk': low_risk, 'mid_risk': mid_risk, 'high_risk': high_risk}
    risk = {k: int(v) for k, v in risk.items()}

    return risk
