import json

import requests

from publish.OrderDetails import OrderDetails

client_id_sandbox = '0f945822-ca71-413b-b986-d0037c7e0b05'
client_secret_sandbox = '89cc568b-44dd-477a-a0f4-0e1bd30f7ce5'
sandbox_api_url = "https://api.sandbox.lulu.com/auth/realms/glasstree/protocol/openid-connect/token"
sandbox_base_url = "https://api.sandbox.lulu.com/"
print_job_url = sandbox_base_url + "print-jobs/"
job_details_url = sandbox_base_url + "print-jobs/%s/"
all_jobs_url = 'https://api.sandbox.lulu.com/print-jobs/statistics/'

LULU_MONTICELLO_POD_ID = "0827X1169FCPRELW060UW444MNG"


def get_api_key(filename):
    """ Given a filename,
        return the contents of that file
    """
    try:
        with open(filename, 'r') as f:
            # It's assumed our file contains a single line,
            # with our API key
            return f.read().strip()
    except FileNotFoundError:
        print("'%s' file not found" % filename)


def get_access_token_json(client_id: str, client_secret: str) -> str:
    data = {'grant_type': 'client_credentials'}
    access_token_response = requests.post(sandbox_api_url, data=data, allow_redirects=False,
                                          auth=(client_id, client_secret))
    return access_token_response.json()


def __get_pod_package_id() -> str:
    """
    0827X1169: A4 Medium
    FC: full color
    STD: standard quality/ PRE: Premium Quality
    LW: linen wrap binding
    080CW444: 80# uncoated white paper with a bulk of 444 ppi
    M: matte cover coating
    N: navy colored linen
    G: golden foil stamping
    :return: Gives a predefined set LULU POD package id
    """
    return "0827X1169FCPRELW060UW444MNG"


def get_shipping_json() -> str:
    return """{
        "name": "Mudita Singhal",
        "organization":"Rethink Yearbooks",
        "street1": "1042 Waterbird Way",
        "city": "Santa Clara",
        "state_code": "CA",
        "country_code": "US",
        "postcode": "95051",
        "phone_number": "408-438-6825",
        "email" : "rethinkyearbooks@gmail.com",
        "is_business":true
    }"""


def get_line_items(student_books: [OrderDetails]) -> str:
    internal_line_items = ",".join([line_item.get_lulu_line_item() for line_item in student_books])
    return """ "line_items" : [""" + internal_line_items + "]"


def create_order_payload(student_books: [OrderDetails], external_id="RethinkYearbooks") -> str:
    data = """{ "external_id": "%s", 
                %s ,
                "shipping_option_level": "MAIL",
                "contact_email": "rethinkyearbooks@gmail.com",
                "shipping_address": %s
               }""" % (external_id, get_line_items(student_books), get_shipping_json())
    return data


def get_header() -> str:
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer %s' % get_access_token_json(client_id_sandbox, client_secret_sandbox)[
            'access_token'],
    }
    return headers


def submit_full_order(student_books: [OrderDetails], external_id="RethinkYearbooks"):
    job_payload = create_order_payload(student_books, external_id)
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer %s' % get_access_token_json(client_id_sandbox, client_secret_sandbox)['access_token'],
    }

    response = requests.request('POST', print_job_url, data=job_payload, headers=headers)
    return response


def get_job_details(lulu_job_id: str):
    url = job_details_url % lulu_job_id
    print(url)
    headers = {
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer %s' % get_access_token_json(client_id_sandbox, client_secret_sandbox)['access_token'],
    }

    response = requests.request('GET', url, headers=headers)

    print(response.text)
    return response.text
