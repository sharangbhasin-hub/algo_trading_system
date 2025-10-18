<!
    with st.spinner("Generating session..."):
        access_token = kite_client.generate_session(request_token)
        if access_token:
            st.session_state.access_token = access_token
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Failed to generate session. Please try logging in again.")

if st.session_state.access_token:
    st.sidebar.success("Logged in successfully!")
    profile = kite_client.get_profile()
    if profile:
        st.sidebar.write(f"Welcome, {profile['user_name']}!")
else:
    st.sidebar.warning("You are not logged in.")
    login_url = kite_client.get_login_url()
    st.sidebar.link_button("Login with Kite", login_url)
    st.info("Please log in to start the application.")
    st.stop()

# --- 4. Initialize Core Components ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if not st.session_state.initialized:
    with st.spinner("Initializing Core Components..."):
        st.session_state.data_handler = DataHandler(kite_client)
        st.session_state.data_handler.initialize()
        
        st.session_state.portfolio_manager = PortfolioManager(initial_capital=100000)
        st.session_state.execution_handler = ExecutionHandler(kite_client, st.session_state.portfolio_manager)
        st.session_state.risk_manager = RiskManager(
            portfolio_manager=st.session_state.portfolio_manager,
            execution_handler=st.session_state.execution_handler
        )
        
        # Initialize Strategies
        st.session_state.strategies = {
            "orb": OpeningRangeBreakoutStrategy("NIFTY BANK", st.session_state.data_handler, st.session_state.execution_handler, st.session_state.portfolio_manager, st.session_state.risk_manager),
            "straddle": ShortStraddleStrategy("NIFTY BANK", st.session_state.data_handler, st.session_state.execution_handler, st.session_state.portfolio_manager, st.session_state.risk_manager),
            "oi_change": OIChangeStrategy("NIFTY BANK", st.session_state.data_handler, st.session_state.execution_handler, st.session_state.portfolio_manager, st.session_state.risk_manager)
        }
        st.session_state.initialized = True
    st.success("Core components initialized.")

# --- 5. Main Application UI ---
st.title("📈 Intraday Options Trading Dashboard")

# Strategy Control Panel
st.sidebar.header("Strategy Control")
for name, strategy in st.session_state.strategies.items():
    strategy.active = st.sidebar.toggle(f"Activate {strategy.name}", value=False, key=f"strat_{name}")

# --- 6. Real-time Data and Option Chain Display ---
data_handler = st.session_state.data_handler
portfolio_manager = st.session_state.portfolio_manager
risk_manager = st.session_state.risk_manager

selected_instrument = "NIFTY BANK" # Hardcoded for this version
expiry_date = get_nearest_expiry(data_handler.instrument_df, selected_instrument)

st.header(f"Live Data for {selected_instrument}")
st.info(f"Displaying data for nearest expiry: **{expiry_date.strftime('%d-%b-%Y')}**")

# Subscribe to underlying index token
# This needs to be looked up from the instruments file
# Example token for NIFTY BANK index
index_token = 260105 
data_handler.subscribe_to_tokens([index_token])

# Get the option chain for the selected expiry and subscribe
option_chain = data_handler.get_option_chain(selected_instrument, expiry_date)
if not option_chain.empty:
    tokens_to_subscribe = option_chain['instrument_token'].tolist()
    if 'websocket_started' not in st.session_state:
        data_handler.start_websocket()
        st.session_state['websocket_started'] = True
    data_handler.subscribe_to_tokens(tokens_to_subscribe)

# --- UI Placeholders ---
top_placeholder = st.empty()
chain_placeholder = st.empty()

# Initialize option chain DataFrame in session state
if st.session_state.option_chain_df.empty:
    df = option_chain[['instrument_token', 'tradingsymbol', 'strike', 'instrument_type']].copy()
    df['ltp'] = 0.0
    df['oi'] = 0
    df['volume'] = 0
    st.session_state.option_chain_df = df.set_index('instrument_token')

# --- Real-time Update Loop ---
st_autorefresh(interval=2000, limit=None, key="main_loop")

try:
    ticks = data_handler.tick_queue.get_nowait()
    
    # Update the main DataFrame with new tick data
    underlying_ltp = None
    for tick in ticks:
        token = tick['instrument_token']
        if token == index_token:
            underlying_ltp = tick['last_price']
            st.session_state.underlying_ltp = underlying_ltp

        if token in st.session_state.option_chain_df.index:
            st.session_state.option_chain_df.loc[token, 'ltp'] = tick['last_price']
            st.session_state.option_chain_df.loc[token, 'oi'] = tick['oi']
            st.session_state.option_chain_df.loc[token, 'volume'] = tick['volume_traded']
    
    # Update P&L
    portfolio_manager.update_pnl(ticks)

except queue.Empty:
    pass # No new ticks
except Exception as e:
    log.error("Error in main loop", error=str(e))

# Run strategy logic if underlying LTP is available
if st.session_state.underlying_ltp:
    current_time = datetime.now(timezone("Asia/Kolkata")).time()
    for strategy in st.session_state.strategies.values():
        strategy.run(st.session_state.underlying_ltp, current_time)

# Run risk checks
risk_manager.check_global_stop_loss()
risk_manager.run_end_of_day_check()

# Display Data
with top_placeholder.container():
    col1, col2, col3 = st.columns(3)
    col1.metric("Underlying LTP", f"₹{st.session_state.underlying_ltp:,.2f}" if st.session_state.underlying_ltp else "N/A")
    col2.metric("Total P&L", f"₹{portfolio_manager.get_pnl():,.2f}")
    col3.metric("Open Positions", len(portfolio_manager.get_positions()))
    
    st.subheader("Current Positions")
    positions_df = pd.DataFrame.from_dict(portfolio_manager.get_positions(), orient='index')
    if not positions_df.empty:
        st.dataframe(positions_df)
    else:
        st.write("No open positions.")

with chain_placeholder.container():
    st.subheader("Live Option Chain")
    calls = st.session_state.option_chain_df[st.session_state.option_chain_df['instrument_type'] == 'CE']
    puts = st.session_state.option_chain_df[st.session_state.option_chain_df['instrument_type'] == 'PE']
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(calls[['tradingsymbol', 'strike', 'ltp', 'oi', 'volume']].sort_values('strike'))
    with col2:
        st.dataframe(puts[['tradingsymbol', 'strike', 'ltp', 'oi', 'volume']].sort_values('strike', ascending=False))
]]>
