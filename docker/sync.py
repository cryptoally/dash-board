from firebase import firebase
import subprocess
import json
import datetime
import requests
import config

CONFIG_FILE_PATH = "/root/data/dash-board/docker/config.ini"


def chunks(s, n):
    for start in range(0, len(s), n):
        yield s[start:start+n]


def get_price(request, exchange, market):
    exchanges = {
        'cryptsy': ['return', 'markets', market, 'lasttradeprice'],
        'bittrex': ['result', 'Last'],
        'bitfinex': ['last_price'],
        'btce': [market, 'last'],
        'bitstamp': ['last'],
        'okcoin': ['ticker', 'last'],
        'poloniex': [market, 'last']
    }
    val = request
    if exchange in exchanges:
        for i in exchanges[exchange]:
            val = val.get(i, {})
        try:
            output = float(val)
            return output
        except Exception as e:
            print e
    return None


def main():
    appconfig = config.getConfiguration(CONFIG_FILE_PATH)
    if appconfig is None:
        message = "Error parsing config file"
        raise Exception(message)

    print appconfig
    required_config_keys = ['firebase']
    for key in required_config_keys:
        if key not in appconfig:
            message = "*** ERROR: key \'%s\' is required" % key
            raise Exception(message)

    dashstats_auth = firebase.FirebaseAuthentication(appconfig['firebase']['token'], appconfig['firebase']['email'])
    dashstats = firebase.FirebaseApplication(appconfig['firebase']['url'], dashstats_auth)

    #run dash-cli getmininginfo
    #dashd should already been started
    getmininginfo = subprocess.check_output(["dash-cli","-datadir=/root/data","-conf=/root/data/dash.conf" ,"getmininginfo"])
    getmininginfo = json.loads(getmininginfo)
    print getmininginfo

    #run dash-cli masternode count
    masternodecount = subprocess.check_output(["dash-cli","-datadir=/root/data", "-conf=/root/data/dash.conf" ,"masternode", "count"])
    print "masternodecount: %s" % masternodecount

    #update firebase values
    hashrate = round(float(getmininginfo["networkhashps"])/1000000000, 2)

    #run dash-cli spork show
    spork = subprocess.check_output(["dash-cli","-datadir=/root/data","-conf=/root/data/dash.conf" ,"spork", "show"])
    spork = json.loads(spork)
    payment_enforcement = "On"
    unix_time_now = datetime.datetime.utcnow()
    unix_time_now = unix_time_now.strftime("%s")
    print "unix_time_now: %s" % unix_time_now
    print "SPORK_8_MASTERNODE_PAYMENT_ENFORCEMENT: %s" % spork["SPORK_8_MASTERNODE_PAYMENT_ENFORCEMENT"]

    #check if masternode payments enforcement is enabled
    if int(spork["SPORK_8_MASTERNODE_PAYMENT_ENFORCEMENT"]) > int(unix_time_now):
        payment_enforcement = "Off"

    #get average DASH-BTC from cryptsy, bittrex and bitfinex
    DashBtc = {
        'cryptsy': {'url': 'http://pubapi2.cryptsy.com/api.php?method=singlemarketdata&marketid=155', 'fn_price': get_price, 'exchange': 'cryptsy', 'market': 'DRK'},
        'bittrex':  {'url': 'https://bittrex.com/api/v1.1/public/getticker?market=btc-dash', 'fn_price': get_price, 'exchange': 'bittrex', 'market': 'DRK'},
        'poloniex': {'url': 'https://poloniex.com/public?command=returnTicker', 'fn_price': get_price, 'exchange': 'poloniex', 'market': 'BTC_DASH'}
        }

    avg_price_dashbtc = []
    for key, value in DashBtc.iteritems():
        try:
            r = requests.get(value['url'])
            try:
                output = json.loads(r.text)
                price = value['fn_price'](output, value['exchange'], value['market'])
                if price is not None:
                    avg_price_dashbtc.append(price)
            except Exception as e:
                print e
                print "Could not get price from %s:%s" % (value['exchange'], value['market'])
        except requests.exceptions.RequestException as e:
            print e
            print "Could not get price from %s:%s" % (value['exchange'], value['market'])
    print "avg_price_dashbtc: %s" % avg_price_dashbtc
    if len(avg_price_dashbtc) > 0:
        DASHBTC = reduce(lambda x, y: x+y, avg_price_dashbtc)/len(avg_price_dashbtc)
        print avg_price_dashbtc
        print "AVG DASHBTC: %s" % round(DASHBTC, 5)

    #get average BTC-USD from btce, bitstamp, bitfinex
    BtcUsd = {
        'btce': {'url': 'https://btc-e.com/api/3/ticker/btc_usd', 'fn_price': get_price, 'exchange': 'btce', 'market': 'btc_usd'},
        'bitstamp': {'url': 'https://www.bitstamp.net/api/ticker/', 'fn_price': get_price, 'exchange': 'bitstamp', 'market': 'BTCUSD'},
        'bitfinex': {'url': 'https://api.bitfinex.com/v1/pubticker/BTCUSD', 'fn_price': get_price, 'exchange': 'bitfinex', 'market': 'BTCUSD'},
        'okcoin': {'url': 'https://www.okcoin.com/api/v1/ticker.do?symbol=btc_usd', 'fn_price': get_price, 'exchange': 'okcoin', 'market': 'BTCUSD'},
    }
    avg_price_btcusd = []
    for key, value in BtcUsd.iteritems():
        try:
            r = requests.get(value['url'])
            try:
                output = json.loads(r.text)
                price = value['fn_price'](output, value['exchange'], value['market'])
                if price is not None:
                    avg_price_btcusd.append(price)
            except Exception as e:
                print e
                print "Could not get price from %s:%s" % (value['exchange'], value['market'])
        except requests.exceptions.RequestException as e:
            print e
            print "Could not get price from %s:%s" % (value['exchange'], value['market'])
    if len(avg_price_btcusd) > 0:
        BTCUSD = reduce(lambda x, y: x+y, avg_price_btcusd)/len(avg_price_btcusd)
        print avg_price_btcusd
        print "AVG BTCUSD: %s" % round(BTCUSD, 8)
        #f.put("", "priceBTCUSD", "$%s" % round(BTCUSD, 2))
        DASHUSD = "$%s" % round(float(BTCUSD * DASHBTC), 2)
        print "DASHUSD: %s" % DASHUSD

    output = {"difficulty": round(getmininginfo["difficulty"], 2), "enforcement": payment_enforcement,
        "hashrate": hashrate, "lastblock": getmininginfo["blocks"], "masternodecount": masternodecount, "price": round(float(BTCUSD * DASHBTC), 2),
        "priceBTC": round(DASHBTC, 5), "priceBTCUSD": round(BTCUSD, 2), "timestamp": {".sv": "timestamp"}
        }

    #get total coins supply from Chainz
    try:
        r = requests.get("http://chainz.cryptoid.info/dash/api.dws?q=totalcoins")
        int_total_coins = r.text.split(".")[0]
        try:
            #validate request
            int(int_total_coins)
            inv_total_coins = int_total_coins[::-1]
            availablesupply = ",".join(chunks(inv_total_coins, 3))[::-1]
            print "Available supply: %s" % availablesupply
            output.update({"availablesupply": availablesupply})
            #f.put("", "availablesupply", availablesupply)
        except ValueError:
            #reply is not an integer
            print "\033[91m chainz reply is not valid \033[0m"
    except requests.exceptions.RequestException as e:
        print e

    dashstats.post("stats", output)
    print "sync ended"

if __name__ == "__main__":
    main()
