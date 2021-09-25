import pandas as pd
import time
import engine


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
        single_col = engine.gen_historical(symbols['Symbol'][(i*5)+j], api, period, days)
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
sim_dict = {}
max_inst = 0
max_comb = 0
min_inst = 500
min_comb = -500
most_inst = ''
most_comb = ''
least_inst = ''
least_comb = ''

for item in big_stocks.columns:
    for it in big_stocks.columns:
        # if stock not being compared to self
        if item != it:

            # use gen_diversification method to get comparison data for 2 stocks (item and it)
            div = engine.gen_diversification(big_stocks[item], big_stocks[it])

            # store stock w minimum instances for div[3] in all comparisons with 'item'
            if div[3][0] < min_inst:
                min_inst = div[3][0]
                least_inst = it

            # div[3] contains instance of simultaneous loss for both stocks
            # therefore, store item with lowest negative combination for all comparisons with 'item'
            if div[3][1] + div[3][2] > min_comb:
                min_comb = div[3][1] + div[3][2]
                least_comb = it

            # div[0] contains instances of simultaneous growth for both stocks
            # therefore, stock pair with most instances of div[0] have largest correlated growth
            if div[0][0] > max_inst:
                max_inst = div[0][0]
                most_inst = it

            # find stock pair with largest combined value of the growth magnitude from div[0]
            if div[0][1] + div[0][2] > max_comb:
                max_comb = div[0][1] + div[0][2]
                most_comb = it

    # store 2 minimized diversification values for each item in div_dict
    div_dict[item] = {least_inst, least_comb}
    sim_dict[item] = {most_inst, most_comb}

print(div_dict)
print(sim_dict)

# similarity dataframe to store rep of diff between current and past periods for each stock
similarity = pd.DataFrame()

# store last 10 days in 'last10' and rest of stock historical data in 'past_data'
past_data = big_stocks.iloc[:-10, :]
last10 = big_stocks.iloc[-10:, :]

# use find_similar method to generate similarity statistics for current and every past period for each stock 'item'
for item in last10.columns:
    similarity[item] = engine.find_similar(last10[item], past_data[item], 0.1)
print(similarity)

# use gen_indicators method to generate growth and loss dictionaries
grow_dict = {}
loss_dict = {}
for index, col in big_stocks.iteritems():
    grow_dict[index], loss_dict[index] = engine.gen_indicators(col, 10, 20)

print(grow_dict)
print(loss_dict)

# initialize 2 dataframes which will be used as the growth and loss models
grow_model_df = pd.DataFrame()
loss_model_df = pd.DataFrame()

# use concat to add the period indicating growth and loss for each item in both dicts
# grow_model_df contains columns of all periods directly followed by large growth in dict grow
# loss_model_df contains columns of all periods directly followed by large loss in dict grow
for item in big_stocks.columns:
    for i in range(len(grow_dict[item])):
        grow_ind = big_stocks.loc[grow_dict[item][i]-20:grow_dict[item][i]-1, item]
        grow_ind.reset_index(drop=True, inplace=True)
        col = item + str(i)
        grow_model_df = pd.concat([grow_model_df, grow_ind], axis=1)
    for i in range(len(loss_dict[item])):
        loss_ind = big_stocks.loc[loss_dict[item][i]-20:loss_dict[item][i]-1, item]
        loss_ind.reset_index(drop=True, inplace=True)
        col = item + str(i)
        loss_model_df = pd.concat([loss_model_df, loss_ind], axis=1)
print(grow_model_df)
print(loss_model_df)

# using mean on each row in dataframes, we observe average values at each day leading up to large growth/loss
# this can become our fitted model to compare current periods with and determine if they indicate growth or loss
grow_mean = grow_model_df.mean(axis=1)
loss_mean = loss_model_df.mean(axis=1)

# using std on each row in dataframes, we observe the average distance from the mean for each day in leadup period
grow_std = grow_model_df.std(axis=1)
loss_std = loss_model_df.std(axis=1)

# if the mean is roughly zero then this means that the indicators were random and this model will not be useful
# if the standard deviations are very large, then this means that the model will classify indicators too frequently

print(grow_mean)
print(loss_mean)
print(grow_std)
print(loss_std)
