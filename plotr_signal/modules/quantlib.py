from pandas import DataFrame, Series, concat
import numpy as np

class QuantLib:

    @classmethod
    def MACD(cls, price_data:DataFrame, span_short:int=12, span_long:int=26,
             signal_span:int=9, column:str="close", adjust:bool=True,) -> DataFrame:
        """
        Moving average convergence divergence (MACD) is a trend-following momentum indicator
        that shows the relationship between two moving averages of a security’s price.
        The MACD is calculated by subtracting the 26-period exponential moving average (EMA)
        from the 12-period EMA.

        The result of that calculation is the MACD line. A nine-day EMA of the MACD called 
        the "signal line," is then plotted on top of the MACD line, which can function as a 
        trigger for buy and sell signals.
        """
        ema12 = price_data[column].ewm(span=span_short, adjust=adjust).mean()
        ema26 = price_data[column].ewm(span=span_long, adjust=adjust).mean()
        macd = Series(ema12 - ema26, name="macd")
        signal = Series(macd.ewm(span=signal_span, adjust=adjust).mean(), name="signal")
        
        return concat([macd, signal], axis=1)
    
    @classmethod
    def RSI(cls, price_data:DataFrame, time_period:int=14) -> DataFrame:
        """
        Relative strength index (RSI) is a momentum indicator used in technical analysis that
        measures the magnitude of recent price changes to evaluate overbought or oversold
        conditions in the price of a stock or other asset. The RSI is displayed as an oscillator
        (a line graph that moves between two extremes) and can have a reading from 0 to 100.
        """
        def rma(x, n, y0):
            a = (n-1) / n
            ak = a**np.arange(len(x)-1, -1, -1)
            return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a**np.arange(1, len(x)+1)]
        
        df = DataFrame()

        df['change'] = price_data['close'].diff()
        df['gain'] = df.change.mask(df.change < 0, 0.0)
        df['loss'] = -df.change.mask(df.change > 0, -0.0)
        df['avg_gain'] = rma(df.gain[time_period+1:].to_numpy(), time_period, np.nansum(df.gain.to_numpy()[:time_period+1])/time_period)
        df['avg_loss'] = rma(df.loss[time_period+1:].to_numpy(), time_period, np.nansum(df.loss.to_numpy()[:time_period+1])/time_period)
        df['rs'] = df.avg_gain / df.avg_loss
        df['rsi_period'] = 100 - (100 / (1 + df.rs))
        
        return df

    @classmethod
    def STOCH(cls, ohlc:DataFrame, period:int=14) -> Series:
        """Stochastic oscillator %K
         The stochastic oscillator is a momentum indicator comparing the closing price of a security
         to the range of its prices over a certain period of time.

         The sensitivity of the oscillator to market movements is reducible by adjusting that time
         period or by taking a moving average of the result.
        """

        highest_high = ohlc["high"].rolling(center=False, window=period).max()
        lowest_low = ohlc["low"].rolling(center=False, window=period).min()

        STOCH = Series(
            (ohlc["close"] - lowest_low) / (highest_high - lowest_low) * 100,
            name="{0} period STOCH %K".format(period),
        )

        return STOCH
