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


@app.route('/')
def hello():
    return 'Hello World'

@app.route('/message', methods=['POST'])
def in_raid():
    pass


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


@handler.add(JoinEvent)
def handle_join(event):
    print('join', event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
