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


    def get_rack_id(self, rack_name):
        url = f'{self.api_url}/dcim/racks/?name={rack_name}'
        response = requests.get(url, verify=False, headers=self.headers)


        if response.status_code == 200:
            print(response.json())
            rack_id = response.json()['results'][0]['id']
            
            return rack_id
        else:
            print(f"Failed to fetch rack id. Status code: {response.status_code}")
            return None

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
                rack_rear = response.text
                return rack_rear
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

    def get_rendered_config(self, device_id):
        url = f'https://192.168.56.10/dcim/devices/{device_id}/render-config/?export=True'
        response = requests.get(url, verify=False,  headers=self.headers)

        if response.status_code == 200:
            config = response.content
            return config
        else:
            print(f"Failed to fetch config. Status code: {response.status_code}")
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
    parser.add_argument('--rack_name')
    args = parser.parse_args()



    # Instance for CRUD
    crud = CRUD(api_url, api_token)

    # Fetch devices by rack ID
    if args.rack_name:
        rack_id = crud.get_rack_id(args.rack_name)
    else:
        rack_id = args.rack_id

    
    rack_name = crud.get_rack_name(rack_id)
    rack_front = crud.get_rack_front(rack_id)
    rack_rear = crud.get_rack_rear(rack_id)
    rack_devices = crud.get_devices_by_rack_id(rack_id)


    for device in rack_devices:
        if device['config_template']:
            rendered_config = crud.get_rendered_config(device['id'])
            print(rendered_config)


    device_interfaces_front_ports_list = []
    interfaces_list = []
    front_ports_list = []


    for device in rack_devices:
        if device['name'] is not None:
            interfaces_list = []
            front_ports_list = []
            for interface in crud.get_interfaces_by_device_id(device['id']):
                interfaces_cables_link_peers = {
                    "interface_name": interface['name']
                }
                if interface.get('cable') is not None and interface['cable'].get('label') is not None:
                    interfaces_cables_link_peers['interface_cable'] = interface['cable']['label']
                    interfaces_cables_link_peers['interface_link_peer'] = str(interface['link_peers'][0]['name'])
                    interfaces_cables_link_peers['interface_link_peer_device'] = str(interface['link_peers'][0]['device']['name'])
                interfaces_list.append(interfaces_cables_link_peers)

            for front_port in crud.get_front_ports_by_device_id(device['id']):
                front_ports_cables_link_peers = {
                    "front_port_name": front_port['name']
                }
                if front_port.get('cable') is not None and front_port['cable'].get('label') is not None:
                    front_ports_cables_link_peers['front_port_cable'] = front_port['cable']['label']
                    front_ports_cables_link_peers['front_port_link_peer'] = front_port['link_peers'][0]['name']
                    front_ports_cables_link_peers['front_port_link_peer_device'] = front_port['link_peers'][0]['device']['name']
                front_ports_list.append(front_ports_cables_link_peers)

            device_interface_front_port = {
                "device_name": device['name'],
                "device_id": device['id'],
                "interface": interfaces_list,
                "front_port": front_ports_list
            }
            device_interfaces_front_ports_list.append(device_interface_front_port)

    env = Environment(loader=FileSystemLoader('src'))
    index_template = env.get_template('index.html')
    output_from_parsed_template = index_template.render(rack_name=rack_name,
                                                        rack_front=rack_front,
                                                        rack_rear=rack_rear,
                                                        device_interfaces_front_ports_list=device_interfaces_front_ports_list)
    with open(f"outputs/{rack_name}_doku.html", "w") as chap_page:
        chap_page.write(output_from_parsed_template)

    # Convert doku.html to doku.pdf
    path = os.path.abspath(f'outputs/{rack_name}_doku.html')
    converter.convert(f'file:///{path}', f'outputs/{rack_name}_doku.pdf')

if __name__ == "__main__":
    main()
