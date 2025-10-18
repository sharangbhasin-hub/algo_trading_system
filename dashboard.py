<!)
    
    if st.button("Initialize Data Handler"):
        with st.spinner("Initializing Data Handler and fetching instruments..."):
            st.session_state.data_handler = DataHandler(kite_client)
            st.session_state.data_handler.initialize()
        st.success("Data Handler Initialized.")

# --- 5. Real-time Data and Option Chain Display ---
if st.session_state.data_handler:
    data_handler = st.session_state.data_handler
    
    # Get nearest expiry
    expiry_date = get_nearest_expiry(data_handler.instrument_df, selected_instrument)
    st.subheader(f"Live Option Chain for {selected_instrument}")
    st.info(f"Displaying data for nearest expiry: **{expiry_date.strftime('%d-%b-%Y')}**")

    # Get the option chain for the selected expiry
    option_chain = data_handler.get_option_chain(selected_instrument, expiry_date)
    
    if not option_chain.empty:
        # Subscribe to tokens
        tokens_to_subscribe = option_chain['instrument_token'].tolist()
        if 'websocket_started' not in st.session_state:
            data_handler.start_websocket()
            st.session_state['websocket_started'] = True
        
        data_handler.subscribe_to_tokens(tokens_to_subscribe)

        # --- UI Placeholders ---
        placeholder = st.empty()

        # Initialize option chain DataFrame in session state if not present
        if st.session_state.option_chain_df.empty:
            df = option_chain[['instrument_token', 'tradingsymbol', 'strike', 'option_type']].copy()
            df['ltp'] = 0.0
            df['oi'] = 0
            df['volume'] = 0
            st.session_state.option_chain_df = df.set_index('instrument_token')

        # --- Real-time Update Loop ---
        while True:
            try:
                ticks = data_handler.tick_queue.get(timeout=1)
                
                # Update the DataFrame with new tick data
                for tick in ticks:
                    token = tick['instrument_token']
                    if token in st.session_state.option_chain_df.index:
                        st.session_state.option_chain_df.loc[token, 'ltp'] = tick['last_price']
                        st.session_state.option_chain_df.loc[token, 'oi'] = tick['oi']
                        st.session_state.option_chain_df.loc[token, 'volume'] = tick['volume']

                # Display the updated data
                with placeholder.container():
                    calls = st.session_state.option_chain_df[st.session_state.option_chain_df['option_type'] == 'CE']
                    puts = st.session_state.option_chain_df[st.session_state.option_chain_df['option_type'] == 'PE']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Call Options")
                        st.dataframe(calls[['tradingsymbol', 'strike', 'ltp', 'oi', 'volume']].sort_values('strike'))
                    with col2:
                        st.subheader("Put Options")
                        st.dataframe(puts[['tradingsymbol', 'strike', 'ltp', 'oi', 'volume']].sort_values('strike', ascending=False))

            except queue.Empty:
                # If queue is empty, just re-display the last known data
                with placeholder.container():
                    calls = st.session_state.option_chain_df[st.session_state.option_chain_df['option_type'] == 'CE']
                    puts = st.session_state.option_chain_df[st.session_state.option_chain_df['option_type'] == 'PE']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Call Options")
                        st.dataframe(calls[['tradingsymbol', 'strike', 'ltp', 'oi', 'volume']].sort_values('strike'))
                    with col2:
                        st.subheader("Put Options")
                        st.dataframe(puts[['tradingsymbol', 'strike', 'ltp', 'oi', 'volume']].sort_values('strike', ascending=False))
                time.sleep(1) # Prevent high CPU usage
            except Exception as e:
                log.error("Error in main loop", error=str(e))
                time.sleep(1)
else:
    st.info("Please initialize the Data Handler from the sidebar to begin.")
]]>
