import textwrap

class StructuralInputs:
    def __init__(self, asset_based_fees, reserve_account_pct, capture_all_xs_spread, post_default_trigger_month,
                 default_trigger_pct, swap_active):
        self.asset_based_fees = asset_based_fees
        self.reserve_account_pct = reserve_account_pct
        self.capture_all_xs_spread = capture_all_xs_spread
        self.post_default_trigger_month = post_default_trigger_month
        self.default_trigger_pct = default_trigger_pct
        self.swap_active = swap_active

    def __str__(self):
        return textwrap.dedent('''
        asset_based fees: {}, reserve account percentage: {}, capture all excess spread: {},
        post default trigger month: {}, default trigger percentage: {}, swap active: {}'''
        .format(self.asset_based_fees, self.reserve_account_pct, self.capture_all_xs_spread,
                self.post_default_trigger_month, self.default_trigger_pct, self.swap_active))