import requests
import pandas as pd
import time


# gen_historical uses param ticker, range, day, and apikey to generate dataframe of stock historical data
def gen_historical(t, a, p, d):

    # generating url from params and getting from web using requests
    api_url = f'https://api.polygon.io/v2/aggs/ticker/{t}/range/{d}/day/{p}?apiKey={a}'
    data = requests.get(api_url).json()

    # returns dataframe from results if stock data found, none if not found
    if 'results' in data:
        df = pd.DataFrame(data['results'])
        return df
    return None


# find_similar uses param of recent and past historical to find instance most similar to recent in past
def find_similar(c, p):

    # generate dataframe where each row i is a sequence of len(c) values from p[i] to p[i+len(c)-1]
    # this allows c to be comparable with each row in p (columns 0 - (len(c)-1))
    comp = pd.DataFrame()
    for x in range(len(c)):
        comp[str(x)] = p.shift(-x)

    comp.dropna(inplace=True)  # clean comp dataframe
    c.reset_index(drop=True, inplace=True)  # reset index of c so it is aligned with comp.columns
    comp['combo'] = 0  # add combo column to comp, initialized to 0

    # iterate 0 -> len(c)
    # comp['combo'] becomes combined diff of recent and past value when compared with each row in comp
    # return comp['combo'] (small value indicates relation between that row and recent data)
    for x in range(len(c)):
        comp['combo'] = comp['combo'] + abs(comp[str(x)] - c[x])
    return comp['combo']


# gen_diversification uses param of two comparable stock datasets
def gen_diversification(x, y):

    # 4 arrays hold values tied to occurrences of: both stocks up, both down, and one up one down
    dbl_up = [0, 0, 0]
    dwn_up = [0, 0, 0]
    up_dwn = [0, 0, 0]
    dbl_dwn = [0, 0, 0]

    # loop through all dates in compared stocks, adjust 1 of the 4 arrays above depending on relation of 2 stocks
    for n in range(1, len(x)):
        # if both stocks >= 0 on that day, update dbl_up array (instances+1, total_x+x[n], total_y+y[n])
        if x[n] >= 0 and y[n] >= 0:
            dbl_up[0] += 1
            dbl_up[1] += x[n]
            dbl_up[2] += y[n]
        elif y[n] >= 0:  # x guaranteed < 0, therefore update dwn_up
            dwn_up[0] += 1
            dwn_up[1] += x[n]
            dwn_up[2] += y[n]
        elif x[n] >= 0:  # y guaranteed < 0, therefore update up_dwn
            up_dwn[0] += 1
            up_dwn[1] += x[n]
            up_dwn[2] += y[n]
        else:  # x and y guaranteed < 0, therefore update dbl_dwn
            dbl_dwn[0] += 1
            dbl_dwn[1] += x[n]
            dbl_dwn[2] += y[n]

    # return array w all 4 of the 3 item arrays from loop above within (shows relation between 2 stocks)
    return [dbl_up, dwn_up, up_dwn, dbl_dwn]


# variables for apikey, range, and day values for url generation
api = '2NeJlmXsI_XiSj8uG3IWHjs8PRvp5rMF'
period = '2019-08-01/2021-09-06'
days = '1'

# read in stock symbols excel file using pandas, only use top 100 stocks
symbols = pd.read_excel('US-Stock-Symbols.xlsx')
symbols = symbols.iloc[:100, :]

# cleaning stock symbols, eliminating all unreadable symbols (only letters allowed)
symbols['Symbol'] = symbols['Symbol'].str.replace(r'[^a-zA-Z].*', '')
symbols.reset_index(drop=True, inplace=True)  # realign index w 0

big_stocks = pd.DataFrame()  # will contain adjusted average stock values for all stocks in symbols
stock_ends = pd.DataFrame()  # will contain end of day stock values for all stocks in symbols

# loop through 100 stock symbols, generate api_url, and store values in big_stocks and stock_ends
for i in range(20):
    for j in range(5):
        single_col = gen_historical(symbols['Symbol'][(i*5)+j], api, period, days)
        if single_col is not None:

            # generate close values for each stock and store in stock_ends dataframe
            stock_ends[symbols['Symbol'][(i*5)+j]] = single_col['c']

            # generate adjusted value to store in big_stocks dataframe
            # store: value - previous day / previous day (which represents % growth/loss)
            single_vw = single_col['vw']
            previous = single_vw.shift(1)
            big_stocks[symbols['Symbol'][(i*5)+j]] = (single_vw - previous) / previous

    time.sleep(60)  # sleep after every 5 because polygon free api only allows for 5 stocks requests per minute
print(big_stocks)
print(stock_ends)

# drop first index of big_stocks because of adjustment, then eliminate all NaN values
big_stocks.drop(big_stocks.index[[0]], inplace=True)
big_stocks.dropna(axis=1, inplace=True)
stock_ends.dropna(axis=1, inplace=True)

# variables needed for loop to store names & div matrices of values minimizing combined loss w 'item'
div_dict = {}
min_inst = 500
min_comb = -500
least_inst = ''
least_comb = ''
li_div = []
lc_div = []

for item in big_stocks.columns:
    for it in big_stocks.columns:
        # if stock not being compared to self
        if item != it:

            # use gen_diversification method to get comparison data for 2 stocks (item and it)
            div = gen_diversification(big_stocks[item], big_stocks[it])

            # store stock w minimum instances for div[3] in all comparisons with 'item'
            if div[3][0] < min_inst:
                min_inst = div[3][0]
                least_inst = it
                li_div = div

            # div[3] contains instances of both stocks being negative
            # therefore, store item with lowest negative combination for all comparisons with 'item'
            if div[3][1] + div[3][2] > min_comb:
                min_comb = div[3][1] + div[3][2]
                least_comb = it
                lc_div = div

    # store 2 minimized diversification values for each item in div_dict
    div_dict[item] = {least_inst, least_comb}
    print(div_dict)

# similarity dataframe to store rep of diff between current and past periods for each stock
similarity = pd.DataFrame()

# store last 10 days in 'last10' and rest of stock historical data in 'past_data'
past_data = big_stocks.iloc[:-10, :]
last10 = big_stocks.iloc[-10:, :]

# use find_similar method to generate similarity statistics for current and every past period for each stock 'item'
for item in last10.columns:
    similarity[item] = find_similar(last10[item], past_data[item])
print(similarity)
