'''
Created on May 26, 2021 
@author: Kenny
Based on the code by Chi
'''

import pandas as pd
import argparse
import sys
import os
import textwrap
#from pathlib import Path

class ACB:
    def __init__(self, symbol):
        self.symbol = symbol
        self.shares = 0
        self.total_acb = 0        
        self.total_capital_gain = 0
        #{sell_date:[price,shares,commission,acb,capital_gain]}
        self.dispositions = {}        

    def __str__(self):
        result = ""
        result += "Symbol: " + self.symbol
        result += ", total ACB: " + str(self.total_acb)        
        result += ", capital gain: " + str(self.total_capital_gain)
        result += ", shares: " + str(self.shares)
        return result
    
    # after each transaction, the number of shares can NOT be negative
    # negative shares means either BRW process failed or data error occured
    def Check_Error(self, action, shares):
        err_buy = (action == 'Buy' and self.shares + shares <= 0)
        err_sell = (action == 'Sell' and self.shares - shares < 0)
        if(err_buy or err_sell):
            msg = f'{action} {self.symbol} {shares} share(s) error: '
            msg += f'Current shares is {self.shares};'                
            raise Exception(msg)
        
    def Buy(self, price, shares, commission):
        self.Check_Error('Buy', shares)
        cost = price * shares + commission
        
        self.total_acb += cost
        self.shares += shares        

    def Sell(self, date, price, shares, commission):
        self.Check_Error('Sell', shares)
        proceeds = price * shares - commission
        acb = self.total_acb/self.shares        
        capital_gain = proceeds - (acb * shares)
                
        if self.dispositions.get(date) is None:
            self.dispositions[date] = []
        self.dispositions[date].append([price,shares,commission,acb,capital_gain])         
        
        # the sequence of the following variable assignment is important!        
        self.total_acb = self.total_acb * ((self.shares-shares) / self.shares)  
        self.shares -= shares
        self.total_capital_gain += capital_gain

class ACBCalculator:
    def __init__(self, input_file=None):
        if (input_file is None):
            raise Exception("input file for ACB calculator can NOT be none");

        self.input_file = input_file
        print("input file: ", self.input_file)

        # a list of activities, e.g. buy or sell; key=symbol
        # The list of activities is then sorted by transaction date
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
        #filtered_actions = ['Buy','Sell', 'BRW']
        filtered_actions = ['Buy','Sell']
        result = pd.read_excel(self.input_file,filtered_worksheet)
        result = result.reindex(columns=filtered_columns)
        result = result[result['Action'].isin(filtered_actions)]
      
        for s in result['Symbol'].unique():            
            self.symbol_activities[s] = []
            
        for _, row in result.iterrows():
            s = row['Symbol']
            if s=='H038778': continue # a fix when Action = BRW 
            self.symbol_activities[s].append(row.tolist())            

        for symbol, activities in self.symbol_activities.items():
            # If during the same day, for one symbol there are multiple buy/sell transactions
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
            # The code needs to alert user if there are multiple transaction not one side only,
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
                    self.symbol_ACB[symbol].Sell(date, price, shares * -1, commission)

                print(activity)
                print(self.symbol_ACB[symbol])
                print()
                #print(daily_stats)
            print("\n")
        
        for symbol, acb in self.symbol_ACB.items():
            print("Symbol {}: total capital gain {}".
                  format(symbol, acb.total_capital_gain))

        print("\n\n")

        for symbol, stats in self.symbol_stats.items():
            for date, daily_stats in stats.items():
                if daily_stats[0] > 0 and daily_stats[1] > 0:
                    print("WARNING -> Symbol {} buy transaction {} sell transaction {} on date {}".format
                          (symbol, daily_stats[0], daily_stats[1], date))
def BRW(symbol_from, symbol_to):
    symbol_map = {'DLR': ['DLR.TO', 'H038778']}
    print(symbol_map.get('DLR'))
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''Script to calculate ACB (adjusted total_acb base) and capital gain or loss''',
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