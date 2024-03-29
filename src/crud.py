import requests
import argparse
from jinja2 import Template, Environment, FileSystemLoader
import os
from pyhtml2pdf import converter


class CRUD:
    def __init__(self, api_url, api_token):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            "Authorization": self.api_token
        }


    def get_rack_name(self, rack_id):
        url = f'{self.api_url}/dcim/racks/{rack_id}'
        response = requests.get(url, verify=False, headers=self.headers)

        if response.status_code == 200:
            rack_name = response.json()['name']
            return rack_name
        else:
            print(f"Failed to fetch rack name. Status code: {response.status_code}")
            return None


    def get_rack_front(self, rack_id):
        url = f'{self.api_url}/dcim/racks/{rack_id}/elevation/?face=front&render=svg'
        response = requests.get(url, verify=False, headers=self.headers)
        if response.status_code == 200:
                rack_front = response.text
                return rack_front
        else:
            print(f"Failed to fetch front rack. Status code: {response.status_code}")
            return None

    def get_rack_rear(self, rack_id):
        url = f'{self.api_url}/dcim/racks/{rack_id}/elevation/?face=rear&render=svg'
        response = requests.get(url, verify=False, headers=self.headers)
        if response.status_code == 200:
                rear = response.text
                return rear
        else:
            print(f"Failed to fetch rear rack. Status code: {response.status_code}")
            return None
        
    
    def get_devices_by_rack_id(self, rack_id):
        url = f'{self.api_url}/dcim/devices/?rack_id={rack_id}'
        response = requests.get(url, verify=False,  headers=self.headers)

        if response.status_code == 200:
            devices = response.json()['results']
            return devices
        else:
            print(f"Failed to fetch devices. Status code: {response.status_code}")
            return None

    def get_interfaces_by_device_id(self, device_id):
        url = f'{self.api_url}/dcim/interfaces/?device_id={device_id}'
        response = requests.get(url, verify=False,  headers=self.headers)

        if response.status_code == 200:
            interfaces = response.json()['results']
            return interfaces
        else:
            print(f"Failed to fetch interfaces. Status code: {response.status_code}")
            return None
    
    def get_front_ports_by_device_id(self, device_id):
        url = f'{self.api_url}/dcim/front-ports/?device_id={device_id}'
        response = requests.get(url, verify=False,  headers=self.headers)

        if response.status_code == 200:
            front_ports = response.json()['results']
            return front_ports
        else:
            print(f"Failed to fetch front ports. Status code: {response.status_code}")
            return None

def main():
    # NetBox API URL and token
    api_url = 'https://192.168.56.10/api'
    api_token = 'Token 1e679ca95470caf70398a42dd8300453eac1ec8b'

    # Rack ID to search for devices
    parser = argparse.ArgumentParser(
                    prog='Netbox Rack-Doku',
                    description='Generates Device Doku of specific Rack')
    parser.add_argument('--rack_id')
    args = parser.parse_args()

    # Instance for CRUD
    crud = CRUD(api_url, api_token)

    devices_interfaces_list = []
    interfaces_list = []
    front_port_list = []

    # Fetch devices by rack ID
    rack_name = crud.get_rack_name(args.rack_id)
    rack_front = crud.get_rack_front(args.rack_id)
    rack_rear = crud.get_rack_rear(args.rack_id)
    rack_devices = crud.get_devices_by_rack_id(args.rack_id)
    
    #device_front_ports = crud.get_front_ports_by_device_id(args.rack_id)


    """i = 0
    for d in rack_devices:
        if d['name'] is not None:
            device_name = d['name']
            for interface in crud.get_interfaces_by_device_id(d['id']):
                interfaces_list .append(interface['name'])
            device_interfaces_list.append(device_name)
            device_interfaces_list.append(str(d['id']))
            device_interfaces_list.append(interfaces_list)
            interfaces_list = []
            devices_interfaces_list.append(device_interfaces_list)
            device_interfaces_list = []
            i += 1"""

    for d in rack_devices:
        if d['name'] is not None:
            device_name = d['name']
            interfaces_list = []
            front_port_list = []
            for interface in crud.get_interfaces_by_device_id(d['id']):
                interfaces_list.append(interface['name'])
            for front_port in crud.get_front_ports_by_device_id(d['id']):
                front_port_list.append(front_port['name'])

            device_interfaces = {
                "deviceName": device_name,
                "deviceID": d['id'],
                "interfaceNames": interfaces_list,
                "frontportNames": front_port_list
            }
            devices_interfaces_list.append(device_interfaces)

    #device_interface_cable_list = [d['cable']['label'] for d in device_interfaces]
    #device_interface_link_peers_list = [d['link_peers']['name'] for d in device_interfaces]

    env = Environment(loader=FileSystemLoader('src'))
    index_template = env.get_template('index.html')
    output_from_parsed_template = index_template.render(rack_name=rack_name,
                                                        rack_front=rack_front,
                                                        rack_rear=rack_rear,
                                                        devices_interfaces_list=devices_interfaces_list)
    with open("outputs/output.html", "w") as chap_page:
        chap_page.write(output_from_parsed_template)

    # Convert output.html to output.pdf
    path = os.path.abspath('outputs/output.html')
    converter.convert(f'file:///{path}', 'outputs/output.pdf')

if __name__ == "__main__":
    main()
