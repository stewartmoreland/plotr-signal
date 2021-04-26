#! /usr/bin/env python
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql.schema import ForeignKey
from plotr_signal.database import Base

from sqlalchemy.orm import relationship


class Symbols(Base):
    __tablename__ = 'symbols'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(8), unique=True)
    name = Column(String(64), unique=False)
    sector = Column(String(32), unique=False)
    price = relationship("Price")

    def __init__(self, ticker=None, name=None, sector=None):
        self.ticker = ticker
        self.name = name
        self.sector = sector

    def __repr__(self):
        return self

class Price(Base):
    __tablename__ = 'price'

    id = Column(Integer, primary_key=True)
    ticker = Column(String(8), ForeignKey(Symbols.ticker), unique=False)
    datetime = Column(DateTime, unique=False)
    price = Column(Float, unique=False)

    def __init__(self, ticker=None, datetime=None, price=None):
        self.ticker = ticker
        self.datetime = datetime
        self.price = price

    def __repr__(self):
        return self
