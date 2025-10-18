<! == underlying) &
            (self.instrument_df['expiry'] == pd.to_datetime(expiry_date))
        ]
        return chain

    def start_websocket(self):
        """Starts the WebSocket connection in a background thread."""
        kite_client = st.session_state.kite_client
        kite_client.initialize_ticker(self.on_ticks, self.on_connect, self.on_close)
        
        # Run WebSocket in a separate thread
        t = threading.Thread(target=kite_client.start_ticker)
        add_script_run_ctx(t)
        t.start()
        log.info("WebSocket thread started.")

    def subscribe_to_tokens(self, tokens):
        """Subscribes to a list of instrument tokens."""
        new_tokens = [token for token in tokens if token not in self.subscribed_tokens]
        if new_tokens and st.session_state.kite_client.ticker:
            st.session_state.kite_client.ticker.subscribe(new_tokens)
            st.session_state.kite_client.ticker.set_mode(st.session_state.kite_client.ticker.MODE_FULL, new_tokens)
            self.subscribed_tokens.update(new_tokens)
            log.info(f"Subscribed to {len(new_tokens)} new tokens.")

    # --- WebSocket Callbacks ---
    def on_ticks(self, ws, ticks):
        """Callback function to handle incoming ticks."""
        try:
            self.tick_queue.put(ticks)
        except Exception as e:
            log.error("Error in on_ticks", error=str(e))

    def on_connect(self, ws, response):
        """Callback on successful WebSocket connection."""
        log.info("WebSocket connected.")
        # Resubscribe to existing tokens if connection is re-established
        if self.subscribed_tokens:
            ws.subscribe(list(self.subscribed_tokens))
            ws.set_mode(ws.MODE_FULL, list(self.subscribed_tokens))
            log.info(f"Resubscribed to {len(self.subscribed_tokens)} tokens.")

    def on_close(self, ws, code, reason):
        """Callback on WebSocket connection close."""
        log.warning("WebSocket closed", code=code, reason=reason)
]]>
