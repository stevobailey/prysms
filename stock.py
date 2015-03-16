#! /opt/local/bin/python
# stock.py contains StockError, stock object defintion, and portfolio object definition

import sys, os, csv, math
import urllib2
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import lines, rc
import numpy as np
from collections import defaultdict
import cPickle as pickle


class StockError(Exception):
  'Base class for execptions raised in this program'
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)








class stock:
  'Stock base class'

  # load on creation, but don't auto-update
  # if datfile doesn't exist, __load() will initialize it
  def __init__(self, ticker):
    self.ticker = ticker
    self.datfile = 'data/' + self.ticker + '.dat'
    self.data = []
    self.date = date(2000, 1, 1) 
    self.date_idx = 0       # row number for this stock's date, for quick access
    self.date_data = dict() # data for this stock's date, for quick access
    self.__load()


  # string is just ticker
  def __str__(self):
    return repr(self.ticker)


  # use pickle
  def update(self):
    url = 'http://ichart.finance.yahoo.com/table.csv?s=' + self.ticker
    try:
      response = urllib2.urlopen(url)
    except urllib2.HTTPError:
      raise StockError('Error: Ticker symbol ' + self.ticker + ' could not be found.')
    except urllib2.URLError:
      raise StockError('Error: Check your internet connection.')
    cr = csv.DictReader(response)
    for row in cr:
      row['Date'] = datetime.strptime(row['Date'], "%Y-%m-%d").date() # save time by preconverting dates
      self.data.append(row)  # store csv data in memory for quick access
    pickle.dump(self.data, open(self.datfile, 'wb'), -1)


  # load data from datfile into memory
  def __load(self):
    if os.path.isfile(self.datfile):
      self.data = pickle.load(open(self.datfile, 'rb'))
    else:
      self.update()


  # grab latest date available, returns date object
  def latest_date(self):
    return self.data[0]['Date']

    
  # grab earliest date available, returns date object
  def earliest_date(self):
    return self.data[-1]['Date']


  # set the date for this stock
  def set_date(self, date):
    self.date = date
    [self.date_data, self.date_idx] = self.__binsearch_idx(self.data, self.date)


  # step the date for this stock
  def step_date(self):
    self.date_idx -= 1
    self.date_data = self.data[self.date_idx]
    self.date = self.date_data['Date']


  # grab the data for a specific day, where day is a datetime.date object
  def __row(self, day):
    if day == self.date:
      return self.date_data
    else:
      return self.__binsearch(self.data, day)

  
  # binary search for data on a specific day
  def __binsearch(self, subdata, day):
    if len(subdata) == 0:
      raise StockError('Error: No data found for date ' + str(day) + ' for stock ' + self.ticker)
    else:
      midpoint = len(subdata)//2
      middata = subdata[midpoint]['Date']
      if middata == day:
        return subdata[midpoint]
      else:
        if day < middata:
          return self.__binsearch(subdata[midpoint+1:], day)
        else:
          return self.__binsearch(subdata[:midpoint], day)


  # binary search for data on a specific day, also returns index
  def __binsearch_idx(self, subdata, day, idx=0):
    if len(subdata) == 0:
      raise StockError('Error: No data found for date ' + str(day))
    else:
      midpoint = len(subdata)//2
      middata = subdata[midpoint]['Date']
      if middata == day:
        return [subdata[midpoint], idx+midpoint]
      else:
        if day < middata:
          return self.__binsearch_idx(subdata[midpoint+1:], day, idx+midpoint+1)
        else:
          return self.__binsearch_idx(subdata[:midpoint], day, idx)


  # grab the data for a range of days
  def __rows(self, start, end):
    rows = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        rows.append(row)
    if not rows:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return rows


  # get closing price for a specific day
  # day must be a datetime.date object
  def close(self, day, adjusted=True):
    return float(self.__row(day)['Adj Close' if adjusted else 'Close'])


  # get opening price for a specific day
  # day must be a datetime.date object
  def open(self, day, adjusted=True):
    row = self.__row(day)
    if adjusted:
      return float(row['Adj Close'])/float(row['Close'])*float(row['Open'])
    else:
      return float(row['Open'])


  # get high price for a specific day
  # day must be a datetime.date object
  def high(self, day, adjusted=True):
    row = self.__row(day)
    if adjusted:
      return float(row['Adj Close'])/float(row['Close'])*float(row['High'])
    else:
      return float(row['High'])


  # get low price for a specific day
  # day must be a datetime.date object
  def low(self, day, adjusted=True):
    row = self.__row(day)
    if adjusted:
      return float(row['Adj Close'])/float(row['Close'])*float(row['Low'])
    else:
      return float(row['Low'])


  # get volume for a specific day
  def volume(self, day, adjusted=True):
    row = self.__row(day)
    if adjusted:
      return int(round(float(row['Close'])/float(row('Adj Close'))*row['Volume']))
    else:
      return int(row['Volume'])


  # get average volume for a range of days
  def average_volume(self, start, end, adjusted=True):
    vsum = 0
    for row in self.__rows(start, end):
      if adjusted:
        vsum += int(round(float(row['Close'])/float(row('Adj Close'))*row['Volume']))
      else:
        vsum += int(row['Volume'])
    return int(round(vsum / float(len(rows))))


  # get closing prices for a range of days
  def closes(self, start, end, adjusted=True):
    closes = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        closes.append(float(row['Adj Close' if adjusted else 'Close']))
    if not closes:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return closes


  # get opening prices for a range of days
  def opens(self, start, end, adjusted=True):
    opens = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        if adjusted:
          opens.append(float(row['Adj Close'])/float(row['Close'])*float(row['Open']))
        else:
          opens.append(float(row['Open']))
    if not opens:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return opens


  # get high prices for a range of days
  def highs(self, start, end, adjusted=True):
    highs = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        if adjusted:
          highs.append(float(row['Adj Close'])/float(row['Close'])*float(row['High']))
        else:
          highs.append(float(row['High']))
    if not highs:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return highs


  # get low prices for a range of days
  def lows(self, start, end, adjusted=True):
    lows = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        if adjusted:
          lows.append(float(row['Adj Close'])/float(row['Close'])*float(row['Low']))
        else:
          lows.append(float(row['Low']))
    if not lows:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return lows


  # get volume for a range of days
  def volumes(self, start, end, adjusted=True):
    volumes = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        if adjusted:
          volumes.append(int(round(float(row['Close'])/float(row('Adj Close'))*row['Volume'])))
        else:
          volumes.append(int(row['Volume']))
    if not volumes:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return volumes


  # get trading days for a range of days
  def days(self, start, end):
    days = []
    for row in self.data:
      day = row['Date']
      if day >= start and day <= end:
        days.append(row['Date'])
    if not days:
      raise StockError('Error: No data found between dates ' + str(start) + ' and ' + str(end) + ' (inclusive)')
    return days


  # plots OHLC chart for a range of days
  def plot_ohlc(self, start, end):
    # not very efficient but quick for single plots
    days = self.days(start, end)
    bases = self.lows(start, end)
    highs = self.highs(start, end)
    deltas = np.array(highs)-np.array(bases)
    closes = self.closes(start, end)
    opens = self.opens(start, end)
    green_days, green_deltas, green_bases, green_opens, green_closes = [], [], [], [], []
    red_days, red_deltas, red_bases, red_opens, red_closes = [], [], [], [], []
    for day, base, delta, o, c in zip(days, bases, deltas, opens, closes):
      if o < c:
        green_days.append(day)
        green_deltas.append(delta)
        green_bases.append(base)
        green_opens.append(o)
        green_closes.append(c)
      else:
        red_days.append(day)
        red_deltas.append(delta)
        red_bases.append(base)
        red_opens.append(o)
        red_closes.append(c)
    width = 0
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22}
    rc('font', **font)
    ax = plt.axes()
    rectsg = ax.bar(green_days, green_deltas, width, bottom=green_bases, color='#4CBB17', edgecolor='#4CBB17')
    rectsr = ax.bar(red_days, red_deltas, width, bottom=red_bases, color='#FF0000', edgecolor='#FF0000')
    ax.set_yscale('log')
    ymin = min(bases)*0.99
    ymax = max(highs)*1.01
    ax.set_ylim([ymin, ymax])
    ax.yaxis.set_ticks(np.logspace(math.log10(ymin), math.log10(ymax), num=20))
    ax.set_yticks([], minor=True)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.2f'))
    plt.ylabel('Price (USD)')
    plt.title(self.ticker)
    for opening, closing, bar in zip(green_opens, green_closes, rectsg):
      x, w = bar.get_x(), 0.2
      ax.plot((x - w, x), (opening, opening), color='#4CBB17')
      ax.plot((x, x + w), (closing, closing), color='#4CBB17')
    for opening, closing, bar in zip(red_opens, red_closes, rectsr):
      x, w = bar.get_x(), 0.2
      ax.plot((x - w, x), (opening, opening), color='#FF0000')
      ax.plot((x, x + w), (closing, closing), color='#FF0000')
    plt.show()


  # returns the next legal trading day after the specified day
  def next_day(self, day):
    if day == self.date:
      return self.data[self.date_idx-1]['Date']
    else:
      next_day = day + timedelta(days=1)
      error = True
      while error:
        try:
          val = self.__binsearch(self.data, next_day)
        except StockError:
          next_day = next_day + timedelta(days=1)
        else:
          error = False
        if error and next_day > self.latest_date():
          raise StockError('Error: No data for ' + self.ticker + ' after ' + str(day) + '.')
      return next_day











# investment portfolio object
class portfolio:
  'Contains portfolio information, including money, stocks bought, and other stock trading metadata'
  
  # initialize portfolio with money and commission rate
  def __init__(self, money=0, commission=10, date=date(2000, 1, 1)):
    self.money = money # liquid funds
    self.tmoney = money # funds available for trading
    self.value = money # money + shares times current prices
    self.commission = commission

    # positions contains a list of stock objects currently held by portfolio
    self.positions = [] 

    # these dictionaries are all indexed by stock tickers, specifically those found in positions
    self.shares = defaultdict(lambda: 0)        # how many shares of a stock this portfolio contains
    self.buyprices = dict()                     # prices at which each stock was bought
    self.maxprices = dict()                     # maximum prices seen since shares were purchased, including daily highs
    self.minprices = dict()                     # minimum prices seen since shares were purchased, including daily lows
    self.curprices = dict()                     # current (closing) prices for each stock
     
    # current date for this portfolio
    self.date = date
    self.timer = stock('AAPL') # reference stock for next_day
    self.timer.set_date(date)

    # buy and sell orders are executed at each tick of date
    self.buy_orders = []
    self.sell_orders = []


  # print portfolio info
  def __str__(self):
    print '--------------------------------------------------------'
    print 'Portfolio:'
    print '--------------------------------------------------------'
    print 'Date  = ' + str(self.date)
    print 'Money = %0.2f' % (self.money)
    print 'TMoney = %0.2f' % (self.tmoney)
    print 'Value = %0.2f' % (self.value)
    if len(self.positions) > 0:
      print '--------------------------------------------------------'
      print 'Positions:'
      print '--------------------------------------------------------'
      print '|  Ticker  |  Shares  |   Buy$   |   Cur$   |    G/L   |'
      for p in self.positions:
        print '--------------------------------------------------------'
        gl = (self.curprices[p.ticker]-self.buyprices[p.ticker])/self.buyprices[p.ticker]*100
        print '|' + p.ticker.center(10) + '|' + str(self.shares[p.ticker]).center(10) + '|' + ('%0.2f' % self.buyprices[p.ticker]).center(10) + '|' + ('%0.2f' % self.curprices[p.ticker]).center(10) + '|' + ('%0.2f%%' % gl).center(10) + '|'
    if len(self.buy_orders) > 0:
      print '--------------------------------------------------------'
      print 'Buy Orders:'
      print '--------------------------------------------------------'
      print '|  Ticker  |  Shares  |  Limit$  |  Stop$   |   Exp    |'
      for p in self.buy_orders:
        print '--------------------------------------------------------'
        print '|' + p[0].ticker.center(10) + '|' + str(p[1]).center(10) + '|' + ('%0.2f' % p[2] if p[2] else 'N/A').center(10) + '|' + ('%0.2f' % p[3] if p[3] else 'N/A').center(10) + '|' + (str(p[4]) if p[4] else 'GTC').center(10) + '|'
    if len(self.sell_orders) > 0:
      print '--------------------------------------------------------'
      print 'Sell Orders:'
      print '--------------------------------------------------------'
      print '|  Ticker  |  Shares  |  Limit$  |  Stop$   |   Exp    |'
      for p in self.sell_orders:
        print '--------------------------------------------------------'
        print '|' + p[0].ticker.center(10) + '|' + str(p[1]).center(10) + '|' + ('%0.2f' % p[2] if p[2] else 'N/A').center(10) + '|' + ('%0.2f' % p[3] if p[3] else 'N/A').center(10) + '|' + (str(p[4]) if p[4] else 'GTC').center(10) + '|'
    return '--------------------------------------------------------\n'




  # puts in a buy order
  # default is market order, but limit and stop values can be specified
  #   limit order is executed at limit price if price is reached during a day, or at open if open < limit
  #   stop order is executed at stop price if price is reached during a day, or at open if open > stop
  # order expiration is GTC unless a date object is specified
  def buy(self, stock, shares, limit=False, stop=False, exp=False):
    if exp and exp <= self.date:
      raise StockError('Error: Order expiration date must be after current date.')
    if stop and limit and stop < limit:
      print 'Warning: Buy order has stop price less than limit price. This becomes a market order.'
      limit = False
      stop = False
    if stop:
      self.tmoney = self.tmoney - stop*shares
    elif limit: 
      self.tmoney = self.tmoney - limit*shares
    else:
      self.tmoney = self.tmoney - stock.close(self.date)*shares
    order = [stock, shares, limit, stop, exp]
    self.buy_orders.append(order)


  # puts in a sell order
  # if shares is unspecified or <= zero, all shares are sold
  # default is market order, but limit and stop values can be specified
  #   limit order is executed at limit price if price is reached during a day, or at open if open > limit
  #   stop order is executed at stop price if price is reached during a day, or at open if open < stop
  # order expiration is GTC unless a date object is specified
  def sell(self, stock, shares=0, limit=False, stop=False, exp=False):
    if exp and exp <= self.date:
      raise StockError('Error: Order expiration date must be after current date.')
    if stop and limit and stop > limit:
      print 'Warning: Sell order has stop price greater than limit price. This becomes a market order.'
      limit = False
      stop = False
    if shares > 0 and self.shares[stock.ticker] < shares:
      raise StockError('Error: Cannot sell more shares than you own.')
    elif shares <= 0:
      if self.shares[stock.ticker] == 0:
        raise StockError('Error: This portfolio does not own any shares of ' + stock.ticker + '.')
      else:
        shares = self.shares[stock.ticker]
    for so in self.sell_orders:
      if so[0] == stock and so[1] + shares > self.shares[stock.ticker]:
        raise StockError('Error: Multiple sell orders of stock ' + stock.ticker + ' exceed the shares owned.')
    order = [stock, shares, limit, stop, exp]
    self.sell_orders.append(order)


  # check existing orders and execute as needed
  def __exec_orders(self):

    # buy orders
    # order formatting: [stock, shares, limit, stop, exp]
    new_buy_orders = []
    for bo in self.buy_orders:
      if bo[4] and bo[4] <= self.date:
        continue
      # load stock from position if it's in there already
      s = bo[0]
      popen = s.open(self.date)
      if bo[2]: # limit order
        if popen < bo[2]:
          self.__ibuy(s, bo[1], popen)
          continue
        elif s.low(self.date) <= bo[2]:
          self.__ibuy(s, bo[1], bo[2])
          continue
      if bo[3]: # stop order
        if popen > bo[3]:
          self.__ibuy(s, bo[1], popen)
          continue
        elif s.high(self.date) >= bo[3]:
          self.__ibuy(s, bo[1], bo[3])
          continue
      if not bo[2] and not bo[3]: # market order
        self.__ibuy(s, bo[1], popen)
        continue
      new_buy_orders.append(bo)
    self.buy_orders = new_buy_orders

    # sell orders
    # order formatting: [stock, shares, limit, stop, exp]
    new_sell_orders = []
    for so in self.sell_orders:
      if so[4] and so[4] <= self.date:
        continue
      s = False
      for pos in self.positions:
        if pos.ticker == so[0].ticker:
          s = pos
      if not s:
        raise StockError('Error: Tried to sell shares of unowned stock!')
      popen = s.open(self.date)
      if so[2]: # limit order
        if popen > so[2]:
          self.__isell(s, so[1], popen)
          continue
        elif s.high(self.date) >= so[2]:
          self.__isell(s, so[1], so[2])
          continue
      if so[3]: # stop order
        if popen < so[3]:
          self.__isell(s, so[1], popen)
          continue
        elif s.low(self.date) <= so[3]:
          self.__isell(s, so[1], so[3])
          continue
      if not so[2] and not so[3]: # market order
        self.__isell(s, so[1], popen)
        continue
      new_sell_orders.append(so)
    self.sell_orders = new_sell_orders


  # buy a stock
  def __ibuy(self, stock, shares, price):
    if not stock in self.positions:
      self.positions.append(stock)
      self.shares[stock.ticker] = shares
      self.buyprices[stock.ticker] = price
      self.maxprices[stock.ticker] = price
      self.minprices[stock.ticker] = price
    else:
      existing_shares = self.shares[stock.ticker]
      self.shares[stock.ticker] = existing_shares+shares
      self.buyprices[stock.ticker] = (self.buyprices[stock.ticker]*existing_shares+price*shares)/(existing_shares+shares)
    self.money -= price*shares-self.commission
        

  # sell a stock
  def __isell(self, stock, shares, price):
    if shares == self.shares[stock.ticker]:
      self.positions.remove(stock)
      del self.shares[stock.ticker] 
      del self.buyprices[stock.ticker] 
      del self.maxprices[stock.ticker] 
      del self.minprices[stock.ticker] 
      del self.curprices[stock.ticker] 
    else:
      self.shares[stock.ticker] -= shares
    self.money += price*shares-self.commission
      

  # increments the date, executes orders, and updates current value
  def step(self):
    updated = False
    self.timer.step_date()
    self.date = self.timer.date
    self.__exec_orders()
    self.value = self.money
    self.tmoney = self.money
    for bo in self.buy_orders:
      if bo[3]:
        self.tmoney = self.tmoney - bo[3]*bo[1]
      elif bo[2]:
        self.tmoney = self.tmoney - bo[2]*bo[1]
      else:
        self.tmoney = self.tmoney - bo[0].close(self.date)*bo[1]
    for s in self.positions:
      #s.step_date()
      close = s.close(self.date)
      high = s.high(self.date)
      low = s.low(self.date)
      self.curprices[s.ticker] = close
      if low < self.minprices[s.ticker]:
        self.minprices[s.ticker] = low
      if high > self.maxprices[s.ticker]:
        self.maxprices[s.ticker] = high
      self.value += close*self.shares[s.ticker]
