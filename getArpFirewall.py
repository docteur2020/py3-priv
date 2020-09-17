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


DIR_JSON_FW='/home/x112097/ARP/FW/'

def getLastDumpArpFW(directory=DIR_JSON_FW):
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
		


if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-s", "--save",action="store",help="Save ARP table to json dump",required=False)
	group1.add_argument("-l", "--load",action="store",help="Load ARP table to json dump",required=False)
	parser.add_argument("-m", "--mac",action="store",help="Get ARP entry for a mac",required=False)
	parser.add_argument("-p", "--printing",action="store_true",help="Affichage des ARP",required=False)
	args = parser.parse_args()
	
	arp_fw={}
	
	if args.save:
		url = 'https://hcs-tooling.gts.socgen/cmdb/api/v1/all-devices/?fields=name,arp&device-types=firewall '
		os.environ['NO_PROXY'] = 'hcs-tooling.gts.socgen'
		r = requests.get(url, verify=False, headers={'X-API-KEY': '887104b073d57bd2c19dddb1755a0ddd5e371666'}, stream=True, proxies={}) 
		arp_unicorns = json.loads(r.text)
		
		for arps in arp_unicorns:
			for arp in arps['arp']:
				arp_fw[arp['mac']]={'firewall':arps['name'],'ip':arp['ip']}
				
		
		save_json_arp(arp_fw,args.save)
		
		if args.mac:
			print(get_arp_entry(args.save,args.mac))
		
	if args.load:
		arp_fw=load_json_arp(args.load)
		
		if args.mac:
			print(get_arp_entry(args.load,args.mac))
		
	if args.printing:
		print(arp_fw)
		
		

		