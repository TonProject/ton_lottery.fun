from flask import Flask, render_template
import json
import os
import subprocess
import sys
import time
import logging
import requests

app = Flask(__name__)

address = "0QB6AA4Mb_SNs_iIuq02c7ypC5VxyY4JWmEkQuKswcg46VxG"
api_key = "9e65765482dadd6cdf5924c842c698c33855875ad05c84fd77fdb0420e8be537"

headers = {'X-API-Key': api_key}
baseUrl = "https://toncenter.com/api/v2/"


def make_request(method):
    data = {'method': method, 'address': address, 'stack': []}
    r = requests.post(baseUrl + "runGetMethod", json=data, headers=headers)
    json_object = json.loads(r.text)
    return json_object


def get_balance():
    result = make_request('balance')
    if result['ok']:
        return round(int(result['result']['stack'][0][1], 16) / 1000000000, 2)
    return 0


def get_seqno():
    result = make_request('get_seqno')
    if result['ok']:
        return int(result['result']['stack'][0][1], 16)
    return 0


def get_order_seqno():
    result = make_request('get_order_seqno')
    if result['ok']:
        return int(result['result']['stack'][0][1], 16)
    return 0


def get_number_of_wins():
    result = make_request('get_number_of_wins')
    if result['ok']:
        return int(result['result']['stack'][0][1], 16)
    return 0


def get_incoming_amount():
    result = make_request('get_incoming_amount')
    if result['ok']:
        return round(int(result['result']['stack'][0][1], 16) / 1000000000, 2)
    return 0


def get_outgoing_amount():
    result = make_request('get_outgoing_amount')
    if result['ok']:
        return round(int(result['result']['stack'][0][1], 16) / 1000000000, 2)
    return 0


def get_orders():
    orders_res = []
    result = requests.get(baseUrl + "getTransactions?address=" + address + "&limit=10",
                          headers=headers)
    json_object = json.loads(result.text)
    if json_object['ok']:
        orders = json_object['result']
        for order in orders:
            # Игнорируем трензакцию, если это:
            # 1) вывод средств "по запросу"
            # 2) "мелкий" перевод
            if order['in_msg']['source'] != "" and int(order['in_msg']['value']) >= 500000000:
                if len(order['out_msgs']) > 0 and int(order['out_msgs'][0]['value']) == 2 * int(
                        order['in_msg']['value']):
                    status = 'win'
                    value = round(int(order['out_msgs'][0]['value']) / 1000000000, 2)
                else:
                    value = round(int(order['in_msg']['value']) / 1000000000, 2)
                    status = 'lose'

                order_result = {'id': order['transaction_id']['hash'], 'status': status, 'timestamp': order['utime'],
                                'amount': value,
                                'address': order['in_msg']['source']}
                print(order_result)
                orders_res.append(order_result)
    else:
        return orders_res
    return orders_res


def get_state():
    balance = get_balance()
    recommended_amount = balance / 10
    response = {'address': address, 'balance': balance,
                'seqno': get_seqno(),
                'order_seqno': get_order_seqno(), 'number_of_wins': get_number_of_wins(),
                'incoming_amount': get_incoming_amount(), 'outgoing_amount': get_outgoing_amount(),
                'orders': get_orders(),
                'recommended_amount': recommended_amount}
    return response


class State:
    last_check = int(time.time())
    json2 = get_state()


state = State()


@app.route("/")
def index():
    logging.warning('Started')

    if int(time.time()) - state.last_check > 20:
        state.last_check = int(time.time())
        state.json2 = get_state()

    data = state.json2
    return render_template('index.html', data=data)


if __name__ == "__main__":
    app.run()
