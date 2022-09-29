# -*- coding: utf-8 -*-
"""Handle API requests to the DigiKey API

Code refactored from https://github.com/sparkmicro/Ki-nTree/blob/main/kintree/search/digikey_api.py"""

import json
import logging
import os

import digikey
import digikey.oauth.oauth2
from digikey.exceptions import DigikeyOauthException
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


logger = logging.getLogger(__name__)

SEARCH_HEADERS = [
    'product_description',
    'detailed_description',
    'digi_key_part_number',
    'manufacturer',
    'manufacturer_part_number',
    'product_url',
    'primary_datasheet',
    'primary_photo',
    'standard_pricing',
    'quantity_available'
]
PARAMETERS_MAP = [
    'parameters',
    'parameter',
    'value',
]

class HTTPServerHandler(BaseHTTPRequestHandler):
    """
    HTTP Server callbacks to handle Digikey OAuth redirects
    """
    def __init__(self, request, address, server, a_id, a_secret):
        self.app_id = a_id
        self.app_secret = a_secret
        self.auth_code = None
        super().__init__(request, address, server)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        get_params = parse_qs(urlparse(self.path).query)
        if 'code' in get_params:
            self.auth_code = get_params['code'][0]
            self.wfile.write(bytes('<html>' +
                                   '<body>'
                                   '<h1>You may now close this window.</h1>' +
                                   '<p>Auth code retreived: ' + self.auth_code + '</p>'
                                   '</body>'
                                   '</html>', 'utf-8'))
            self.server.auth_code = self.auth_code
            self.server.stop = 1
        else:
            raise DigikeyOauthException('Digikey did not return authorization token in request: {}'.format(self.path))

    # Disable logging from the HTTP Server
    def log_message(self, format, *args):
        return


if os.environ.get('DIGIKEY_STORAGE_PATH') is None:
    os.environ['DIGIKEY_STORAGE_PATH'] = str(Path(__file__).parent.parent.parent / 'storage')

# Check if storage path exists, else create it
if not os.path.exists(os.environ['DIGIKEY_STORAGE_PATH']):
    os.makedirs(os.environ['DIGIKEY_STORAGE_PATH'], exist_ok=True)


def disable_api_logger():
    # Digi-Key API logger
    logging.getLogger('digikey.v3.api').setLevel(logging.CRITICAL)
    # Disable DEBUG
    logging.disable(logging.DEBUG)


def check_environment() -> bool:
    DIGIKEY_CLIENT_ID = os.environ.get('DIGIKEY_CLIENT_ID', None)
    DIGIKEY_CLIENT_SECRET = os.environ.get('DIGIKEY_CLIENT_SECRET', None)

    if not DIGIKEY_CLIENT_ID or not DIGIKEY_CLIENT_SECRET:
        return False

    return True


def setup_environment(force=False) -> bool:
    file_exists = False

    if not check_environment() or force:
        # SETUP the Digikey authentication see https://developer.digikey.com/documentation/organization#production
        
        try:
            with open(os.environ['DIGIKEY_STORAGE_PATH'] + "/digikey_credentials.json", 'r') as f:
                credentials = json.load(f)
                file_exists

            os.environ['DIGIKEY_CLIENT_ID'] = credentials['client_id']
            os.environ['DIGIKEY_CLIENT_SECRET'] = credentials['client_secret']
        except Exception as e:
            print("It seems that your Digikey credentials are not stored correctly ({})".format(e))
            print("Would you like to provide them to me?")

            os.environ['DIGIKEY_CLIENT_ID'] = input("Digikey Client ID: ").strip()
            os.environ['DIGIKEY_CLIENT_SECRET'] = input("Digikey Client Secret: ").strip()
    
    if not file_exists:
         with open(os.environ['DIGIKEY_STORAGE_PATH'] + "/digikey_credentials.json", 'w') as f:
            json.dump({
                "client_id": os.environ.get('DIGIKEY_CLIENT_ID', None),
                "client_secret": os.environ.get('DIGIKEY_CLIENT_SECRET', None)
            }, f)
        
            logging.info("Storing Digi-key credentials into {}".format(f))

    return check_environment()


def get_default_search_keys():
    return [
        'product_description',
        'product_description',
        'revision',
        'keywords',
        'digi_key_part_number',
        'manufacturer',
        'manufacturer_part_number',
        'product_url',
        'primary_datasheet',
        'primary_photo',
    ]


def find_categories(part_details: str):
    ''' Find categories '''
    try:
        return part_details['limited_taxonomy'].get('value'), part_details['limited_taxonomy']['children'][0].get('value')
    except:
        return None, None

def fetch_access_token():
    # Check if a token already exists on the storage

    digikey.oauth.oauth2.open_new = lambda url: print("Open URL in your browser please... {}".format(url))
    token_handler =  digikey.oauth.oauth2.TokenHandler(version=3)
    token_handler.get_access_token()

def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''
    from wrapt_timeout_decorator import timeout

    part_info = {}
    if not setup_environment():
        return part_info

    @timeout(dec_timeout=20)
    def digikey_search_timeout():
        return digikey.product_details(part_number).to_dict()

    # Query part number
    try:
        part = digikey_search_timeout()
    except:
        part = None

    if not part:
        return part_info

    category, subcategory = find_categories(part)
    try:
        part_info['category'] = category
        part_info['subcategory'] = subcategory
    except:
        part_info['category'] = ''
        part_info['subcategory'] = ''

    headers = SEARCH_HEADERS

    for key in part:
        if key in headers:
            if key == 'manufacturer':
                part_info[key] = part['manufacturer']['value']
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    [parameter_key, name_key, value_key] = PARAMETERS_MAP

    for parameter in range(len(part[parameter_key])):
        parameter_name = part[parameter_key][parameter][name_key]
        parameter_value = part[parameter_key][parameter][value_key]
        # Append to parameters dictionary
        part_info['parameters'][parameter_name] = parameter_value

    return part_info

if __name__ == '__main__':
    # fetch_access_token()
    part = fetch_part_info('RMCF0402JT10K0')

    print("Printing example part...")
    json_str = json.dumps(part, indent=1, sort_keys=True)

    try:
        from pygments import highlight
        from pygments.lexers import JsonLexer
        from pygments.formatters import TerminalFormatter

        print(highlight(json_str, JsonLexer(), TerminalFormatter()))
    except ImportError:
        print(json_str)
