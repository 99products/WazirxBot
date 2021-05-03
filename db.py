from deta import Deta
import json

deta_key=json.load(open('config.json','r'))['deta_key']
db=Deta(deta_key)
alerts = db.Base('alerts')
def fetch_alerts(user:str):
    return list(alerts.fetch({"user": user}))[0]

def count(user:str):
    return len(fetch_alerts(user))

def fetch_all_alerts():
    return list(alerts.fetch())[0]

def insert(alert):
    alerts.put(alert)

def delete(key:str):
    alerts.delete(key)

