from QuantLib import *
import numpy as np
import pandas as pd
import collections

class Loan:
    def __init__(self, rate_type, amortizing_type, original_principal_balance, principal_balance, issue_date,
                 maturity_date, stub_date, tenor, calendar, business_convention, termination_business_convention,
                 date_generation, month_end, settlement_days, day_count, rate, prepay_curve, prepay_stress,
                 gross_cumulative_loss, loss_stress, loss_timing_curve, sda_curve, recovery_rate, recovery_lag):
        self.rate_type = rate_type
        self.amortizing_type = amortizing_type
        self.original_principal_balance = original_principal_balance
        self.current_principal_balance = principal_balance
        self.issue_date = issue_date
        self.maturity_date = maturity_date
        self.stub_date = stub_date
        self.tenor = tenor
        self.calendar = calendar
        self.business_convention = business_convention
        self.termination_business_convention = termination_business_convention
        self.date_generation = date_generation
        self.end_of_month = month_end
        self.schedule = Schedule(self.issue_date, self.maturity_date, self.tenor, self.calendar,
                                 self.business_convention, self.termination_business_convention, self.date_generation,
                                 self.end_of_month, self.stub_date)
        self.settlement_days = settlement_days
        self.day_count = day_count
        self.rate = rate
        self.prepay_curve = prepay_curve
        self.prepay_stress = prepay_stress
        self.gross_cumulative_loss = gross_cumulative_loss
        self.loss_stress = loss_stress
        self.loss_timing_curve = loss_timing_curve
        self.sda_curve = sda_curve
        self.recovery_rate = recovery_rate
        self.recovery_lag = recovery_lag
        self.notional_cashflow_interest = []
        self.notional_cashflow_principal_amortization = []
        self.notional_cashflow = []
        self.cashflow_interest = []
        self.cashflow_principal_amortization = []
        self.cashflow_defaults = []
        self.cashflow_prepayments = []
        self.cashflow_principal_recovery = []
        self.cashflow = []
        self.ending_notional_principal_balance = []
        self.beginning_notional_principal_balance = []
        self.ending_principal_balance = []
        self.beginning_principal_balance = []
        self.beginning_notional_principal_balance.append(0)
        self.beginning_principal_balance.append(0)
        self.ending_notional_principal_balance.append(self.current_principal_balance)
        self.ending_principal_balance.append(self.current_principal_balance)
        self.cashflow_available_to_pay_liabilities = []

        my_per = int(self.get_original_term() * self.tenor.frequency())
        for i, date in enumerate(list(self.schedule)):
            if date != self.issue_date:

                if self.rate_type == 'FixedRateBond':
                    my_rate = float(self.rate)/self.tenor.frequency()
                elif self.rate_type == 'FloatingRateBond':
                    my_rate = float(self.rate[i])/self.tenor.frequency()

                # start with notional amortization schedule
                self.beginning_notional_principal_balance.append(self.ending_notional_principal_balance[-1])

                if self.amortizing_type == 'FixedAmortizingBond':
                    my_prin = -np.asscalar(np.ppmt(my_rate, i, my_per, self.original_principal_balance))
                    my_int = -np.asscalar(np.ipmt(my_rate, i, my_per, self.original_principal_balance))
                elif self.amortizing_type == 'FloatingAmortizingBond':
                    pmt = -np.asscalar(np.pmt(my_rate, my_per, self.original_principal_balance))
                    my_int = self.beginning_notional_principal_balance[-1]*my_rate
                    my_prin = pmt -my_int
                elif self.amortizing_type is None:
                    my_prin = 0

                self.notional_cashflow_principal_amortization.append(SimpleCashFlow(my_prin, date))
                self.notional_cashflow_interest.append(SimpleCashFlow(my_int, date))
                self.notional_cashflow = self.notional_cashflow_principal_amortization + \
                                         self.notional_cashflow_interest
                self.ending_notional_principal_balance.append(self.beginning_notional_principal_balance[-1]-my_prin)

                # next is the actual amortization schedule
                self.beginning_principal_balance.append(self.ending_principal_balance[-1])
                my_index = int((i-1)/self.tenor.frequency())*self.tenor.frequency()+1
                my_default_rate = self.loss_timing_curve[my_index]*self.gross_cumulative_loss\
                                  *self.loss_stress/self.tenor.frequency()
                my_default = self.beginning_principal_balance[1]*my_default_rate
                self.cashflow_defaults.append(SimpleCashFlow(my_default, date))
                my_prepay_rate = self.prepay_curve[i]
                my_amort_factor = self.ending_notional_principal_balance[-1]/\
                                  self.ending_notional_principal_balance[-2]
                my_prepay = max(min(self.beginning_principal_balance[-1]-my_default,
                                    self.beginning_principal_balance[-1]*my_amort_factor*my_prepay_rate),0)
                self.cashflow_prepayments.append(SimpleCashFlow(my_prepay, date))

                if self.amortizing_type == 'FixedAmortizingBond' or self.amortizing_type == 'FloatingAmortizingBond':
                    my_prin = (self.beginning_principal_balance[-1]-my_default)*(1-my_amort_factor)
                elif self.amortizing_type is None:
                    my_prin = 0

                self.cashflow_principal_amortization.append(SimpleCashFlow(my_prin, date))
                my_int = my_rate*(self.beginning_principal_balance[-1]-my_default)
                self.cashflow_interest.append(SimpleCashFlow(my_int, date))
                my_recovery = 0
                my_recovery_start_date = self.calendar.advance(list(self.schedule)[0],self.recovery_lag)

                if date > my_recovery_start_date:
                    my_recovery = self.recovery_rate*self.cashflow_defaults[-self.recovery_lag.length()].amount()

                self.cashflow_principal_recovery.append(SimpleCashFlow(my_recovery, date))
                self.cashflow = self.cashflow_defaults + self.cashflow_prepayments + \
                                self.cashflow_principal_amortization + self.cashflow_interest + \
                                self.cashflow_principal_recovery
                self.cashflow_available_to_pay_liabilities = self.cashflow_prepayments+\
                                                             self.cashflow_principal_amortization+\
                                                             self.cashflow_interest+\
                                                             self.cashflow_principal_recovery
                self.ending_principal_balance.append(self.ending_principal_balance[-1]-my_default-
                                                     my_prepay-my_prin)

        self.instrument = Bond(self.settlement_days, self.calendar, self.original_principal_balance,
                               self.maturity_date, self.issue_date, self.notional_cashflow)
        self.cashflow_dictionary = collections.OrderedDict([
            ("date",
             list(self.schedule)),
            ("beginning notional balance",
             self.beginning_notional_principal_balance),
            ("notional interest",
             self.translate_cashflow_to_list(self.notional_cashflow_interest)),
            ("notional principal amortization",
             self.translate_cashflow_to_list(self.notional_cashflow_principal_amortization)),
            ("ending notional balance",
             self.ending_notional_principal_balance),
            ("beginning balance",
             self.beginning_principal_balance),
            ("defaults",
             self.translate_cashflow_to_list(self.cashflow_defaults)),
            ("prepayments",
             self.translate_cashflow_to_list(self.cashflow_prepayments)),
            ("principal amortization",
             self.translate_cashflow_to_list(self.cashflow_principal_amortization)),
            ("interest",
             self.translate_cashflow_to_list(self.cashflow_interest)),
            ("principal recovery",
             self.translate_cashflow_to_list(self.cashflow_principal_recovery)),
            ("ending balance",
             self.ending_principal_balance),
            ("cash available to pay liabilities",
             self.translate_cashflow_to_list(self.cash_flow_available_to_pay_liabilities()))
        ])

    def __str__(self):
        return 'type: ' + type(self.instrument).__name__ + ' principal balance: {}, rate: {},  term: {}, schedule: {}' \
            .format(self.principal_balance, self.rate, self.get_schedule_dates(), list(self.schedule))

    def get_schedule_dates(self):
        return [d for i, d in enumerate(self.schedule)]

    def get_original_term(self):
        return (ActualActual().yearFraction(self.issue_date, self.maturity_date))

    def get_remaining_term(self, effective_date):
        return (ActualActual().yearFraction(effective_date, self.maturity_date))

    def get_npv(self, be):
        self.instrument.setPricingEngine(be)
        return self.instrument.NPV()

    def cash_flow_available_to_pay_liabilities(self):
        cf = self.cashflow_principal_recovery+self.cashflow_principal_amortization+self.cashflow_interest+\
             self.cashflow_prepayments
        return self.accumulate(cf)

    def accumulate(self, cfs):
        result = []
        for dt in list(self.schedule)[1:]:
            sub_cfs = [cf.amount() for i, cf in enumerate(cfs) if cfs[i].date() == dt]
            result.append(SimpleCashFlow(sum(sub_cfs), dt))
        return result

    # def get_ending_principal(self):
    #     bal = [self.original_principal_balance]
    #     cf_sum = 0
    #     for i, d in enumerate(list(self.schedule)[1:]):
    #         cf_sum = cf_sum + self.cashflow_defaults[i].amount()+ self.cashflow_prepayments[i].amount() +\
    #                  self.cashflow_principal_amortization[i].amount()
    #         bal.append(self.original_principal_balance-cf_sum)
    #     return bal
    #
    # def get_ending_notional_principal(self, dt):
    #     bal = [self.original_principal_balance]
    #     sum_cf = self.sum_cf_until_date(self.notional_cashflow_principal_amortization,dt)
    #     bal.append(self.original_principal_balance-sum_cf)
    #     return bal
    #
    # def get_beginning_principal(self):
    #     bal = [0]
    #     return bal + self.get_ending_principal()[:-1]
    #
    def sum_cf_until_date(self, cf, dt):
        i = 0
        sum_cf = 0
        sch_dates = list(self.schedule)[1:]
        while  sch_dates[i] <= dt:
            sum_cf = sum_cf + cf[i].amount()
            i += 1
        return sum_cf
    #
    # def get_beginning_notional_principal(self):
    #     bal = [0]
    #     return bal + self.get_ending_notional_principal()[:-1]

    def translate_cashflow_to_list(self, cf):
        cf_list = [0]
        [cf_list.append(c.amount()) for c in cf]
        return cf_list

    def show_cashflow(self):
        df = pd.DataFrame(self.cashflow_dictionary)
        print(df)

class Loans:
    def __init__(self, name, positions):
        self.name = name
        self.positions = positions

    def representative_loan(self):
        sum_principal_balance = 0
        weighted_avg_rate = 0
        weighted_avg_term = 0
        for pos in self.positions:
            sum_principal_balance = sum_principal_balance + pos.principal_balance
            weighted_avg_rate = weighted_avg_rate + pos.rate * pos.principal_balance
            weighted_avg_term = weighted_avg_term + pos.get_original_term() * pos.principal_balance
        weighted_avg_rate = weighted_avg_rate / sum_principal_balance
        weighted_avg_term = weighted_avg_term / sum_principal_balance
        return Loan(sum_principal_balance, weighted_avg_rate, weighted_avg_term)
