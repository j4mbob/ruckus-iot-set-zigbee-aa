#!/usr/bin/env python3

try:
	import requests
	import argparse
	import certifi
	import sys
	import json
	import http.client as http_client
    # ignore self signed cert errors:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

except ImportError as e:
	print('error importing modules: ' + str(e))
	exit(1)

class Ruckus_IoT():

	def parse_args(self):
		parser = argparse.ArgumentParser(description="Ruckus IoT Controller",conflict_handler='resolve')
		parser.add_argument("username", action="store", help="username of iot controller")
		parser.add_argument("password", action="store", help="password for iot controller")
		parser.add_argument("host", action="store", help="iot controller host")
		parseargs = vars(parser.parse_args(None if sys.argv[1:] else ['-h']))
		
		return parseargs['username'],parseargs['password'],parseargs['host']
		
	def logon(self,username,password,hostname):

		self.hostname = hostname

		try: 
			self.session = requests.Session()
			self.request = self.session.get('https://'+ self.hostname + '/v1/oauth/login', verify=False,auth=(username, password))
			output = self.request.json()
			self.session_token = output['access_token']
			self.request.raise_for_status()
		except requests.exceptions.RequestException as e:
			print(e)
			exit()
		else:

			return self.session,self.session_token,self.request

	def get_gateway_details(self):
		headers = {'Authorization': 'token {}'.format(self.session_token)}
		gateway_output = self.session.get('https://' + self.hostname + '/app/v1/gateway', headers=headers).json()

		self.gateway_devices = {}

		for i in gateway_output['data']:
			self.gateway_devices[i['ip_network_info']['ip']] = {}
		
			self.gateway_devices[i['ip_network_info']['ip']]['gateway_euid'] = i['gateway_euid']
			self.gateway_devices[i['ip_network_info']['ip']]['network_mac1'] = i['diagnostics_info'][0]['network_mac']
			self.gateway_devices[i['ip_network_info']['ip']]['network_mac2'] = i['diagnostics_info'][1]['network_mac']


	def modify_gateway_radio(self,network_mac,gateway_euid):
		headers = {'Authorization': 'token {}'.format(self.session_token)}
		body = {
   				 "iot_mode": "zigbee_aa",
    			"network_mac": network_mac
				}
	
		gateway_output = self.session.put('https://' + self.hostname + '/app/v1/gateway/' + gateway_euid + '/management/IOT_MODE',json=body, headers=headers)

		if gateway_output.ok:
			print('modified ' + gateway_euid + ': ' + str(gateway_output))
		else:
			print('error in API when modifying ' + gateway_euid + ': ' + str(gateway_output.json()))


	def set_gateways(self):
		for ap_ip in self.gateway_devices:
			self.modify_gateway_radio(self.gateway_devices[ap_ip]['network_mac1'],self.gateway_devices[ap_ip]['gateway_euid'])


if __name__ == "__main__":

	r = Ruckus_IoT()
	username,password,host = r.parse_args()
	r.logon(username,password,host)
	r.get_gateway_details()
	r.set_gateways()
