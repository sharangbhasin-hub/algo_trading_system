<!
        self.trade_taken = False
        self.entry_price = None
        self.stop_loss = None
        self.target = None

    def run(self, underlying_ltp, current_time):
        """Main logic loop for the strategy."""
        if not self.active:
            return
            
        # Define the opening range
        if current_time >= self.orb_start_time and self.range_high is None:
            # In a real implementation, you'd fetch historical data for this window
            # For this example, we'll simulate it.
            # This part needs to be connected to actual 1-min historical data.
            log.warning("ORB historical data fetch is not implemented. Using placeholder values.")
            self.range_high = underlying_ltp * 1.005
            self.range_low = underlying_ltp * 0.995
            log.info("ORB range defined", high=self.range_high, low=self.range_low)

        # Check for breakout after the range is set
        if self.range_high is not None and not self.trade_taken and current_time > self.orb_end_time:
            if underlying_ltp > self.range_high:
                log.info("ORB Bullish Breakout detected", ltp=underlying_ltp, range_high=self.range_high)
                self.execute_trade('BUY', underlying_ltp)
            elif underlying_ltp < self.range_low:
                log.info("ORB Bearish Breakout detected", ltp=underlying_ltp, range_low=self.range_low)
                self.execute_trade('SELL', underlying_ltp)

    def execute_trade(self, side, underlying_ltp):
        """Selects an option and places the trade."""
        self.trade_taken = True
        
        # 1. Select Strike Price (ATM)
        atm_strike = get_atm_strike(underlying_ltp, self.strike_interval)
        
        # 2. Find the correct option instrument
        option_type = 'CE' if side == 'BUY' else 'PE'
        expiry = get_nearest_expiry(self.data_handler.instrument_df, self.underlying)
        
        target_option = self.data_handler.get_instrument(self.underlying, expiry, atm_strike, option_type)
        
        if target_option is None:
            log.error("Could not find option instrument for ORB trade.", strike=atm_strike, type=option_type)
            return

        # 3. Define Risk and Targets
        # For simplicity, using a fixed percentage stop-loss on the premium
        option_ltp = self.portfolio_manager.get_ltp(target_option['tradingsymbol']) # Requires ltp tracking
        if not option_ltp:
            log.error("Could not get LTP for target option to calculate SL/Target.")
            # Fallback or fetch quote
            return

        self.entry_price = option_ltp
        self.stop_loss = self.entry_price * (1 - self.sl_pct / 100)
        self.target = self.entry_price * (1 + self.target_pct / 100)

        # 4. Calculate Position Size
        quantity = self.risk_manager.calculate_position_size(self.entry_price, self.stop_loss)
        
        if quantity == 0:
            log.warning("Position size is zero. Skipping trade.")
            return

        # 5. Place Order
        log.info("Placing ORB order", symbol=target_option['tradingsymbol'], qty=quantity, side=side)
        self.execution_handler.place_order(
            tradingsymbol=target_option['tradingsymbol'],
            exchange='NFO',
            transaction_type=self.execution_handler.kite.TRANSACTION_TYPE_BUY,
            quantity=quantity,
            order_type=self.execution_handler.kite.ORDER_TYPE_MARKET,
            product=self.execution_handler.kite.PRODUCT_MIS
        )
        st.toast(f"ORB {side} Signal on {target_option['tradingsymbol']}!")

class ShortStraddleStrategy(BaseStrategy):
    """9:20 AM Short Straddle Strategy"""
    def __init__(self, underlying, data_handler, execution_handler, portfolio_manager, risk_manager, entry_time_str="09:20", exit_time_str="15:15", sl_pct=25.0):
        super().__init__("9:20 Short Straddle", underlying, data_handler, execution_handler, portfolio_manager, risk_manager)
        self.entry_time = datetime.strptime(entry_time_str, "%H:%M").time()
        self.exit_time = datetime.strptime(exit_time_str, "%H:%M").time()
        self.sl_pct = sl_pct
        self.trade_taken = False
        self.positions = {} # Tracks legs: {'CE': {...}, 'PE': {...}}
        self.total_premium_collected = 0

    def run(self, underlying_ltp, current_time):
        if not self.active:
            return

        # Entry logic
        if current_time >= self.entry_time and not self.trade_taken:
            self.execute_straddle(underlying_ltp)
            self.trade_taken = True

        # Stop-loss logic
        if self.trade_taken:
            self.check_stop_loss()
            
        # EOD Exit logic
        if self.trade_taken and current_time >= self.exit_time:
            log.info("End of day exit for Short Straddle")
            self.execution_handler.square_off_all_positions() # Simplified
            self.reset_strategy()
            st.toast("Short Straddle EOD Exit!")

    def execute_straddle(self, ltp):
        log.info(f"Executing Short Straddle for {self.underlying} at LTP {ltp}")
        
        atm_strike = get_atm_strike(ltp, self.strike_interval)
        expiry = get_nearest_expiry(self.data_handler.instrument_df, self.underlying)
        
        ce_option = self.data_handler.get_instrument(self.underlying, expiry, atm_strike, 'CE')
        pe_option = self.data_handler.get_instrument(self.underlying, expiry, atm_strike, 'PE')

        if not ce_option or not pe_option:
            log.error("Could not find CE/PE instruments for straddle.")
            return

        # Simplified position sizing - 1 lot
        quantity = 15 # Example for BANKNIFTY

        # Sell Call
        self.execution_handler.place_order(
            tradingsymbol=ce_option['tradingsymbol'],
            exchange='NFO',
            transaction_type=self.execution_handler.kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            order_type=self.execution_handler.kite.ORDER_TYPE_MARKET,
            product=self.execution_handler.kite.PRODUCT_MIS
        )
        # Sell Put
        self.execution_handler.place_order(
            tradingsymbol=pe_option['tradingsymbol'],
            exchange='NFO',
            transaction_type=self.execution_handler.kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            order_type=self.execution_handler.kite.ORDER_TYPE_MARKET,
            product=self.execution_handler.kite.PRODUCT_MIS
        )
        
        # Placeholder for fetching entry price and premium
        # In a real system, you'd get this from order execution confirmation
        ce_ltp = self.portfolio_manager.get_ltp(ce_option['tradingsymbol']) or 100
        pe_ltp = self.portfolio_manager.get_ltp(pe_option['tradingsymbol']) or 100
        self.total_premium_collected = ce_ltp + pe_ltp
        self.positions['CE'] = {'symbol': ce_option['tradingsymbol'], 'entry_price': ce_ltp}
        self.positions['PE'] = {'symbol': pe_option['tradingsymbol'], 'entry_price': pe_ltp}

        st.toast(f"Short Straddle executed at strike {atm_strike}!")

    def check_stop_loss(self):
        """Check if the combined premium has exceeded the stop-loss percentage."""
        if not self.positions:
            return
            
        ce_ltp = self.portfolio_manager.get_ltp(self.positions['CE']['symbol'])
        pe_ltp = self.portfolio_manager.get_ltp(self.positions['PE']['symbol'])

        if ce_ltp is None or pe_ltp is None:
            return # Not all data is available yet

        current_premium = ce_ltp + pe_ltp
        stop_loss_premium = self.total_premium_collected * (1 + self.sl_pct / 100)

        if current_premium >= stop_loss_premium:
            log.warning("Short Straddle STOP LOSS hit!", current_premium=current_premium, sl_premium=stop_loss_premium)
            self.execution_handler.square_off_all_positions() # Simplified
            self.reset_strategy()
            st.error("Short Straddle Stop-Loss Triggered!")

    def reset_strategy(self):
        self.trade_taken = False
        self.positions = {}
        self.total_premium_collected = 0

class OIChangeStrategy(BaseStrategy):
    """Trades based on significant intraday changes in Open Interest."""
    def __init__(self, underlying, data_handler, execution_handler, portfolio_manager, risk_manager, oi_change_threshold=100000):
        super().__init__("OI Change Strategy", underlying, data_handler, execution_handler, portfolio_manager, risk_manager)
        self.oi_change_threshold = oi_change_threshold
        self.last_oi_snapshot = {} # {strike: {'CE_oi': val, 'PE_oi': val}}

    def run(self, underlying_ltp, current_time):
        if not self.active:
            return

        # Get current option chain data
        expiry = get_nearest_expiry(self.data_handler.instrument_df, self.underlying)
        option_chain_df = st.session_state.option_chain_df
        
        if option_chain_df.empty:
            return

        # Initialize snapshot
        if not self.last_oi_snapshot:
            for _, row in option_chain_df.iterrows():
                strike = row['strike']
                if strike not in self.last_oi_snapshot:
                    self.last_oi_snapshot[strike] = {'CE_oi': 0, 'PE_oi': 0}
                
                oi_key = f"{row['instrument_type']}_oi"
                self.last_oi_snapshot[strike][oi_key] = row['oi']
            return

        # Analyze OI changes
        for _, row in option_chain_df.iterrows():
            strike = row['strike']
            oi_type = row['instrument_type']
            current_oi = row['oi']
            
            if strike in self.last_oi_snapshot:
                last_oi = self.last_oi_snapshot[strike][f"{oi_type}_oi"]
                oi_change = current_oi - last_oi

                # Signal logic: Significant OI buildup on one side
                if oi_change > self.oi_change_threshold:
                    log.info("Significant OI Change Detected", strike=strike, type=oi_type, change=oi_change)
                    # Example: If significant Call OI builds up, it's resistance -> Bearish signal
                    if oi_type == 'CE':
                        st.toast(f"OI Alert: High Call writing at {strike}. Potential Resistance.")
                    # Example: If significant Put OI builds up, it's support -> Bullish signal
                    elif oi_type == 'PE':
                        st.toast(f"OI Alert: High Put writing at {strike}. Potential Support.")
                
                # Update snapshot
                self.last_oi_snapshot[strike][f"{oi_type}_oi"] = current_oi
]]>
