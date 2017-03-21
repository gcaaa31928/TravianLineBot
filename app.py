import json
import os
import re
import urllib
import requests
from flask import Flask, request, abort
from flask_cors import CORS

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import JoinEvent
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from linebot.models import SourceGroup
from linebot.models import SourceUser
from tinydb import Query
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

app = Flask(__name__)
CORS(app)

access_token = os.environ.get('ACCESS_TOKEN', 'Q+VCL2yaFLwzV8wFK19H7glBB/kj1fHm7G8Apxv2HZv8GTSlg9V8c38/VQvSMvQtcG+38nv2OlAZVrT7ZmSm+1HT1pWbE29a0ROZ27y0mchjOdeZ2hnW0HwA/wtIDNrbKNezIbc43wAo1dtOTsiMPgdB04t89/1O/w1cDnyilFU=')
secret = os.environ.get('SECRET', '63d41afb19023f069426487e8bc56ecc')

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)
messages = []
message_index = 0
db = TinyDB(storage=MemoryStorage)
message_table = db.table('message_table')
report_table = db.table('report_table')
alliance_report_table = db.table('alliance_report_table')
token_table = db.table('token')
be_raid_table = db.table('be_raid')
send = db.table('send')
travian_url = 'http://ts4.travian.ru/'

current_report = {}
current_report_read = False


def parseJson(string):
    string = re.sub(r"(,?)(\w+?)\s+?:", r"\1'\2' :", string)
    string = string.replace("'", "\"")
    return json.loads(string)

def get_sender():
    senders = []
    for sender in send.all():
        senders.append(sender['id'])
    return senders


@app.route("/callback", methods=['POST'])
def callback():
    print(access_token, secret)
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


def handle_report(data):
    report = str(data['report'])
    name = str(data['key'])
    if report_table.contains(Query().name == name):
        report_table.update({'report': report, 'name': name}, Query().name == name)
    else:
        report_table.insert({'report': report, 'name': name})


def get_all_reports():
    all_messages = ''
    # print((report_table.all()))
    if len(report_table.all()) == 0:
        return '沒有任何事件發生'
    for data in report_table.all():
        all_messages += '{}.\n'.format(data['name'])
        reports = parseJson(data['report'])
        for index, report in enumerate(reports):
            all_messages += '{}. {}'.format(index + 1, report['info'])
    return all_messages


def get_report(name):
    reports = report_table.get(Query().name == name)['report']
    all_messages = ''
    reports = parseJson(reports)
    for index, report in enumerate(reports):
        all_messages += '{}. {}'.format(index + 1, report['info'])
    return all_messages


def report_url(content):
    params = urllib.parse.urlencode({
        'report': content,
        'step1': '保存记录',
        'design': 1
    })
    params = params.encode('utf-8')
    req = urllib.request.Request('http://travian-reports.net/hk/convert', params)
    response = urllib.request.urlopen(req)
    return response.geturl()


def get_report_url(name, index):
    index -= 1
    reports = report_table.get(Query().name == name)['report']
    report = parseJson(reports)[index]
    # url = report_url(report['content'])
    return travian_url + report['url']


def handle_message(data):
    msg = str(data['message'])
    name = str(data['key'])
    if message_table.contains(Query().name == name):
        message_table.update({'message': msg, 'name': name}, Query().name == name)
    else:
        message_table.insert({'message': msg, 'name': name})


def get_all_messages():
    all_messages = ''
    if len(message_table.all()) == 0:
        return '沒有任何事件發生'
    for index, data in enumerate(message_table.all()):
        all_messages += '{}\n'.format(data['message'])
    return all_messages


def get_message(name):
    return message_table.get(Query().name == name)['message']


def handle_alliance_report(data):
    reports = str(data['report'])
    reports = parseJson(reports)
    if len(reports) <= 0:
        return
    report = reports[0]
    if not alliance_report_table.contains(Query().id == report['id']):
        alliance_report_table.insert({'id': report['id']})
        for sender in get_sender():
            line_bot_api.push_message(sender, TextSendMessage(text=report['content']))


def handle_token(data):
    token = data['token']
    if len(token_table.all()) > 0:
        token_table.purge()
    print(token_table)
    token.insert({'token': token})

def has_alliance_report():
    if len(alliance_report_table.search(Query().read == False)) > 0:
        return True
    return False


def get_all_alliance_report():
    all_message = "花生戰報來囉:\n"
    report = alliance_report_table.get(Query().read == False)
    alliance_report_table.update({'read': True}, Query().id == report['id'])
    all_message += report['content']

    # for index, report in enumerate(alliance_report_table.search(Query().read == False)):
    #      all_message += '{}. '.format(index+1) + report['url'] + '\n'
    # alliance_report_table.update({'read': True}, Query().read == False)
    # print(alliance_report_table.all())
    return all_message


def handle_be_raid(data):
    village_name = str(data['village_name'])
    village_id = str(data['village_id'])
    in_time = str(data['in_time'])
    if not be_raid_table.contains(Query().id == village_id):
        be_raid_table.insert({'id': village_id})
        for sender in get_sender():
            line_bot_api.push_message(sender, TextSendMessage(text="{} 被攻擊了!! 在{}後抵達".format(village_name, in_time)))

# def has_alliance_report():
#     if len(alliance_report_table.search(Query().read == False)) > 0:
#         return True
#     return False
#
#
# def get_all_alliance_report():
#     all_message = "花生戰報來囉:\n"
#     report = alliance_report_table.get(Query().read == False)
#     alliance_report_table.update({'read': True}, Query().id == report['id'])
#     all_message += report['content']
#
#     # for index, report in enumerate(alliance_report_table.search(Query().read == False)):
#     #      all_message += '{}. '.format(index+1) + report['url'] + '\n'
#     # alliance_report_table.update({'read': True}, Query().read == False)
#     # print(alliance_report_table.all())
#     return all_message

@app.route('/')
def hello():
    return 'Hello World'


@app.route('/message', methods=['POST'])
def message():
    data = request.get_json()
    handle_message(data)
    return 'ok'


@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()
    handle_report(data)
    return 'ok'


@app.route('/alliance_report', methods=['POST'])
def alliance_report():
    data = request.get_json()
    handle_alliance_report(data)
    return 'ok'


@app.route('/token', methods=['POST'])
def get_token():
    data = request.get_json()
    handle_token(data)
    return 'ok'

@app.route('/be_raid', methods=['POST'])
def be_raid():
    data = request.get_json()
    handle_be_raid(data)
    return 'ok'

def set_send_id(id):
    if not send.contains(Query().id == id):
        send.insert({'id': id})
        print(send.all())


@handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event):
    print(event)
    text = event.message.text
    source = event.source
    id = ''
    if isinstance(source, SourceUser):
        id = source.user_id
    elif isinstance(source, SourceGroup):
        id = source.group_id
    set_send_id(id)
    if '狀態' in text:
        text = text.replace('狀態', '')
        if text == '':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_all_messages()))
        else:
            name = text
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_message(name)))
    elif '報告' in text:
        matches = re.search('(.*)報告(\d*)', text)
        if matches.group(1) == '' and matches.group(2) == '':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_all_reports()))
        elif matches.group(2) == '':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_report(matches.group(1))))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_report_url(matches.group(1), int(matches.group(2)))))
    elif '敬禮' in text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='敬禮'))
    elif '安安' in text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='安'))
    elif '0.0' in text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='0.0'))



@handler.add(JoinEvent)
def handle_join(event):
    print('join', event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='超神掛掛進場'))


if __name__ == "__main__":
    # clear_messages()
    app.run(host='127.0.0.1', port=5000)
