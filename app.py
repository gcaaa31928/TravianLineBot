import json
import os
import re
import urllib
import requests
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
from tinydb.storages import MemoryStorage

app = Flask(__name__)
access_token = os.environ.get('ACCESS_TOKEN',
                              'Q+VCL2yaFLwzV8wFK19H7glBB/kj1fHm7G8Apxv2HZv8GTSlg9V8c38/VQvSMvQtcG+38nv2OlAZVrT7ZmSm+1HT1pWbE29a0ROZ27y0mchjOdeZ2hnW0HwA/wtIDNrbKNezIbc43wAo1dtOTsiMPgdB04t89/1O/w1cDnyilFU=')
secret = os.environ.get('SECRET', '64d7bbe9e32d897d48e35a323e6f0642')

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)
messages = []
message_index = 0
db = TinyDB(storage=MemoryStorage)
message_table = db.table('message_table')
report_table = db.table('report_table')


def parseJson(string):
    string = re.sub(r"(,?)(\w+?)\s+?:", r"\1'\2' :", string)
    string = string.replace("'", "\"")
    return json.loads(string)


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
    # reportStr = str(data['report'])
    # reportStr = re.sub(r"(,?)(\w+?)\s+?:", r"\1'\2' :", reportStr)
    # reportStr = reportStr.replace("'", "\"")
    report = str(data['report'])
    name = str(data['key'])
    if report_table.contains(Query().name == name):
        report_table.update({'report': report, 'name': name}, Query().name == name)
    else:
        report_table.insert({'report': report, 'name': name})
    print(get_report_image('GCA', 1))


def get_all_reports():
    all_messages = ''
    # print((report_table.all()))
    if len(report_table.all()) == 0:
        return '沒有任何事件發生'
    for data in report_table.all():
        all_messages += '{}.\n'.format(data['name'])
        reports = parseJson(data['report'])
        for report in reports:
            all_messages += '{}'.format(report['info'])
    return all_messages


def get_report(name):
    reports = report_table.get(Query().name == name)['report']
    all_messages = ''
    reports = parseJson(reports)
    for report in reports:
        all_messages += '{}'.format(report['info'])
    return all_messages


def get_image_from_url(url):
    r = requests.post('https://web-capture.net/zh_TW/initiate_conversion.php', files={
        'link': url,
        'output': 'jpeg',
    })
    return r.status_code


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
    url = report_url(report['content'])
    return url


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
    elif '報告' in text:
        matches = re.search('(.*)報告(\d+)', text)
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


@handler.add(JoinEvent)
def handle_join(event):
    print('join', event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='超神掛掛進場'))


if __name__ == "__main__":
    # clear_messages()
    app.run(host='127.0.0.1', port=5000)
