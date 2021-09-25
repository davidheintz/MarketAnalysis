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
# third param 'm' is the multiplier for each applying similarity of each day
# for example, c = 3 days and m = .5: add 1 x deviation for day1, 1.5 x dev for day2, 2 x dev for day3
def find_similar(c, p, m):

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
        comp['combo'] = comp['combo'] + (abs(comp[str(x)] - c[x])*1+(x*m))
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


# gen_indicators method uses params of stock dataframe, along with 2 indices
def gen_indicators(s, ip, mp):

    a = s.copy()
    grow = []
    loss = []
    # calculate percent growth or loss in each period starting from index x
    for x in range(mp, len(a) - ip):
        a[x] = (a[x + ip] - a[x]) / a[x]  # percent growth over period

    # only use calculated values, and sort them to easily access largest and smallest
    a = a.iloc[mp:len(a) - ip, ]
    a = a.sort_values(ascending=False)

    # add items starting at largest (first) to growth dict at index of stock
    # continue adding items with growth > .1, and not conflicting with others
    y = 0
    curr_rank = a.iloc[[y]]
    while curr_rank.iloc[0] > .1:
        is_in = False
        for val in grow:
            if abs(val - curr_rank.index[0]) < 10:
                is_in = True
        if is_in is False:
            grow.append(curr_rank.index[0])
        y += 1
        curr_rank = a.iloc[[y]]

    y = len(a)-1
    curr_rank = a.iloc[[y]]

    # add items starting at smallest (last) to loss dict at index of stock
    # continue adding items with growth < -.1, and not conflicting with others
    while curr_rank.iloc[0] < -.1:
        is_in = False
        for val in loss:
            if abs(val - curr_rank.index[0]) < 10:
                is_in = True
        if is_in is False:
            loss.append(curr_rank.index[0])
        y -= 1
        curr_rank = a.iloc[[y]]

    # return dicts of largest growth/loss periods indexed at their related stocks
    return grow, loss
