import argparse
import json
import jsoneditor
import logging
import re
import random
import string
import requests
from dataclasses import dataclass
from fake_useragent import UserAgent
from pprint import pprint

ua = UserAgent()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(message)s'
)

phone_pattern_legacy = re.compile(r'\{formatted_phone:(.*)}')
phone_pattern = re.compile(r'\{phone:([^}]*)}')


@dataclass
class Phone:
    country_code: str
    phone: str

    def __str__(self):
        return self.country_code + self.phone


@dataclass
class FakeData:
    first_name: str
    last_name: str
    password: str
    email: str
    username: str


def generate_fake_data():
    first_name = random.choice(["Мария", "Анна", "Екатерина", "Светлана", "Ирина", "Ольга"])
    last_name = random.choice(["Иванова", "Петрова", "Смирнова", "Кузнецова", "Соколова", "Попова"])
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(['mail.ru', 'yandex.ru', 'gmail.com'])}"
    username = first_name.lower() + str(random.randint(100, 999))
    return FakeData(first_name, last_name, password, email, username)


fake_data = generate_fake_data()

logging.debug("Fake data: %s", fake_data)


def format_phone(phone, mask):
    formatted_phone = []
    phone_index = 0
    for symbol in mask:
        if phone_index < len(phone):
            if symbol == '*':
                formatted_phone.append(phone[phone_index])
                phone_index += 1
            else:
                formatted_phone.append(symbol)
    return ''.join(formatted_phone)


def format_by_pattern(input_string, phone):
    new_string = input_string

    match_legacy = phone_pattern_legacy.search(input_string)
    if match_legacy:
        new_string = new_string.replace(
            match_legacy.group(),
            format_phone(str(phone), match_legacy.group(1))
        )

    match = phone_pattern.search(input_string)
    if match:
        new_string = new_string.replace(
            match.group(),
            format_phone(phone.phone, match.group(1))
        )

    replacements = {
        "full_phone": str(phone),
        "phone": phone.phone,
        "first_name": fake_data.first_name,
        "last_name": fake_data.last_name,
        "password": fake_data.password,
        "email": fake_data.email,
        "username": fake_data.username
    }

    for key, value in replacements.items():
        new_string = new_string.replace("{" + key + "}", str(value))

    return new_string


def process_request(request, phone):
    url = format_by_pattern(request["url"], phone)
    logging.info("URL: %s", url)

    params = {
        "method": request["method"],
        "url": url,
        "headers": {"User-Agent": ua.random}
    }

    logging.info("Method: %s", request["method"].upper())

    if "headers" in request:
        for k, v in request["headers"].items():
            formatted_key = format_by_pattern(k, phone)
            formatted_value = format_by_pattern(v, phone)
            params["headers"][formatted_key] = formatted_value

        logging.info("Headers: %s", params["headers"])

    if "json" in request:
        json_body = format_by_pattern(json.dumps(request["json"]), phone)

        try:
            json.loads(json_body)
        except Exception as e:
            logging.warning("INVALID JSON BODY: %s, Error: %s", json_body, str(e))

        logging.debug("JSON Body: %s", json_body)

        params["json"] = json_body

    if "data" in request:
        formdata = {
            format_by_pattern(k, phone): format_by_pattern(v, phone)
            for k, v in request["data"].items()
        }

        logging.debug("Form data Body: %s", formdata)

        params["data"] = formdata

    logging.debug("Sending request with params: %s", params)

    try:
        response = requests.request(**params)
        try:
            pprint(response.json())
        except json.JSONDecodeError:
            print(response.text)
    except requests.RequestException as e:
        logging.error("Request failed: %s", str(e))


def process_service(service, phone):
    if "requests" in service:
        for index, request in enumerate(service["requests"]):
            logging.info("Request #%s", index)
            process_request(request, phone)
    else:
        process_request(service, phone)


def process_services(services, phone):
    if isinstance(services, list):
        for index, service in enumerate(services):
            logging.info("Service #%s", index)
            process_service(service, phone)
    elif isinstance(services, dict):
        process_service(services, phone)


def on_result(result, filename, phone):
    print(json.dumps(result))

    with open(filename, "w", encoding="UTF-8") as file:
        file.write(json.dumps(result))

    process_services(result, phone)


parser = argparse.ArgumentParser(description='Process JSON file with requests.')
parser.add_argument('--file', type=str, help='Path to the JSON file', default='service.json')
parser.add_argument('--country-code', type=str, help='Country code (default: 7)', default='7')
parser.add_argument('--phone', type=str, help='Phone number')
parser.add_argument('-e', '--edit', action='store_true', help='Run editor')

args = parser.parse_args()

country_code = args.country_code.strip() if args.country_code.strip() else "7"

phone_number = args.phone.strip() if args.phone else input("Enter phone number: ")

phone = Phone(country_code, phone_number)

with open(args.file, "r", encoding="UTF-8") as file:
    base = json.loads(file.read())

if args.edit:
    jsoneditor.editjson(base, callback=lambda result: on_result(result, args.file, phone))
else:
    process_services(base, phone)