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


def handle_message(data):
    msg = str(data['message'])
    name = str(data['key'])
    db = TinyDB('db.json')
    if db.contains(Query().name == name):
        db.update({'message': msg, 'name': name}, Query().name == name)
    else:
        db.insert({'message': msg, 'name': name})


def get_all_messages():
    all_messages = ''
    db = TinyDB('db.json')
    if len(db.all()) == 0:
        return '沒有任何事件發生'
    for index, data in enumerate(db.all()):
        all_messages += '{}. {}\n'.format(index, data['message'])
    return all_messages


def clear_messages():
    db = TinyDB('db.json')
    db.remove(Query().message.all)


@app.route('/')
def hello():
    return 'Hello World'


@app.route('/message', methods=['POST'])
def message():
    data = request.get_json()
    print(data)
    handle_message(data)
    return 'ok'


@handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event):
    print(event)
    text = event.message.text
    if '狀態' in text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=get_all_messages()))


@handler.add(JoinEvent)
def handle_join(event):
    print('join', event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='超神掛掛進場'))


if __name__ == "__main__":
    # clear_messages()
    app.run(host='127.0.0.1', port=5000)
