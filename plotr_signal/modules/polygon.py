from polygon import RESTClient
import json

class Polygon(object):
    def __init__(self, api_key):
        self.client = RESTClient(api_key)

    def get_historical_data(self, ticker, from_, to, 
                            multiplier='1', interval='minute', unadjusted=False):
        data = self.client.stocks_equities_aggregates(ticker,multiplier,interval,from_,to,unadjusted=unadjusted)

        return data

    def get_equity_info(self, ticker):
        data = self.client.reference_ticker_details(symbol=ticker)
        
        return data

