<!
        self.portfolio_manager = portfolio_manager
        self.execution_handler = execution_handler
        self.max_risk_per_trade = max_risk_per_trade # e.g., 0.01 for 1%
        self.total_capital = total_capital
        self.global_stop_loss_pct = global_stop_loss_pct # e.g., 0.10 for 10% of capital
        self.eod_square_off_time = datetime.strptime(eod_square_off_time_str, "%H:%M").time()

    def calculate_position_size(self, entry_price, stop_loss_price):
        """Calculates position size based on fixed fractional risk."""
        if entry_price <= stop_loss_price:
            log.warning("Entry price must be greater than stop loss for position sizing.")
            return 0

        risk_per_contract = entry_price - stop_loss_price
        risk_amount = self.total_capital * self.max_risk_per_trade
        
        if risk_per_contract == 0:
            return 0
            
        num_contracts = floor(risk_amount / risk_per_contract)
        
        # Assuming a minimum lot size of 1 for simplicity
        # In reality, this should be fetched from instrument data
        lot_size = 15 # Example for BANKNIFTY
        
        num_lots = floor(num_contracts / lot_size)
        
        return max(1, num_lots) * lot_size # Return quantity in terms of shares/units

    def check_global_stop_loss(self):
        """Checks if the total portfolio P&L has breached the global stop loss."""
        current_pnl = self.portfolio_manager.get_pnl()
        if current_pnl < 0 and abs(current_pnl) >= (self.total_capital * self.global_stop_loss_pct):
            log.critical("GLOBAL STOP LOSS BREACHED. Squaring off all positions.")
            st.error("GLOBAL STOP LOSS BREACHED! Squaring off all positions.")
            self.execution_handler.square_off_all_positions()
            # You might want to add logic to halt all further trading for the day
            return True
        return False

    def run_end_of_day_check(self):
        """Checks if it's time to square off all positions for end of day."""
        now = datetime.now(timezone("Asia/Kolkata")).time()
        if now >= self.eod_square_off_time:
            log.info("End of day square off triggered.")
            st.warning("End of Day: Squaring off all open positions.")
            self.execution_handler.square_off_all_positions()
            return True
        return False
]]>
