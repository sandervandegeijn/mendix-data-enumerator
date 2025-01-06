import requests
import json
from termcolor import colored
import random
import os
import argparse

class MendixClient:

    current_user = 'Anonymous'
    local_cache = None
    # Login as a local or anonymous user

    def __init__(self, base_url:str, proxy:str=None, users:dict=None):
        self.create_session(base_url, proxy)
        self.users = users
        self.downloaded_files = []

        # Check if the base_url is a valid Mendix URL
        MendixClient.check_base_url(base_url)
        self.base_url = base_url

    def check_base_url(base_url:str):
        # Check if the base_url is a valid Mendix URL
        if not base_url.startswith('http'):
            raise ValueError('Base URL should start with http')
        if base_url.endswith('/'):
            raise ValueError('Base URL should not end with /')

    def create_session(self, base_url:str, proxy:str=None):
        self.session = requests.Session()
        self.session.verify = False

        # Set user id to default Firefox user id
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.session.cookies.update({'__Host-DeviceType':'Desktop', '__Host-Profile':'Responsive'})
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}
            # Disable verification if a proxy is used
            self.session.verify = False
            # Disable TLS warnings if verification is disabled
        requests.urllib3.disable_warnings(
        requests.urllib3.exceptions.InsecureRequestWarning)


    def login(self, username=None, password=None):
        """
        Login as a local or anonymous user
        """

        # Clear previous login info
        self.session.headers.update({'X-Csrf-Token': None})
        self.session.cookies.update({'__Host-XASself.sessionID':None})
        url = f'{self.base_url}/xas/'
        if username == None:
            print("Anonymous login")
        else:
            # Login
            print(f"{username} login")
            data = {
                "action": "login",
                "params": {
                    "username": username,
                    "password": password
                }
            }
            result = self.session.post(url, json=data)
            if not result.status_code == 200:
                raise RuntimeError("Could not login")
            self.session.headers.update({'X-Csrf-Token': result.json().get('csrftoken')})

        # Fill the Mendix local cache and get CSRF-token
        data = {"action":"get_session_data","params":{}}
        result = self.session.post(url, json=data)
        if not result.status_code == 200:
            raise RuntimeError("Could not acquire CSRF")
        else:
            self.session.headers.update({'X-Csrf-Token': result.json().get('csrftoken')})
            self.current_user = result.json()['user']['attributes']['Name']['value']
        self.local_cache = result.json()
        #print(json.dumps(self.local_cache))
    
    def set_headers(self, headers):
        self.session.headers.update(headers)
        data = {"action":"get_session_data","params":{}}
        url = f'{self.base_url}/xas/'
        result = self.session.post(url, json=data)
        self.current_user = result.json()['user']['attributes']['Name']['value']
        self.local_cache = result.json()

    def get_objects_by_xpath(self, class_type, limit=10):
        """
        Get objects by xpath
        """
        url = f'{self.base_url}/xas/'
        data ={
            "action": "retrieve_by_xpath",
            "params":
            {
                "xpath": f'//{class_type}',
                "schema":
                {
                    "amount": limit
                }
            }
        }
        result = self.session.post(url, json=data)
        return result.json().get('objects', {})

    def get_object_by_id(self, guid):
        """
        Get an object by its guid/id
        """

        url = f'{self.base_url}/xas/'
        data ={
            "action": "retrieve_by_ids",
            "params":
            {
                "ids": [guid],
                "schema":{}
            }
        }

        result = self.session.post(url, json=data)
        return result.json().get('objects', {})

    def get_classes(self):
        """
        Get all the available classes/types from the metadata of the flow,
        sorted alphabetically by objectType.
        """
        classes = sorted(
            (item.get('objectType') for item in self.local_cache.get('metadata', []))
        )
        return classes


    def update_attribute(self, guid, name, value):
        url = f'{self.base_url}/xas/'
        data = {"action":"commit","params":{"guids":[guid]},"changes":{guid:{name:{"value":value}}}}
        result = self.session.post(url, json=data)
        return result.json().get('objects', {})

    def pretty_print_objects(self, objects):
        """
        Pretty print objects
        """

        output = ''
        for object in objects:
            if output != '':
                output += '\n'
            output += f'[{object["objectType"]}] @ {object["guid"]}'
            attributes = object.get('attributes', {})
            for attribute in attributes.items():
                output += '\n\t'
                if attribute[1].get('readonly', False):
                    output += colored(attribute[0], 'green')
                else:
                    output += colored(attribute[0], 'red')
                    output += ' (MODIFIABLE)'
                output += f": {str(attribute[1].get('value', ''))[:128]}"
        return output
    
    def find_micro_flows(self):
        operation_ids = [item for x, y in self.local_cache.get('microflows').items() for item in y.split(',')]
        for operation_id in operation_ids:
            url = f'{self.base_url}/xas/'
            data = {"action":"runtimeOperation","operationId":operation_id,"params":{},"validationGuids":[],"changes":{},"objects":[],"profiledata":{}}
            result = self.session.post(url, json=data)
            if result.status_code == 200:
                description = result.json().get('description', None)
                if description:
                    print(description)
                else:
                    print(self.pretty_print_objects(result.json().get('objects', [])))
    
    def monitor_files(self, destination_path):
        try:
            while True:
                objects = self.get_objects_by_xpath('System.FileDocument')
                for obj in objects:
                    if obj['guid'] not in self.downloaded_files:
                        self.downloaded_files.append(obj['guid'])
                        self.downloadfile(obj['guid'],obj['attributes']['Name']['value'], destination_path)
        except KeyboardInterrupt:
            print('Stopping monitoring')

    def downloadfile(self, guid, name, destination_path):
        url = f'{self.base_url}/file'
        params = {
            'guid': guid
        }
        result = self.session.get(url, params=params)
        if not result.status_code == 200:
            print(f"Could not download file {guid}")
        else:
            destination_path = f'{destination_path}/{guid}_{name}'
            with open(destination_path, 'wb') as f:
                f.write(result.content)
            print(f"Downloaded [{guid}]: {name}' to {destination_path}")
    
    def show_source_ip(self) -> str:
        return requests.get('https://icanhazip.com/', proxies=self.session.proxies).text

def print_help():
    print("Commands:")
    print("  help - print this menu")
    print("  //class_name [limit] - Retrieve 10 objects of class_name type")
    print("  id - Retrieve 1 object by its guid/id")
    print("  ? - Retrieve 1 object for each class type")
    print("  list - Retrieve all object class types")
    print("  update guid attribute value - Update an attribute of an object")
    print("  @guid - Check object for all users")
    print("  login [username] - Login as different (or anonymous) user")
    print("  flows - Find microflows")
    print("  show_source_ip - Show source IP")
    print("  monitor_files - Monitor files")
    print("")
    print("Lines in green are read-only attributes, red are modifiable")
    print("")

def main(base_url, proxy=None, users=None, headers=None):
    mc = MendixClient(base_url, proxy)
    # Start by logging as anonymous
    if not headers:
        mc.login()
    else:
        mc.set_headers(headers)

    print_help()

    print(f"Welcome to the Mendix client for {base_url}")
    print(f"You are using source IP: {mc.show_source_ip()}")
    print()
    # Read instructions until CTRL+C
    while True:
        try:
            if mc.local_cache.get('user', None) is not None:
                print("You are logged in as", mc.local_cache['user']['attributes']['Name']['value'])
                print(f"Your GUID: {mc.local_cache['user']['guid']}")

            # Read the instruction from the prompt
            instruction = input(colored(f'[Mendix {mc.current_user}@{base_url}]: ', 'blue'))

            # Retrieve 10 objects of class type input starts with //
            if instruction.startswith('//'):
                # If the input contains a space and a digit, acquire that many objects
                splits = instruction.split(' ')
                if len(splits) > 1 and splits[1].isdigit():
                    results = mc.get_objects_by_xpath(splits[0][2:], splits[1])
                else:
                    results = mc.get_objects_by_xpath(instruction[2:])
                print(mc.pretty_print_objects(results))

            # Retrieve 1 object by its guid/id, if input is a number
            elif instruction.isdigit():
                results = mc.get_object_by_id(instruction)
                print(mc.pretty_print_objects(results))

            # Retrieve 1 object for each class type if input is ?
            elif instruction == "?":
                for my_class in mc.get_classes():
                    results = mc.get_objects_by_xpath(my_class, 1)
                    if len(results) != 0:
                        print(mc.pretty_print_objects(results))

            # Retrieve all object class types if input is list
            elif instruction == "list":
                for my_class in mc.get_classes():
                    print(f'//{my_class}')

            elif instruction == "show_source_ip":
                print(mc.show_source_ip())
            
            elif instruction == "monitor_files":
                # destination path is the current directory + downloads
                destination_path = os.path.join(os.getcwd(), 'downloads')
                mc.monitor_files(destination_path)
            
            elif instruction == "flows":
                mc.find_micro_flows()

            # Login as different (or anonymous) user, if input is 'login username' (or 'login')
            elif instruction.startswith('login'):
                splits = instruction.split(' ')
                if len(splits) > 1:
                    username = splits[1]
                    mc.login(username, users[username])
                else:
                    mc.login()

            # Update an attribute of an object using: 'update <guid> <attribute name> <value>'
            elif instruction.startswith('update'):
                splits = instruction.split(' ')
                if len(splits) >= 4 and splits[1].isdigit():
                    guid = splits[1]
                    name = splits[2]
                    value = ' '.join(splits[3:])
                    result = mc.update_attribute(guid, name, value)
                    print(mc.pretty_print_objects(result))

            # Check object for all users: @<guid>
            elif instruction.startswith('@'):
                if instruction[1:].isdigit():
                    guid = instruction[1:]
                    current_user = mc.current_user
                    for username in users.keys():
                        mc.login(username, users[username])
                        results = mc.get_object_by_id(guid)
                        print(mc.pretty_print_objects(results))
                    mc.login(current_user, users[current_user])
            elif instruction == "help":
                print_help()

        except KeyboardInterrupt:
            print('kthxbye')
            break

# Main program
if __name__ == '__main__':
    #users = {'admin':'admin'}

    # You can create headers from your chrome based browser by going to the network tab and copying the headers section of a request
    # Then run it trough chrome-headers-to-python.py
    # crt.sh is cool for recon, it'll try to find all subdomains of a domain and then check if Mendix is used.
    
    # headers = {
    #     "accept": "application/json",
    # }

    parser = argparse.ArgumentParser(description="Scripting to modify and maintain Opensearch")
    parser.add_argument('--domain', help="The domain to connect to")
    parser.add_argument('--proxy', help='The proxy to use', default=None)
    args = parser.parse_args()

    domain = args.domain
    proxy = args.proxy

    if not domain:
        domain = input("Enter the domain to connect to: ")

    if not domain.startswith('http'):
        domain = 'https://' + domain
    if domain.endswith('/'):
        domain = domain[:-1]

    main(domain, proxy, None, None)
