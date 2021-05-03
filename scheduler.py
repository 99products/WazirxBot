from datetime import datetime
from decimal import Decimal
from queue import Queue
from deta import app, Deta
import db

import telegram
import requests
import json


@app.lib.cron()
def schedule_quote(event):
    fetch_alerts();
    return "ok"

def fetch_alerts():
    responsejson = requests.get('https://api.wazirx.com/api/v2/tickers').json()
    alertslist = db.fetch_all_alerts()
    print(alertslist)

    alerts_to_notify=[]
    alert_messages=[]
    for alert in alertslist:
        currentvalue=responsejson[alert['token']]['last']
        triggervalue=alert['price']
        condition =alert['condition']
        if condition>0 and Decimal(currentvalue)>=Decimal(triggervalue):
            alerts_to_notify.append(alert)
            alert_messages.append(alert['token']+' is at '+currentvalue+' '+' greater than '+triggervalue)
        if condition<0 and Decimal(currentvalue)<=Decimal(triggervalue):
            alerts_to_notify.append(alert)
            alert_messages.append(alert['token'] + ' is at ' + currentvalue + ' ' + ' less than ' + triggervalue)

    for index,alert in enumerate(alerts_to_notify):
        bot.sendMessage(chat_id=alert['user'],text=alert_messages[index])
        db.delete(alert['key'])


telegram_token=json.load(open('config.json','r'))['telegram_token']
bot = telegram.Bot(token=telegram_token)
