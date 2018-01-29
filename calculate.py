from QuantLib import *
import pandas as pd
from loans import Loan, Loans
from fees import Fees
from inputs import StructuralInputs

#Construct a yield curve
calc_date = Date(1,2,2007)
Settings.instance().evaluationDate=calc_date
spot_dates = [Date(1,2,2007), Date(1,3,2017), Date(1,3,2040)]
spot_rates = [0.09, .09, .09]
day_count = Actual360()
calendar = UnitedStates()
interpolation = Linear()
compounding = Compounded
compounding_frequency = Annual
spot_curve = ZeroCurve(spot_dates, spot_rates, day_count, calendar, interpolation, compounding,
                       compounding_frequency)
spot_curve_handle = YieldTermStructureHandle(spot_curve)
#print(spot_curve_handle.discount(Date(1,3,2017)))
bond_engine = DiscountingBondEngine(spot_curve_handle)


sample_rates_and_prepay = pd.read_excel('Sample_Vectors.xlsx', sheet_name='RatesAndPrepay', index_col=0)
sample_loss_timing = pd.read_excel('Sample_Vectors.xlsx', sheet_name='LossTiming', index_col=0)
#print(sample_rates_and_prepay)
#print(sample_loss_timing)
structural_inputs = StructuralInputs(.02, .01, False, 3, .05, True)
#print(structural_inputs)

#Create an asset
issue_date = Date(1,2,2007)
stub_date = Date(1,3,2007)
maturity_date = Date(1,2,2037)
rate_type = 'FloatingRateBond'
#rate_type = 'FixedRateBond'
amortizing_type = 'FloatingAmortizingBond'
tenor = Period(Monthly)
calendar = UnitedStates()
business_convention = Following
termination_business_convention = Following
date_generation = DateGeneration.Forward
end_of_month = False
settlement_days = 0
day_count = Actual360()
rate = sample_rates_and_prepay['1-Month Libor']
#rate = .09
default_rate = .00003*12

loan1 = Loan(rate_type, amortizing_type, 100000000.00, 100000000.00, issue_date, maturity_date, stub_date, tenor,
             calendar, business_convention, termination_business_convention, date_generation, end_of_month,
             settlement_days, day_count, rate, sample_rates_and_prepay['SMM 1'], 1, .01, 1,
             sample_loss_timing['Loss Timing 1'], None, .4, Period(5, Months))

#fee = Fees(loan1.beginning_principal_balance, .05)

print(loan1.get_npv(bond_engine))
#loan1.show_cashflow()
#print(loan1.instrument.cashflows())
#print(loan1.get_original_term())
#print(loan1.get_remaining_term(issue_date))
loans = Loans('port1', [loan1])
loans.show_cashflow()

