import json
import urllib3
import requests
import pdb

urllib3.disable_warnings()
url = 'https://hcs-tooling.gts.socgen/cmdb/api/v1/all-devices/?fields=name,interface,vip&device-types=firewall&statutes=active'
r = requests.get(url=url, verify=False, stream=True )
pdb.set_trace()
d = json.loads(r.text)   



for device in d:
	device_name = device.get('name')
	print(device_name)
	for interface in device.get('interface'):
		print(interface)
	for vip in device.get('vip'):
		print(vip)
