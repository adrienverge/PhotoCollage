import requests
import json

from publish.LuluLineItem import LuluLineItem

client_id_sandbox = '0f945822-ca71-413b-b986-d0037c7e0b05'
client_secret_sandbox = '89cc568b-44dd-477a-a0f4-0e1bd30f7ce5'
sandbox_api_url = "https://api.sandbox.lulu.com/auth/realms/glasstree/protocol/openid-connect/token"
sandbox_base_url = "https://api.sandbox.lulu.com/"
print_job_url = sandbox_base_url + "print-jobs/"
job_details_url = sandbox_base_url + "print-jobs/%s/"
all_jobs_url = 'https://api.sandbox.lulu.com/print-jobs/statistics/'


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


def get_line_items(student_books: [LuluLineItem]) -> str:
    internal_line_items = ",".join([line_item.get_lulu_line_item() for line_item in student_books])

    return """ "line_items" : [""" + internal_line_items + "]"


def get_print_job_all(student_books: [LuluLineItem], external_id="RethinkYearbooks") -> str:
    data = """{ "external_id": "%s", 
                %s ,
                "shipping_option_level": "MAIL",
                "contact_email": "rethinkyearbooks@gmail.com",
                "shipping_address": %s
               }""" % (external_id, get_line_items(student_books), get_shipping_json())
    return data


def get_print_job_data(student_id: str, pod_package_id: str, interior_url: str, cover_url: str,
                       shipping_json: str) -> str:
    data = """{
               "external_id": "%s",
                "line_items": [
                    {
                        "title": "My Book",
                        "pod_package_id": "%s",
                        "quantity": 1,
                        "interior": {
                            "source_url": "%s"
                        },
                        "cover": {
                            "source_url": "%s"
                        }
                    }
                ],
                "shipping_option_level": "MAIL",
                "contact_email": "rethinkyearbooks@gmail.com",
                "shipping_address": %s
    }""" % (student_id, pod_package_id, interior_url, cover_url, shipping_json)

    return data


def get_interior_book_url(student_id: str):
    return "location_of_uploaded_pdf_url/%s" % student_id


def get_cover_url(student_id: str):
    return "location_of_uploaded_pdf_cover_url/%s" % student_id


def create_all_print_jobs(student_books: [LuluLineItem], external_id="RethinkYearbooks"):
    job_payload = get_print_job_all(student_books, external_id)
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer %s' % get_access_token_json(client_id_sandbox, client_secret_sandbox)['access_token'],
    }

    response = requests.request('POST', print_job_url, data=job_payload, headers=headers)
    return response


def create_print_job(student_id: str):
    # Get the product package id
    shipping_json = get_shipping_json()

    # Given the student, retrieve the book, and the cover details
    interior_url = get_interior_book_url(student_id)
    cover_url = get_cover_url(student_id)

    # first step is to get all the necessary data for the print job
    payload = get_print_job_data(student_id, __get_pod_package_id(), interior_url, cover_url, shipping_json)

    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer %s' % get_access_token_json(client_id_sandbox, client_secret_sandbox)['access_token'],
    }

    response = requests.request('POST', print_job_url, data=payload, headers=headers)
    return response


def create_print_job_json(student_id: str):
    response = create_print_job(student_id)
    return json.loads(response.text)


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

def get_all_jobs_details():
    import requests

    headers = {
        'Cache-Control': 'no-cache',
        'Authorization': 'Bearer %s' % get_access_token_json(client_id_sandbox, client_secret_sandbox)['access_token'],
    }

    response = requests.request('GET', all_jobs_url, headers=headers)

    print(response.text)
