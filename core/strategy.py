<!.max()
                self.range_low = orb_data['low'].min()
                log.info("ORB range defined", high=self.range_high, low=self.range_low)

        if self.range_high is not None and not self.trade_taken:
            # Check for breakout
            if current_ltp > self.range_high:
                log.info("ORB Bullish Breakout detected", ltp=current_ltp, range_high=self.range_high)
                self.execute_trade('BUY')
            elif current_ltp < self.range_low:
                log.info("ORB Bearish Breakout detected", ltp=current_ltp, range_low=self.range_low)
                self.execute_trade('SELL')

    def execute_trade(self, side):
        # Simplified trade execution logic
        log.info(f"Executing ORB {side} trade for {self.underlying}")
        # In a real scenario, you would select an appropriate option, calculate size, and place order
        # For this example, we just mark a trade as taken.
        self.trade_taken = True
        st.toast(f"ORB {side} Signal Triggered!")


class ShortStraddleStrategy(BaseStrategy):
    """9:20 AM Short Straddle Strategy"""
    def __init__(self, underlying, data_handler, execution_handler, portfolio_manager, entry_time_str="09:20", exit_time_str="15:15", sl_pct=25.0):
        super().__init__("9:20 Short Straddle", underlying, data_handler, execution_handler, portfolio_manager)
        self.entry_time = datetime.strptime(entry_time_str, "%H:%M").time()
        self.exit_time = datetime.strptime(exit_time_str, "%H:%M").time()
        self.sl_pct = sl_pct
        self.trade_taken = False
        self.positions = {} # To track legs of the straddle

    def run(self, current_ltp, current_time):
        if not self.active:
            return

        # Entry logic
        if current_time >= self.entry_time and not self.trade_taken:
            self.execute_straddle(current_ltp)
            self.trade_taken = True

        # Exit logic (simplified)
        if self.trade_taken and current_time >= self.exit_time:
            log.info("End of day exit for Short Straddle")
            # Logic to square off positions
            self.positions = {}
            self.trade_taken = False # Reset for next day
            st.toast("Short Straddle EOD Exit!")

    def execute_straddle(self, ltp):
        log.info(f"Executing Short Straddle for {self.underlying} at LTP {ltp}")
        # Find ATM strike
        # Select CE and PE options
        # Calculate position size
        # Place sell orders for both legs
        # For this example, we just log the action
        st.toast(f"Short Straddle Signal Triggered at {ltp}!")
]]>
