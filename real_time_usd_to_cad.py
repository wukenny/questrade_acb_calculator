def RtFxRate(from_currency, to_currency) :
    import requests, pprint
    
    api_key = "1FU56XT1D8W24FMA"
    url = r"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"  
    url += "&from_currency=" + from_currency 
    url += "&to_currency=" + to_currency 
    url += "&apikey=" + api_key
   
    # json method format input data object into python dictionary
    # result contains list of nested dictionaries
    result = requests.get(url).json()
  
    pprint.pprint(result)  
    print("After parsing - Realtime Currency Exchange Rate: \n1",
          from_currency, "=",          
          result["Realtime Currency Exchange Rate"]
                ['5. Exchange Rate'], to_currency)    
    
if __name__ == "__main__" :
      
    from_currency = "USD"
    to_currency = "CAD"
  
    RtFxRate(from_currency, to_currency)
