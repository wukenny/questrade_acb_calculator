import requests

def RtFxRate(from_currency, to_currency) :
    """Returns real time Fx rate. first draft for api testing 
        NOT in use
    Args:
        from_currency: currency code of from side
        to_currency: currency code of to side
    Returns:
        simply print out returned json file
    Raises:
        RuntimeError: if there was an error trying to fetch data from web
    """
    import pprint
        
    api_key = "1FU56XT1D8W24FMA"
    url = r"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"  
    url += "&from_currency=" + from_currency 
    url += "&to_currency=" + to_currency
    url += "&apikey=" + api_key
   
    # json method format input data object into python dictionary
    # result contains list of nested dictionaries
    res = requests.get(url)
    if not res.ok:
        raise RuntimeError(f'Error fetching "{url}": {res.status_code}')
    
    json_obj = res.json()
  
    pprint.pprint(json_obj)  
    print("After parsing - Realtime Currency Exchange Rate: \n1",
          from_currency, "=",          
          json_obj["Realtime Currency Exchange Rate"]
                ['5. Exchange Rate'], to_currency)
    
def SdUsdToCad(date):
    """Returns a single day USD to CAD exchange rate
    Args:
        date: in date type of which the query based on
    Returns:
        float type of close rate from the Bank of Canada
    Raises:
        RuntimeError: if there was an error trying to fetch data from web
    """
    str_date = date.strftime("%Y-%m-%d")
    url = r"https://www.bankofcanada.ca/valet/observations/FXUSDCAD?"    
    url += "start_date=" + str_date + "&end_date=" + str_date
    res = requests.get(url)
    if not res.ok:
        raise RuntimeError(f'Error fetching "{url}": {res.status_code}')
    
    json_obj = res.json()
    rate_str = json_obj["observations"][0]["FXUSDCAD"]["v"]
    rtn = float(rate_str)    
    return rtn
    
if __name__ == "__main__" :      
    #from_currency = "USD"
    #to_currency = "CAD"    
    #RtFxRate(from_currency, to_currency)
    
    import datetime
    date = datetime.datetime(2021,1,12)
    result = SdUsdToCad(date)
    print(result)