#! /usr/bin/python

'''
Created on Apr. 3, 2021
@author: chi
updated by Kenny on 2021-05-24
'''

import pandas as pd
import argparse
import sys
import os
import textwrap
import pprint
#from pathlib import Path

class ACB:
    def __init__(self, symbol):
        self.symbol = symbol
        self.shares = 0
        self.total_acb = 0
        self.acb = 0
        self.capital_gain = 0

    def __str__(self):
        result = ""
        result += "Symbol: " + self.symbol
        result += ", total ACB: " + str(self.total_acb)
        #result += ", ACB: " + str(self.acb)
        result += ", capital gain: " + str(self.capital_gain)
        result += ", shares: " + str(self.shares)
        return result

    # price, shares, commission all require to be NOT negative
    def Buy(self, price, shares, commission):
        if (self.shares + shares <= 0):
            raise Exception("Current shares for symbol {} is {}, buy {} shares".format(
                self.symbol, self.shares, shares))

        self.shares += shares
        self.total_acb += price * shares + commission
        self.acb = self.total_acb / self.shares

    # price, shares, commission all require to be NOT negative
    def Sell(self, price, shares, commission):
        if (self.shares - shares < 0):
            raise Exception("Current shares for symbol {} is {}, sell {} shares".format(
                self.symbol, self.shares, shares))

        old_shares = self.shares
        new_shares = old_shares - shares
        old_acb = self.acb

        if new_shares == 0:
            self.total_acb = 0
            self.acb = 0
        else:
            self.total_acb = ( new_shares / old_shares ) * self.total_acb
            # average ACB is NOT changed when sell

        self.shares = new_shares
        self.capital_gain += price * shares - commission - old_acb * shares

class ACBCalculator:
    def __init__(self, input_file=None):
        if (input_file is None):
            raise Exception("input file for ACB calculator can NOT be none");

        self.input_file = input_file
        print("input file: ", self.input_file)

        # a list of activities, e.g. buy or sell
        # The list of activities is sorted by transaction date
        self.symbol_activities = {}
        
        # The dictionary key is transaction date
        # value is a pair { number of buy transaction, number of sell transaction }
        # It's used to alert if there are both buy and sell for a symbol on the same day
        # because it affects ACB calculation and capital gain/loss result
        self.symbol_stats = {}

        # From symbol to its ACB
        self.symbol_ACB = {}
        self.read_data()

    def read_data(self):
        # read data from Activities worksheet
        # keeps only the filtered columns and 'buy/sell' action type for ACB calculation
        filtered_worksheet = 'Activities'
        filtered_columns = ["Transaction Date", "Action", "Symbol",
                            "Quantity", "Price", "Gross Amount",
                            "Commission", "Net Amount"]
        filtered_actions = ['Buy','Sell']
        result = pd.read_excel(self.input_file,filtered_worksheet)
        result = result.reindex(columns=filtered_columns)
        result = result[result['Action'].isin(filtered_actions)]
        # print(result.info())
        # print(result.head())
        # get all the unique symbols
        # for i, row in result.iterrows():
        #     self.symbols[row['Symbol']] = 1
        #pprint.pprint(self.symbols, width=1)        
        for s in result['Symbol'].unique():
            print(f'=== {s} starts ===')
            self.symbol_activities[s] = []
            for i in range(result.shape[0]):
                symbol = result.iloc[i]['Symbol']

                if ( s == symbol ):
                    activity = list(result.iloc[i])
                    self.symbol_activities[symbol].append(activity)
                    #pprint.pprint(self.symbol_activities, width=1)
                    print(activity)        
            print(f'=== {s} ends ======\n')
            #=========================================#
            #wait = input("Press Enter to continue.")
            #=========================================#

        for symbol, activities in self.symbol_activities.items():
            # If during the same day, for one symbol there are multiple transactions
            # The order of buy and sell matters when calculating ACB and capital gain/loss
            # if there are buy and sell. If the transactions are one side only, e.g.
            # only buy or only sell, the order does not matter.
            # However Questrade excel file for activities does NOT include the precise order
            # , only the transaction date. Here we sort on a composite key of
            # [date, transaction side, price, quantity]
            # The purpose is to make it consistent to calculate ACB and capital across different
            # years. It might vary a bit within a year but should be consistent across years
            # as long as you use the same order (sorting) when calculate carry-over from the previous
            # years.
            # The code needs to alert if there are multiple transaction not one side only,
            # happened on the same day for the same symbol.
            activities.sort(key=lambda x:(x[0], x[1], x[4], x[3]))

            if self.symbol_ACB.get(symbol) is None:
                self.symbol_ACB[symbol] = ACB(symbol)

            print("Sorted activity for symbol {}".format(symbol))
            for activity in activities:
                if self.symbol_stats.get(symbol) is None:
                    self.symbol_stats[symbol] = {}

                stats = self.symbol_stats[symbol]
                date = activity[0]
                action = activity[1]
                shares = activity[3] # shares is negative when sell, positive when buy
                price = activity[4]  # price is always positive
                commission = activity[6] * -1   # commission is always negative

                if stats.get(date) is None:
                    stats[date] = [0, 0]  # 0 buy, 0 sell

                daily_stats = stats[date]
                if action == "Buy":
                    daily_stats[0] += 1
                    self.symbol_ACB[symbol].Buy(price, shares, commission)
                else:
                    daily_stats[1] += 1
                    self.symbol_ACB[symbol].Sell(price, shares * -1, commission)

                print(activity)
                print(self.symbol_ACB[symbol])
                print()
                #print(daily_stats)
            print("\n")

        total_capital_gain = 0
        for symbol, acb in self.symbol_ACB.items():
            total_capital_gain += acb.capital_gain
            print("Symbol {} capital gain {}, total capital gain {}".
                  format(symbol, acb.capital_gain, total_capital_gain))

        print("\n\n")

        for symbol, stats in self.symbol_stats.items():
            for date, daily_stats in stats.items():
                if daily_stats[0] > 0 and daily_stats[1] > 0:
                    print("WARNING -> Symbol {} buy transaction {} sell transaction {} on date {}".format
                          (symbol, daily_stats[0], daily_stats[1], date))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''Script to calculate ACB (adjusted cost base) and capital gain or loss''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--input_file", default=None, type=str,
        help = textwrap.dedent(
'''input_file can be absolute path or relative path to the current working directory\n'''
'''if not specified the script tries to read the excel file under the current working directory\n'''
'''otherwise it reads from the specified directory\n'''
'''input_dir can contain multiple levels'''
        )
    )

    args = parser.parse_args()

    calculator = ACBCalculator(args.input_file)
