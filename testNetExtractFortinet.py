#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals



import argparse
import yaml
from netaddr import IPNetwork
import sys
import pdb

def getListNetFromFile(filename):
	with open(filename,'r') as file_r:
		listNet=file_r.read().split()
		return listNet
		
def getDictNatFromFile(filename):
	with open(filename,'r') as file_r:
		listNat__=file_r.read().split()
		#pdb.set_trace()
		listNat={}
		for nat__ in listNat__:
			data=nat__.split(';')
			if len(data)==2:
				realNet=data[0]
				natNet=data[1]
				listNat[realNet]=natNet
			else:
				print("Verify file NAT format",file=sys.stderr)
				sys.exit(1)
				
			
		return listNat

class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)

Loader__.add_constructor('!include', Loader__.include)

def testNetinList(netStr,ListNetStr):
	result=False
	for netCur in ListNetStr:
		if IPNetwork(netStr) in IPNetwork(netCur):
			return True
	
	return result
	
def getNatEntry(netStr,dictNat):
	listNatNet=list(dictNat.keys())
	
	resultat=[]
	for natEntry in listNatNet:
		if IPNetwork(netStr) in IPNetwork(natEntry) or IPNetwork(natEntry) in IPNetwork(netStr):
			resultat.append({natEntry:dictNat[natEntry]})
			
	return resultat
	
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('-y','--yaml',help="yaml that contains object impacted",required=True)
	parser.add_argument('-f','--filenetwork',help="files contains network should be configured",required=True)
	parser.add_argument('-n','--natfile',help="files nat configured on legacy,csv format: net_real;net_nated;type",required=True)
	parser.add_argument('-t','--tag',help="tag representing the flow",required=True)
	parser.add_argument('-e','--exclude',action='append',default=[],help="ruleid to exclude",required=False)
	args = parser.parse_args()
	
	with open(args.yaml, 'r') as yml__:
		try:
			objs = yaml.load(yml__,Loader=yaml.SafeLoader)
		except yaml.constructor.ConstructorError as E:
			print(E)
			objs = yaml.load(yml__,Loader__)
			
	ListeTobeConfigured=getListNetFromFile(args.filenetwork)
	DictNat=getDictNatFromFile(args.natfile)
	ListNat=list(DictNat.keys())
	NetProcessed=[]
	
	for dstorsrc in objs:
		for ruleid in objs[dstorsrc]:
			if ruleid not in args.exclude:
				for obj in objs[dstorsrc][ruleid]:
					try:
						subnet_rule="/".join(objs[dstorsrc][ruleid ][obj]['subnet'].split())
					except KeyError as E:
						print(E)
						print(f'subnet not configured for obj {obj}')
					if not testNetinList(subnet_rule,ListeTobeConfigured):
						print(f"{subnet_rule} ruleid:{ruleid} is not present on future configuration {args.tag}")
					if testNetinList(subnet_rule,ListNat):
						if subnet_rule not in NetProcessed:
							natEntry=getNatEntry(subnet_rule,DictNat)
							print(f"{subnet_rule} is natted on legacy to {natEntry} ruleid{ruleid}")
							NetProcessed.append(subnet_rule)
	
	

	