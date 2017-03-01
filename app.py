import os

from flask import Flask, request, abort

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
from tinydb import Query
from tinydb import TinyDB

app = Flask(__name__)
access_token = os.environ.get('ACCESS_TOKEN', None)
secret = os.environ.get('SECRET', None)

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)
messages = []
message_index = 0
db = TinyDB('db.json')
message_table = db.table('message')
report_table = db.table('report')


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
    if len(report_table.all()) == 0:
        return '沒有任何事件發生'
    for index, data in enumerate(report_table.all()):
        all_messages += '{}. {}\n'.format(index, data['report'])
    return all_messages


def get_report(name):
    return report_table.get(Query().key == name)['report']


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
        all_messages += '{}. {}\n'.format(index, data['message'])
    return all_messages


def get_message(name):
    return message_table.get(Query().key == name)['message']


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event):
    print(event)
    text = event.message.text
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


@handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event):
    print(event)
    text = event.message.text
    if '狀態' in text:
        text = text.replace('狀態', '')
        if text == '':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_all_reports()))
        else:
            name = text
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=get_report(name)))


@handler.add(JoinEvent)
def handle_join(event):
    print('join', event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='超神掛掛進場'))


if __name__ == "__main__":
    # clear_messages()
    app.run(host='127.0.0.1', port=5000)
