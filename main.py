
from queue import Queue
from decimal import Decimal
import telegram
from telegram import InlineKeyboardButton,InlineKeyboardMarkup,Update
import requests
from telegram.ext import Dispatcher, CallbackQueryHandler, CallbackContext
from flask import Flask,request
import db
import json
import sys


app = Flask(__name__)

@app.route('/', methods=["GET"])
def hello_world():
    return "Working.."


@app.route('/', methods=["POST"])
def process():
    request_data = request.get_json()
    # try:
    update = telegram.Update.de_json(request_data, bot)
    dispatcher.process_update(update)
    if update.message:
        chat_id = update.message.chat.id
        text=update.message.text.lower()
        response='Invalid'
        keyboards=[]
        if(text=='/alerts' or text=='alerts'):
            show_alerts(update)
        elif (text=='/start' or text=='start' or text=='/help' or text=='help'):
            start(update)
        else:
            fetchAndCreateAlert(update)
    # except:
    #     print(sys.exc_info()[0])
    #     return 'error'
    return 'ok'

def alert_callback(update:Update,context:CallbackContext):
    query = update.callback_query.data
    db.delete(query.split(' ')[0])
    print(update)
    responsestr, keyboards = fetch_alerts(update.callback_query.message.chat.id)
    update.callback_query.edit_message_text(text=responsestr,reply_markup=InlineKeyboardMarkup([keyboards]))




def show_alerts(update):
    responsestr,keyboards=fetch_alerts(update.message.chat.id)
    bot.sendMessage(chat_id=update.message.chat.id, text=responsestr, reply_markup=InlineKeyboardMarkup([keyboards]))

def fetch_alerts(id:str):
    alertslist = db.fetch_alerts(id)
    responsestr = ''
    i = 0
    keyboards = []
    for alert in alertslist:
        i = i + 1
        keyboards.append(InlineKeyboardButton(
            f"Delete '{i}'", callback_data=alert['key'] + ' ' + alert['token'] + '@' + alert['price']))
        responsestr = responsestr + str(i) + '. ' + alert['token'] + \
                      (' greater than ' if alert['condition'] > 0 else ' less than ') + ' ' + alert['price'] + '\n'
    responsestr = responsestr if responsestr else 'No alerts'
    return responsestr,keyboards
def fetchAndCreateAlert(update):
    text=update.message.text.lower().strip()
    token=text
    price=''
    if len(text.split('@'))==2:
        token,price=text.split('@')

    responsejson = requests.get('https://api.wazirx.com/api/v2/tickers').json()
    response=''
    if token in responsejson:
        response = responsejson[token]['last']
        if price:
            count=db.count(update.message.chat.id)
            if(count<3):
                response_val=Decimal(response)
                price_val =Decimal(price)
                condition=1 if price_val>=response_val else -1
                db.insert({'user':update.message.chat.id,'token':token,'price':price,'condition':condition})
                response= 'Alert set: '+token+(' greater than or equal 'if condition>0 else ' less than or equal ')+price+'\ncurrent value: '+response
            else:
                response="Max 3 alerts. /alerts"

    response= response if response else HELP_TEXT
    bot.sendMessage(chat_id=update.message.chat.id, text=response)


def start(update):
    bot.sendMessage(chat_id=update.message.chat.id,text=HELP_TEXT)

HELP_TEXT='Usage: \n1.Message <token> to get its price\ne.g. wrxinr or btcinr\n\n2.To set alert <token>@<price>\ne.g. wrxinr@220\n\n3.Show alerts /alerts'

telegram_token=json.load(open('config.json','r'))['telegram_token']
bot = telegram.Bot(token=telegram_token)
dispatcher = Dispatcher(bot=bot,use_context=True,update_queue=Queue())
dispatcher.add_handler(CallbackQueryHandler(alert_callback))





