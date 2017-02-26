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
    print(data)
    if data['type'] == 'in_raid':
        messages.append('{} 正被攻擊'.format(data['name']))


@app.route('/')
def hello():
    return 'Hello World'


@app.route('/message', methods=['POST'])
def message():
    data = request.form
    handle_message(data)
    return 'ok'


@handler.add(MessageEvent, message=TextMessage)
def handle_message_event(event):
    print(event)
    text = event.message.text
    if text == '目前狀態':
        if len(messages) == 0:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='沒有任何事件發生'))
        for message in messages:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message))
        messages.clear()


@handler.add(JoinEvent)
def handle_join(event):
    print('join', event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='超神掛掛進場'))


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
