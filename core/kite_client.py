<!["api_key"]
        self.api_secret = st.secrets["kite_credentials"]["api_secret"]
        self.kite = KiteConnect(api_key=self.api_key)
        self.ticker = None

    def set_access_token(self, access_token):
        """Set the access token for the KiteConnect instance."""
        try:
            self.kite.set_access_token(access_token)
            log.info("Kite Connect session initialized successfully.")
        except Exception as e:
            log.error("Failed to set access token", error=str(e))
            raise

    def get_login_url(self):
        """Get the login URL for Kite Connect."""
        return self.kite.login_url()

    def generate_session(self, request_token):
        """Generate a session using the request token."""
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = data["access_token"]
            self.set_access_token(access_token)
            log.info("Session generated successfully.")
            return access_token
        except Exception as e:
            log.error("Session generation failed", error=str(e))
            return None

    def get_profile(self):
        """Fetch user profile."""
        try:
            return self.kite.profile()
        except Exception as e:
            log.error("Failed to fetch profile", error=str(e))
            return None

    def initialize_ticker(self, on_ticks, on_connect, on_close):
        """Initialize and start the KiteTicker WebSocket connection."""
        if "access_token" in st.session_state and st.session_state.access_token:
            access_token = st.session_state.access_token
            self.ticker = KiteTicker(self.api_key, access_token)
            self.ticker.on_ticks = on_ticks
            self.ticker.on_connect = on_connect
            self.ticker.on_close = on_close
            log.info("KiteTicker initialized.")
        else:
            log.error("Cannot initialize KiteTicker: Access token not found.")

    def start_ticker(self):
        if self.ticker and not self.ticker.is_connected():
            log.info("Starting KiteTicker WebSocket connection...")
            self.ticker.connect(threaded=True)
        elif self.ticker and self.ticker.is_connected():
            log.info("KiteTicker is already connected.")
        else:
            log.error("KiteTicker is not initialized. Cannot start.")

    def stop_ticker(self):
        if self.ticker and self.ticker.is_connected():
            log.info("Stopping KiteTicker WebSocket connection...")
            self.ticker.stop()
        else:
            log.info("KiteTicker is not running.")

@st.cache_resource
def get_kite_client():
    """Cached function to get a singleton KiteClient instance."""
    return KiteClient()
]]>
