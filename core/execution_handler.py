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
        except Exception as e:
            log.error("Failed to square off all positions", error=str(e))
]]>
