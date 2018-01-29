from loans import Loan

class Fees:
    def __init__(self, base, fee_pct_instrument):
        self.base = base
        self.fee_pct_instrument = fee_pct_instrument
        self.fee = self.base*self.fee_pct_instrument


