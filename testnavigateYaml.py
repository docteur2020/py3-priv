#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import pdb
import yaml
from ruamel.yaml import YAML
import ruamel.yaml
import sys
import csv


from pprint import pprint
from copy import deepcopy
import os

def test_vlan_notdeployed(vlan,epgs):
	resultat=True
	for epg in epgs:
		if vlan== epg[3]:
			resultat=False
			break
		
			
	return resultat
	
def writeCsv(list_result,fichier_csv):
	with open(fichier_csv,'w+') as csvfile:
		csvwriter=csv.writer(csvfile,delimiter=';',quotechar='"',quoting=csv.QUOTE_ALL)
		for entry in list_result:
			csvwriter.writerow(entry)
	
	return None

	
class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)

Loader__.add_constructor('!include', Loader__.include)


if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file_yml')
	args = parser.parse_args()
	
	print("load yaml:")
	with open(args.file_yml, 'r') as yml__:
		try:
			yaml_obj = yaml.load(yml__,Loader=yaml.SafeLoader)
		except yaml.constructor.ConstructorError as E:
			print(E)
			yaml_obj = yaml.load(yml__,Loader__)
			

	pprint(yaml_obj)

	
	with open('/home/x112097/TMP/Liste-vlanTIG-DC5.TXT') as vlandc5:
		legvlan=vlandc5.read().split()
		
	vlan_not_deploy=[]
	
	vlanEPG={ entry[3]: entry for entry in yaml_obj}
	
	for vlan in legvlan:
		if  test_vlan_notdeployed(vlan,yaml_obj):
			vlan_not_deploy.append(vlan)
			
	csv_result=[]
	for vlan in legvlan:
		if vlan in vlan_not_deploy:
			print(vlan+';TOBECONFIGURED;')
			csv_result.append([vlan,'TOBECONFIGURED','no',None])
		else:
			print(vlan+';ALREADYCONFIGURED;'+str(vlanEPG[vlan]))
			csv_result.append([vlan,'ALREADYCONFIGURED','yes',vlanEPG[vlan]])
			
	
	writeCsv(csv_result,'RESULT/VLAN_DC5.csv')
	pdb.set_trace()
	pprint(yaml_obj)	
