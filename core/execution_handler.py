<!
            for pos in positions:
                if pos['quantity']!= 0:
                    log.info("Squaring off position", symbol=pos['tradingsymbol'], qty=abs(pos['quantity']))
                    self.place_order(
                        tradingsymbol=pos['tradingsymbol'],
                        exchange=pos['exchange'],
                        transaction_type=self.kite.TRANSACTION_TYPE_SELL if pos['quantity'] > 0 else self.kite.TRANSACTION_TYPE_BUY,
                        quantity=abs(pos['quantity']),
                        order_type=self.kite.ORDER_TYPE_MARKET,
                        product=pos['product']
                    )
            st.success("All positions squared off.")
        except Exception as e:
            log.error("Failed to square off all positions", error=str(e))
            st.error("Failed to square off all positions.")

    def place_stop_loss_order(self, tradingsymbol, exchange, transaction_type, quantity, trigger_price, price, product):
        """Places a Stop-Loss Limit (SL) order."""
        # Note: NSE has discontinued SL-M orders for options. We must use SL.
        try:
            order_id = self.kite.place_order(
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_SL,
                product=product,
                price=price,
                trigger_price=trigger_price
            )
            log.info("Stop-loss order placed", order_id=order_id, symbol=tradingsymbol, trigger=trigger_price, price=price)
            st.toast(f"SL Order Placed for {tradingsymbol}")
            
            # TODO: Implement "chasing" logic for the stop-loss
            # This would involve monitoring this order_id and if the market moves past the 'price'
            # without a fill, cancel and replace the order with a more aggressive price.
            # This requires tracking order updates via postbacks or the ticker.
            
            return order_id
        except Exception as e:
            log.error("Stop-loss order placement failed", error=str(e), symbol=tradingsymbol)
            st.error(f"SL order for {tradingsymbol} failed!")
            return None
]]>
