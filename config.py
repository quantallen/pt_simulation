class Pair_Trading_Config:
    # Target symbol is where the LIMIT orders are placed based on calculated spreads.
    # TARGET_SYMBOL = "ETH-USD"
    def __init__(
        self, Ref, Target, open_thershold, stop_loss_threshold, test_second
    ) -> None:

        # Reference symbol is where the MARKET orders are intiated AFTER target symbol's limit orders are filled.
        # REFERENCE_SYMBOL = "BTC-USD"
        self.TARGET_SYMBOL = Target

        # Reference symbol is where the MARKET orders are intiated AFTER target symbol's limit orders are filled.
        self.REFERENCE_SYMBOL = Ref

        # OPEN_POSITION_SPREAD is the target z-score of the spread that we use to open position.
        # (i.e., 2.0 means will open position at 2 std away from the mean)
        self.OPEN_THRESHOLD = float(open_thershold)
        # CLOSE_POSITION_SPREAD is the the target z-score of the spread that we use to close position
        # (i.e., 0.5 means will open position at 0.5 std away from the mean)
        self.STOP_LOSS_THRESHOLD = float(stop_loss_threshold)
        # Window size for calculating spread mean.
        self.MA_WINDOW_SIZE = 120
        self.RETRY_TIME = 1
        self.SLIPPAGE = 0.000
        self.TEST_SECOND = float(test_second)
