from datetime import datetime
from queue import Queue
from decimal import Decimal
import telegram
from telegram import InlineKeyboardButton,InlineKeyboardMarkup,Update
import requests
from telegram.ext import Dispatcher, CallbackQueryHandler, CallbackContext
import db
import json
from deta import App
from fastapi import Request, FastAPI


app = App(FastAPI())

@app.get("/")
def hello_world():
    return "Working.."


@app.post("/")
async def process(request:Request):
    request_data = await request.json()
    update = telegram.Update.de_json(request_data, bot)
    dispatcher.process_update(update)
    if update.message:
        text=update.message.text.lower()
        if(text=='/alerts' or text=='alerts'):
            show_alerts(update)
        elif (text=='/start' or text=='start' or text=='/help' or text=='help'):
            start(update)
        else:
            fetchAndCreateAlert(update)
    return 'ok'


def show_alerts(update):
    responsestr,keyboards=fetch_alerts(update.message.chat.id)
    bot.sendMessage(chat_id=update.message.chat.id, text=responsestr, reply_markup=InlineKeyboardMarkup([keyboards]))

def fetch_alerts(id:str):
    alertslist = db.fetch_alerts(id)
    responsestr = ''
    i = 0
    keyboards = []
    responsejson = requests.get(TICKER_URL).json()
    for alert in alertslist:
        i = i + 1
        keyboards.append(InlineKeyboardButton(
            f"Delete '{i}'", callback_data=alert['key'] + ' ' + alert['token'] + '@' + alert['price']))
        responsestr = responsestr + str(i) + '. ' + alert['token'] + '@'+responsejson[alert['token']]['last']+\
                      (' greater than ' if alert['condition'] > 0 else ' less than ') + ' ' + alert['price'] + '\n'
    responsestr = responsestr if responsestr else 'No alerts'
    return responsestr,keyboards

def alert_callback(update:Update,context:CallbackContext):
    query = update.callback_query.data
    db.delete(query.split(' ')[0])
    print(update)
    responsestr, keyboards = fetch_alerts(update.callback_query.message.chat.id)
    update.callback_query.edit_message_text(text=responsestr,reply_markup=InlineKeyboardMarkup([keyboards]))


def fetchAndCreateAlert(update):
    text=update.message.text.lower().strip()
    token=text
    price=''
    if len(text.split('@'))==2:
        token,price=text.split('@')

    if len(token)<5:
        token=token+'inr'
    responsejson = requests.get(TICKER_URL).json()
    response=''
    if token in responsejson:
        response = responsejson[token]['last']
        if price:
            count=db.count(update.message.chat.id)
            if count<3:
                response_val=Decimal(response)
                price_val =Decimal(price)
                condition=1 if price_val>=response_val else -1
                db.insert({'user':update.message.chat.id,'token':token,'price':price,'condition':condition,'created':str(datetime.now())})
                response= 'Alert set: '+token+(' greater than or equal 'if condition>0 else ' less than or equal ')+price+'\ncurrent value: '+response
            else:
                response="Max 3 alerts. /alerts"

    response= response if response else HELP_TEXT
    bot.sendMessage(chat_id=update.message.chat.id, text=response)



def start(update):
    bot.sendMessage(chat_id=update.message.chat.id,text=HELP_TEXT)


@app.lib.cron()
def schedule_quote(event):
    if(event.type=='cron'):
        fetch_alerts_notify();
    return "ok"

def fetch_alerts_notify():
    responsejson = requests.get(TICKER_URL).json()
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

TICKER_URL='https://api.wazirx.com/api/v2/tickers'
HELP_TEXT="Usage: \n1.Message <token> to get its price\ne.g. wrxinr or btcinr\n\n"\
"2.To set alert <token>@<price>\ne.g. wrxinr@220\n\n3.Show alerts /alerts\n\n"\
"4.'inr' is default, so wrx or btc returns wrxinr or btcinr"

telegram_token=json.load(open('config.json','r'))['telegram_token']
bot = telegram.Bot(token=telegram_token)
dispatcher = Dispatcher(bot=bot,use_context=True,update_queue=Queue())
dispatcher.add_handler(CallbackQueryHandler(alert_callback))
