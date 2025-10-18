<! == underlying_name]
    
    expiries = pd.to_datetime(nfo_df['expiry'].unique()).date
    future_expiries = sorted([d for d in expiries if d >= today])
    
    if future_expiries:
        return future_expiries
    return None

def get_atm_strike(ltp, strike_interval=50):
    """Calculates the At-The-Money (ATM) strike price."""
    return round(ltp / strike_interval) * strike_interval

def calculate_greeks(flag, underlying_price, strike_price, time_to_expiry_days, interest_rate, option_price):
    """
    Calculates Implied Volatility and Greeks for an option.
    flag: 'c' for call, 'p' for put
    time_to_expiry_days: days until expiry
    interest_rate: annualized risk-free rate (e.g., 0.05 for 5%)
    """
    if option_price <= 0 or underlying_price <= 0:
        return None

    t = time_to_expiry_days / 365.0 # Convert days to years

    try:
        # 1. Calculate Implied Volatility
        iv = implied_volatility(option_price, underlying_price, strike_price, t, interest_rate, flag)
        
        if iv > 5: # IV is usually a decimal, a high value suggests an error
            iv = iv / 100

        # 2. Calculate Greeks using the calculated IV
        delta = greeks.analytical.delta(flag, underlying_price, strike_price, t, interest_rate, iv)
        gamma = greeks.analytical.gamma(flag, underlying_price, strike_price, t, interest_rate, iv)
        theta = greeks.analytical.theta(flag, underlying_price, strike_price, t, interest_rate, iv)
        vega = greeks.analytical.vega(flag, underlying_price, strike_price, t, interest_rate, iv)

        return {
            "iv": iv,
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega
        }
    except Exception as e:
        # py_vollib can sometimes fail if price is outside theoretical bounds (e.g., arbitrage)
        log.warning("Could not calculate greeks", error=str(e), option_price=option_price, underlying=underlying_price, strike=strike_price)
        return None
]]>
