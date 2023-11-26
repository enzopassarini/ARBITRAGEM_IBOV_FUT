##### METATRADER #####

import MetaTrader5 as mt5
import pandas as pd

def mt5_connect(login, password, server):
    """
    Connects to MetaTrader 5 and displays basic account information.
    """

    if not mt5.initialize(login=login, password=password, server=server):
        print("initialize() failed")
        mt5.shutdown()
    else: 
        print("Conection stablished with MetaTrader5")
        print(mt5.account_info())


def OpenTicker(ticker):
    """"
    Opens ticker in MT5, making it open for data requests.
    """
    symbol_info = mt5.symbol_info(ticker)
    if not symbol_info.visible:
        mt5.symbol_select(ticker,True)


def RTData(ticker):
    """
    Requests L1 data from specified ticker. Returns it in a dictionary data-structure.
    """

    new_dict = dict()
    realtime_info = mt5.symbol_info(ticker)        
    new_dict["Ticker"] = ticker
    new_dict["bid"] = realtime_info.bid
    new_dict["ask"] = realtime_info.ask
    new_dict["last"] = realtime_info.last

    return new_dict 


def get_price(ticker):
    """
    Simplifier for requesting the last price of the asset.
    """
    return RTData(ticker)["last"]




##### DATES HANDLER #####

import datetime

def find_expiry_day(holidays=""):
    """
    The IBOVESPA futures expiry date is on even months at the wednesday closest to the 15th day. 
    If it is a national holiday, it's in the next day.
    This function finds this date.
    """

    hoje = datetime.date.today()
    mes_atual_par = hoje.month % 2 == 0

    if hoje.day < 15 and mes_atual_par:
        data_alvo = datetime.date(hoje.year, hoje.month, 15)

    else:
        if hoje.month != 12:
            updated_mes_par = hoje.month + 1 if hoje.month % 2 == 1 else hoje.month + 2
            updated_year_mes_par = hoje.year
        else:
            updated_mes_par = 2
            updated_year_mes_par = hoje.year + 1

        data_alvo = datetime.date(updated_year_mes_par, updated_mes_par, 15)

    if data_alvo.weekday() != 2:
        
        for i in range(3):
            data_alvo += datetime.timedelta(days=1)
            if data_alvo.weekday() == 2:
                while pd.to_datetime(data_alvo) in list(holidays["Data"]):
                    data_alvo += datetime.timedelta(days=1)
                return data_alvo.strftime("%Y-%m-%d")
            
        data_alvo += datetime.timedelta(days=-3)

        for i in range(3):
            data_alvo += datetime.timedelta(days=-1)
            if data_alvo.weekday() == 2:
                while pd.to_datetime(data_alvo) in list(holidays["Data"]):
                    data_alvo += datetime.timedelta(days=1)
                return data_alvo.strftime("%Y-%m-%d")
    else:
        while pd.to_datetime(data_alvo) in list(holidays["Data"]):
                data_alvo += datetime.timedelta(days=1)
        return data_alvo.strftime("%Y-%m-%d")
            

def business_days_bet(start, end, holidays):
    """
    Gets the number of business days between two days, adjusted for national holidays.
    """
    business_days = pd.bdate_range(start, end)
    business_days = [i for i in business_days if i not in list(holidays["Data"])]

    return len(business_days) - 1


def first_b_day_nextM(date, holidays):
    """
    Passing a base date, returns the first business day for the next month (relative to it).
    """
    first_day_of_next_month = (pd.to_datetime(date) + pd.offsets.MonthBegin(1)).to_pydatetime()
    first_business_day = pd.bdate_range(first_day_of_next_month, first_day_of_next_month + pd.DateOffset(days=4))[0].to_pydatetime()
    first_business_day = pd.to_datetime(first_business_day)

    while first_business_day in list(holidays["Data"]):
        first_business_day += datetime.timedelta(days=1)
    return first_business_day




##### REAL-TIME IBOV PRICING #####

import requests

def comp_ibov_hoje():
    """
    Returns a tuple with:
    1- the most recent IBOVESPA composition
    2- the current IBOVESPA reductor for index pricing
    """
    url = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJsYW5ndWFnZSI6InB0LWJyIiwicGFnZU51bWJlciI6MSwicGFnZVNpemUiOjEyMCwiaW5kZXgiOiJJQk9WIiwic2VnbWVudCI6IjEifQ=="
    response = requests.get(url)

    redutor = response.json().copy()
    redutor = redutor["header"]["reductor"]
    redutor = redutor.replace(".", "").replace(",", ".")
    redutor = float(redutor)

    # data manipulation
    dados = pd.DataFrame(response.json()["results"])[["cod", "theoricalQty"]]
    dados["theoricalQty"] = dados["theoricalQty"].str.replace(".", "", regex=False)
    dados["theoricalQty"] = pd.to_numeric(dados["theoricalQty"])

    return dados, redutor

def open_ibov_tickers(comp_ibov):
    """
    Opens all of the IBOVESPA tickers in MT5.
    """
    for i in list(comp_ibov["cod"]):
        OpenTicker(i)

def price_IBOV(comp_ibov, redutor):
    """
    Returns the real-time IBOVESPA price
    """
    total_sum = 0

    for i in range(len(comp_ibov)):
        ticker = comp_ibov.loc[i, "cod"]
        qtt = comp_ibov.loc[i, "theoricalQty"] 
        ticker_price = get_price(ticker=ticker)
        value = qtt*ticker_price
        value = value / redutor
        total_sum += value

    return round(total_sum, 2)




#### DI INTERPOLATION #####
import numpy as np

def get_interp_DI_FACTOR(DI1_ticker, DI2_ticker, first_leg, second_leg, dist_expiry, method):
    """
    Returns the RiskFree interpolated FACTOR for IBOV pricing. Does not need +1 adjustment.
    """
    di_1 = get_price(DI1_ticker)
    di_2 = get_price(DI2_ticker)
    total_diff = di_2 - di_1
    
    total_days = first_leg + second_leg

    subdivisions = total_diff/total_days

    final_value = di_1 + (first_leg*subdivisions)
    final_value = (final_value/100)

    if method == "normal":
        final_value = ((1 + final_value) ** (dist_expiry/252))

    if method == "continuous":
        final_value = np.exp(final_value * (dist_expiry/252))

    return final_value
