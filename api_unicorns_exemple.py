# -*- coding: utf-8 -*-
import re

import json
import urllib3
import requests
urllib3.disable_warnings()
import pdb
import csv
import os

url = 'https://hcs-tooling.gts.socgen/cmdb/api/v1/all-devices/'
os.environ['NO_PROXY'] = 'hcs-tooling.gts.socgen'
r = requests.get(url, verify=False, headers={'X-API-KEY': '887104b073d57bd2c19dddb1755a0ddd5e371666'}, stream=True, )
devices_unicorns = json.loads(r.text)
for device in devices_unicorns:
	print(device)