#! /usr/bin/env python
from enum import unique
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.engine import base
from sqlalchemy.sql.schema import ForeignKey, Index
from sqlalchemy.sql.sqltypes import Boolean
from plotr_signal.database import Base

from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(64), unique=True)
    first_name = Column(String(64), unique=False)
    last_name = Column(String(64), unique=False)
    email = Column(String(128), unique=True)
    base_currency = Column(String(6), unique=False)

    def __init__(self, user_name=None, first_name=None, last_name=None, email=None, base_currency=None):
        self.user_name = user_name
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.base_currency = base_currency

    def __repr__(self):
        return self


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


class CryptoCurrencies(Base):
    __tablename__ = 'crypto-currencies'

    id = Column(Integer, primary_key=True)
    currency = Column(String(12), unique=True)
    name = Column(String(64), unique=True)
    min_size = Column(Float, unique=False)

    def __init__(self, currency=None, name=None, min_size=None):
        self.currency = currency
        self.name = name
        self.min_size = min_size

    def __repr__(self):
        return self


class CryptoProducts(Base):
    __tablename__ = 'crypto-products'

    id = Column(Integer, primary_key=True)
    product = Column(String(12), unique=True)
    name = Column(String(64), unique=True)
    base_currency = Column(String(8), unique=False)
    quote_currency = Column(String(8), unique=False)
    base_min_size = Column(Float, unique=False)
    base_max_size = Column(Float, unique=False)
    supervised = Column(Boolean, unique=False, default=False)
    stablecoin = Column(Boolean, unique=False, default=False)

    def __init__(self, product=None, name=None, base_currency=None, quote_currency=None, base_min_size=None, base_max_size=None, supervised=None, stablecoin=None):
        self.product = product
        self.name = name
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_min_size = base_min_size
        self.base_max_size = base_max_size
        self.supervised = supervised
        self.stablecoin = stablecoin

    def __repr__(self):
        return self
