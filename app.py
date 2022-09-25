from flask import Flask, render_template
import json
import os
import subprocess
import sys
import time
import logging

app = Flask(__name__)


lite_client = "./liteclient-build/lite-client/lite-client -C ./liteclient-build/global.config.json"
fift2 = "./liteclient-build/crypto/fift -I ./ton/crypto/fift/lib/ -i"
address = "0QB6AA4Mb_SNs_iIuq02c7ypC5VxyY4JWmEkQuKswcg46VxG"


def init_lite_client():
    p = subprocess.Popen(
        lite_client,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)

    l = p.stderr.readline()
    while l != "":
        logging.warning(l)
        if b'data bytes for block' in l:
            break
        if b'' == l:
            break
        l = p.stderr.readline()
    return p


def init_fift():
    p = subprocess.Popen(
        fift2,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)
    return p


def conver_addr(fift_proc, command):
    fift_proc.stdin.write(command)
    fift_proc.stdin.flush()
    l = fift_proc.stdout.readline()
    l = str(l, 'utf-8').lstrip("\"").rstrip("\" \n")
    # print(l)
    fift_proc.stdout.readline()
    return l


def run_last_method(proc):
    try:
        proc.stdin.write(b'last\n')
        proc.stdin.flush()

        for line in iter(lambda: proc.stderr.readline(), ''):
            if b'last masterchain block' in line:
                break
            if b'latest masterchain block known' in line:
                break
            if b'' == line:
                break

        for line in iter(lambda: proc.stdout.readline(), ''):
            if b'last masterchain block' in line:
                break
            if b'latest masterchain block known' in line:
                break
            if b'' == line:
                break
    except (BrokenPipeError, IOError):
        print('BrokenPipeError caught', file=sys.stderr)


def run_method(proc, command):
    # print("run_method: " + command.decode("utf-8"))

    l = ""
    try:
        proc.stdin.write(command)
        proc.stdin.flush()
        for l in iter(lambda: proc.stderr.readline(), ""):
            if b'starting VM to run method' in l:
                break
            if b'' == l:
                break
            if b'result:  [' in l:
                break

        for l in iter(lambda: proc.stdout.readline(), ""):
            if b'result:  [' in l:
                break
            if b'' == l:
                break
        l = str(l, 'utf-8')
        l = l.split(':')[1].strip()
    except (BrokenPipeError, IOError):
        print('BrokenPipeError caught', file=sys.stderr)
    return l


def get_balance(sub_proc):
    balance = run_method(sub_proc, bytes('runmethod ' + address + ' balance\n', 'utf-8'))
    balance = balance.lstrip("[ ").rstrip(" ]")
    if balance == "":
        return 0
    return round(int(balance) / 1000000000, 2)


def get_seqno(sub_proc):
    seqno = run_method(sub_proc, bytes('runmethod ' + address + ' get_seqno\n', 'utf-8'))
    seqno = seqno.lstrip("[ ").rstrip(" ]")
    if seqno == "":
        return 0
    return int(seqno)


def get_pubkey(sub_proc):
    pubkey = run_method(sub_proc, bytes('runmethod ' + address + ' get_pubkey\n', 'utf-8'))
    pubkey = pubkey.lstrip("[ ").rstrip(" ]")
    return pubkey


def get_order_seqno(sub_proc):
    order_seqno = run_method(sub_proc, bytes('runmethod ' + address + ' get_order_seqno\n', 'utf-8'))
    order_seqno = order_seqno.lstrip("[ ").rstrip(" ]")
    if order_seqno == "":
        return 0
    return int(order_seqno)


def get_number_of_wins(sub_proc):
    wins = run_method(sub_proc, bytes('runmethod ' + address + ' get_number_of_wins\n', 'utf-8'))
    wins = wins.lstrip("[ ").rstrip(" ]")
    if wins == "":
        return 0
    return int(wins)


def get_incoming_amount(sub_proc):
    r = run_method(sub_proc, bytes('runmethod ' + address + ' get_incoming_amount\n', 'utf-8'))
    r = r.lstrip("[ ").rstrip(" ]")
    if r == "":
        return 0
    return round(int(r) / 1000000000, 2)


def get_outgoing_amount(sub_proc):
    r = run_method(sub_proc, bytes('runmethod ' + address + ' get_outgoing_amount\n', 'utf-8'))
    r = r.lstrip("[ ").rstrip(" ]")
    if r == "":
        return 0
    return round(int(r) / 1000000000, 2)


def get_orders(sub_proc, fift_proc):
    r = run_method(sub_proc, bytes('runmethod ' + address + ' get_orders\n', 'utf-8'))
    r = r.lstrip("[ ([").rstrip("]) ]")
    if r == "":
        return []
    orders = r.split("] [")
    if not orders:
        return []
    orders_res = []
    for order in orders:
        order_arr = order.split(" ")
        addr = conver_addr(fift_proc, bytes(order_arr[4] + ' ' + order_arr[5] + ' 4 smca>$ .s drop\n', 'utf-8'))
        order_res = {'id': int(order_arr[0]), 'status': int(order_arr[1]), 'timestamp': int(order_arr[2]),
                     'amount': round(int(order_arr[3]) / 1000000000, 2),
                     'address': addr}
        orders_res.append(order_res)
    return orders_res


def get_state():

    proc = init_lite_client()

    fift = init_fift()

    run_last_method(proc)

    balance = get_balance(proc)

    recommended_amount = balance / 10
    response = {'address': address, 'balance': balance,
                'seqno': get_seqno(proc),
                'order_seqno': get_order_seqno(proc), 'number_of_wins': get_number_of_wins(proc),
                'incoming_amount': get_incoming_amount(proc), 'outgoing_amount': get_outgoing_amount(proc),
                'orders': get_orders(proc, fift),
                'recommended_amount': recommended_amount}
    proc.kill()
    fift.kill()
    return response


class State:
    last_check = int(time.time())
    json2 = get_state()


state = State()


@app.route("/")
def index():
    logging.warning('Started')

    # if int(time.time()) - state.last_check > 120:
    state.last_check = int(time.time())
    state.json2 = get_state()

    data = state.json2
    return render_template('index.html', data=data)


if __name__ == "__main__":
    app.run()
