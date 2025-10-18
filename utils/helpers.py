<! == underlying_name]
    
    expiries = pd.to_datetime(nfo_df['expiry'].unique()).date
    future_expiries = sorted([d for d in expiries if d >= today])
    
    if future_expiries:
        return future_expiries
    return None

def get_atm_strike(ltp, strike_interval=50):
    """Calculates the At-The-Money (ATM) strike price."""
    return round(ltp / strike_interval) * strike_interval

# Placeholder for Greeks calculation
def calculate_greeks(option_data):
    """
    Calculates option greeks. This is a placeholder.
    A real implementation would use a library like py_vollib.
    """
    # This would require spot price, strike, time to expiry, risk-free rate, and IV.
    return {"delta": 0.5, "gamma": 0.02, "theta": -5.0, "vega": 1.5}
]]>
