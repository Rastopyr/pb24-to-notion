import datetime
import calendar
import hashlib
import json


import requests
import xmltodict

from notion.client import NotionClient
from notion.collection import NotionDate

PB_DATE_FORMAT = "%d.%m.%Y"

with open("config.json") as config_file:
    config = json.load(config_file)

to_string = lambda obj: str(obj).encode('utf-8')

currency_cache = {}

def currency_by_date(date, amount):
    [value, currency] = amount.split(" ")

    cache_key = currency if currency == "UAH" else '{}_{}'.format(currency, date)

    if cache_key in currency_cache:
        return float(value) * currency_cache[cache_key]

    request = requests.get('https://api.privatbank.ua/p24api/exchange_rates?json&date={}'.format(date))
    response = request.json()

    if "error" in response:
        raise Exception(response["error"]) 

    currency_list = response["exchangeRate"]

    currency_course = next((cur for cur in currency_list if "currency" in cur and cur["currency"] == currency))

    if not currency_course:
        return float(value);

    currency_cache[cache_key] = currency_course["purchaseRateNB"]

    return float(value) * currency_course["purchaseRateNB"]

def pb24_to_op_list(pb24_list):
    op_list = []

    list_of_charges = filter(lambda op: op["@cardamount"][0] == "-", pb24_list)

    for value in list_of_charges:
        op_date = datetime.datetime.strptime('{} {}'.format(value["@trandate"], value["@trantime"]), '%Y-%m-%d %H:%M:%S')

        normalized_amount = currency_by_date(
            op_date.strftime('%d.%m.%Y'),
            value["@amount"]
        )

        print(normalized_amount)

        op_list.append({
            "id": value['@appcode'],
            "amount": normalized_amount,
            "terminal": value['@terminal'],
            "desc": value['@description'],
            "date": op_date
        })

    return op_list

def query_pb24(pb24_config):
    now = datetime.datetime.now()

    start_date = now.replace(day = calendar.monthrange(now.year, now.month)[0]).strftime(PB_DATE_FORMAT)
    end_date = now.replace(day = calendar.monthrange(now.year, now.month)[1]).strftime(PB_DATE_FORMAT)

    data = f'''<oper>cmt</oper>
    <wait>0</wait>
    <test>0</test>
    <payment id="">
        <prop name="sd" value="{start_date}" />
        <prop name="ed" value="{end_date}" />
        <prop name="card" value="{pb24_config["card"]}" />
    </payment>'''

    signRaw = to_string(data + pb24_config["merchantPassword"])

    signature = hashlib.sha1(to_string(hashlib.md5(signRaw).hexdigest())).hexdigest()

    requestBody = f'''<?xml version="1.0" encoding="UTF-8"?>
    <request version="1.0">
        <merchant>
            <id>{pb24_config["merchantID"]}</id>
            <signature>{signature}</signature>
        </merchant>
        <data>
            {data}
        </data>
    </request>
    '''

    request = requests.post(
        'https://api.privatbank.ua/p24api/rest_fiz',
        data = requestBody,
        headers = {
            'Content-Type': 'application/xml'
        }
    )

    request.raw.decode_content = True

    parsed_response = xmltodict.parse(request.content)

    if "error" in parsed_response:
        raise Exception(parsed_response["error"]) 

    return parsed_response['response']['data']['info']['statements']['statement']

def write_ops_to_notion(notion_config, op_list):
    nclient = NotionClient(token_v2=notion_config["token"])
    cv = nclient.get_collection_view(notion_config["collectionURL"])

    rows = cv.collection.get_rows()

    ops_to_add = list(
        filter(
            lambda op: not any([row for row in rows if row.op_id == op["id"]]),
            op_list
        )
    )

    for op_to_add in ops_to_add:
        row = cv.collection.add_row()

        row.description = op_to_add["desc"]
        row.date = NotionDate(op_to_add["date"])
        row.amount = op_to_add["amount"]
        row.terminal = op_to_add["terminal"]
        row.op_id = op_to_add["id"]

    print('Added {} operations'.format(len(ops_to_add)))



op_list = pb24_to_op_list(query_pb24(config["pb24"]))

op_list.reverse()

write_ops_to_notion(
    config["notion"],
    op_list
)
