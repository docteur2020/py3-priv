#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
import re

import json
import urllib3
import requests
urllib3.disable_warnings()
import pdb
import csv
import os
import argparse
import glob
from time import  strftime , localtime , ctime
import sys
from pprint import pprint as ppr
import pdb

DIR_ARP_ALL='/home/x112097/ARP/ALL/'

def getLastDumpArp(directory=DIR_ARP_ALL):
	return max(glob.glob(directory+'/*.json'),key=os.path.getctime)

def cisco_to_mac(mac_cisco):

	resultat=mac_cisco

	if re.search("\.",mac_cisco):
		try:
			resultat=mac_cisco[0:2].upper()+":"+mac_cisco[2:4].upper()+":"+mac_cisco[5:7].upper()+":"+mac_cisco[7:9].upper()+":"+mac_cisco[10:12].upper()+":"+mac_cisco[12:14].upper()
		except IndexError:
			pdb.set_trace()
	else:
		resultat=mac_cisco
		
	return resultat
	
def load_json_arp(filename):
	dict_arp={}
	with open(filename, 'r') as fp:
		dict_arp=json.load(fp)
		
	return dict_arp

def save_json_arp(dict_arp,filename):
	with open(filename, 'w') as fp:
		json.dump(dict_arp, fp)

def get_arp_entry(dump_json_arp,mac):
	resultat=None
	dict_arp_cur=load_json_arp(dump_json_arp)
	
	try:
		resultat=dict_arp_cur[cisco_to_mac(mac)]
	except KeyError:
		pass
		
	return resultat
		
def getArpFromUnicorn(filedump=()):
	arp_all={}
	if not filedump:
		timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		suffixe=timestamp+'.json'
		filedump=DIR_ARP_ALL+suffixe
	url = 'https://hcs-tooling.gts.socgen/cmdb/api/v1/all-devices/?fields=name,arp&device-types=all '
	os.environ['NO_PROXY'] = 'hcs-tooling.gts.socgen'
	r = requests.get(url, verify=False, headers={'X-API-KEY': '887104b073d57bd2c19dddb1755a0ddd5e371666'}, stream=True, proxies={}) 
	arp_unicorns = json.loads(r.text)
	
	for arps in arp_unicorns:
		for arp in arps['arp']:
			if arp['mac'] in arp_all:
				arp_all[arp['mac']].append({'hostname':arps['name'],'ip':arp['ip']})
			else:
				arp_all[arp['mac']]=[{'hostname':arps['name'],'ip':arp['ip']}]
			
	
	save_json_arp(arp_all,filedump)
	
	return arp_all


if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("--cache",action="store_true",help=u"Use cache",required=False)
	group1.add_argument("--update",action="store_true",help=u"update data from unicorn",required=False)
	args = parser.parse_args()
	
	arps__=None
	if args.cache:
		try:
			lastDump=getLastDumpArp()
			arps__=load_json_arp(lastDump)
			ppr(arps__)
		except ValueError as E:
			print(E)
			print('launch script with option --update',file=sys.stderr)
		
	if args.update:
		arps__=getArpFromUnicorn()
		ppr(arps__,width=300)
