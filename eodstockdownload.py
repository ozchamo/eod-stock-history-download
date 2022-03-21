#!/bin/python3

import sys
import csv
import os
import requests
from datetime import date, datetime

def retrieve_stock_history(stocksymbol, writestockhistorytofile, historydirectory=""):

    # THIS USES EODHISTORICALDATA as the platform

    # PARAMETERS
    # stocksymbol is the ticker with country appended - e.g. AAPL.US
    # writestockhistory file is true if you want to cache the result locally
    # historydirectory is the local directory to cache into

    # RETURNS
    # a list of all days in history, where each day is also a list as described later

    ignorefirstlines = 1 # EODHISTORICALDATA has one line of headers for stock history files

    stockhistoryfile = historydirectory + "/" + stocksymbol + ".csv"

    try:
        os.makedirs(historydirectory, exist_ok = True)
    except OSError as error:
        print("Could not create history directory")

    try:
        csvfilehandler = open(stockhistoryfile, "r")
        csvfile = csv.reader(csvfilehandler)
        print("### Reading in CSV stock price file from CACHE")

    except FileNotFoundError:
        # File does not exist, we get from the web!

        # This one will come from the web!
        key = os.environ["DATA_API_KEY"]

        # https://eodhistoricaldata.com/api/eod/" + stocksymbol
        # will get you:
        # ['Date', 'Open', 'High', 'Low', 'Close', 'Adjusted Close', 'Volume']

        ignorefirstlines = 1
        # The first line of this API resource has ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
        # ALAS, no adjusted close - this requires a serious rewrite or a kludge

        API_URL = "https://eodhistoricaldata.com/api/eod/" + stocksymbol

        # OLDEST IS VERY VERY VERY IMPORTANT! Otherwise the values are provided upside down, something that the data read anf fill algorithms were not designed for
        params = {
            "order": "a",
            "output": "csv",
            "api_token": key,
        }

        print("### Reading in CSV stock price file from API Provider")
        APIresponse = requests.get(API_URL, params)

        csvfile = csv.reader(APIresponse.text.splitlines())

        if writestockhistorytofile:
            with open(stockhistoryfile, mode='wb') as localfile:
                localfile.write(APIresponse.content)

    csvlist = []

    # Configure the appropriate columns for the input
    # We are taking the date and expanding it into 3 columns
    # Year is position 0, thus OPEN is position 3

    # EODHISTORICALDATA provides ['Date', 'Open', 'High', 'Low', 'Close', 'Adjusted Close', 'Volume']
    #

    DATASOURCEDATECOLUMN=0
    DATASOURCEOPENPRICECOLUMN=1
    DATASOURCECLOSEPRICECOLUMN=4
    DATASOURCEVOLUMECOLUMN=6

    firstline = True
    for inputline in csvfile: #Read each line in

        if firstline:
            firstline = False
            if inputline == ['Ticker Not Found.']:
                os.remove(stockhistoryfile)
                return([])

        if ignorefirstlines == 0:

            # sometimes there are days that have null values - look for these to ignore
            if "null" in inputline:
                print("Rejecting with nulls: " + date, inputline)
            else:

                #We read the values in required positions
                datasourcedate = inputline[DATASOURCEDATECOLUMN]  # date is like 2005-12-04 - we change it to 2005,12,04 for homogeneity and ease

                try:
                    datetime.strptime(datasourcedate, "%Y-%m-%d").date()
                except:
                    continue

                datasourceopenprice = float(inputline[DATASOURCEOPENPRICECOLUMN])
                datasourcecloseprice = float(inputline[DATASOURCECLOSEPRICECOLUMN])
                datasourcevolume =  int(inputline[DATASOURCEVOLUMECOLUMN])

                #We assemble the output list - [YY, MM, DD, OPEN, CLOSE, VOLUME]
                outputline = list(map(int, datasourcedate.split("-")))  # Gotta love the simplicity of Python here - NOTE: datesplit is LIST
                outputline.append(datasourceopenprice)
                outputline.append(datasourcecloseprice)
                outputline.append(datasourcevolume)
                csvlist.append(outputline)

        else:
            ignorefirstlines-=1

    # csvlist is a list of day entries, which are in turn lists.
    return(csvlist)

if len(sys.argv) == 1:
    print("ERROR: must pass a stock symbol and country, eg ADBE.US or TLS.AU")
    exit()

stocksymbol = sys.argv[1]

csv_stockpricelist = retrieve_stock_history(stocksymbol, "true", "STOCKHISTORY")

if csv_stockpricelist == []:
    # Stockname was not found
    print("ERROR: The selected stock symbol does not exist!!")
    exit()
