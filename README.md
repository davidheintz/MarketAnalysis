# MarketAnalysis

This program is written by myself, David Heintz

The purpose of this program is to attempt multiple methods of analysis and prediction on recent stock market data using an api from polygon.io and a dataset of 100 stock symbols.

This program currently applies 2 methods.

First: it attempts to diversify one's portfolio by finding the frequency and weight of up/up, up/down, down/up, and down/down between all possible stock pairs and find the pairing with the lowest frequency and weight of down/down (both stocks dropping) for each stock

Second, it finds the period in a stock's history most similar to the recent period of x days and plots the two periods side by side using matplotlib

* this program also calculates the percent change of each stock based on the value (percent change = current - previous / previous)
