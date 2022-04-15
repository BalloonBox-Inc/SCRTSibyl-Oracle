from app_route import *
from local.local_helper import str_to_date
from support.metrics_coinbase import *
import unittest


# -------------------------------------------------------------------------- #
#                                  FIXTURES                                  #
# -------------------------------------------------------------------------- # 

# good data
good_fb = create_feedback_coinbase()
good_acc = str_to_date(json.load(open('test_user_coinbase.json'))['accounts'], good_fb)
good_tx = json.load(open('test_user_coinbase.json'))['transactions']

# empty data
empty_fb = []
empty_acc = []
empty_tx = [] 




# -------------------------------------------------------------------------- #
#                                TEST CASES                                  #
# -------------------------------------------------------------------------- # 
class TestMetrics(unittest.TestCase):


    def test_kyc(self):
        '''
        - ensure the output is always a tuple (int, dict)
        - ensure the output is never NoneType, even when parsing NoneTypes
        - ensure returns full score of 1 when good args are passed to the fn
        '''
        bad_fb = good_fb.pop('kyc', None)
        badkyc = kyc(None, None, bad_fb)

        self.assertIsInstance(badkyc, tuple)  
        self.assertIsInstance(badkyc[0], int)
        self.assertIsInstance(badkyc[1], dict)
        self.assertIsNotNone(kyc(None, None, None)) 
        self.assertEqual(kyc(good_acc, good_tx, good_fb)[0], 1) 


    def test_history_acc_longevity(self):
        '''
        - variable 'age' should be a non-negative of type: int or float
        - if there's no account, the score should be 0
        '''
        history_acc_longevity(good_acc, good_fb)

        self.assertGreaterEqual(history_acc_longevity.age, 0) 
        self.assertIsInstance(history_acc_longevity.age, (int, float))
        self.assertEqual(history_acc_longevity(empty_acc, good_fb)[0], 0) 


    def test_liquidity_tot_balance_now(self):
        '''
        - empty account should result in 'no balance' error
        '''
        self.assertRegex(liquidity_tot_balance_now(empty_acc, good_fb)[1]['liquidity']['error'], 'no balance')


    def test_liquidity_loan_duedate(self):
        '''
        - duedate should be at most 6 months
        '''
        self.assertLessEqual(liquidity_loan_duedate(good_tx, good_fb)['liquidity']['loan_duedate'], 6)


    def test_liquidity_avg_running_balance(self):
        '''
        - no tx yields a 'no tx' error
        '''
        self.assertRegex(liquidity_avg_running_balance(good_acc, empty_tx, good_fb)[1]['liquidity']['error'], 'no transaction history')


    def test_activity_tot_volume_tot_count(self):
        pass

    def test_activity_consistency(self):
        pass

    def test_activity_profit_since_inception(self):
        pass

    def test_helper_fn(self):
        '''
        - Ensure the output of flow() comprises of both positive and negative volumes
        '''
        pass



# -------------------------------------------------------------------------- #
#                            PARAMETRIZATION                                 #
# -------------------------------------------------------------------------- # 

class TestParametrizeOutput(unittest.TestCase):
    '''
    The TestParametrizeOutput object checks that ALL functions 
    of our Coinbase algorithm ALWAYS return a tuple comprising of:
    - an int (i.e., the score)
    - a dict (i.e., the feedback)
    It also checks that the score is ALWAYS in the range [0, 1]
    Finally, it checks that even when all args are NoneTypes, th output is still a tuple
    '''

    def test_output(self):
        pass
 

if __name__ == '__main__':
    unittest.main()
