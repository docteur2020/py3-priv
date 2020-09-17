#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import argparse
from pprint import pprint as ppr
import pdb
import re
import sys
import os
import logging
import pyparsing as pp
from time import gmtime, strftime , localtime
from netaddr import IPNetwork
import yaml
from pathlib import Path
from io import StringIO

from prefixFilter import *
from xlsxDictWriter import xlsMatrix

supportedMode=['address','hostname','list']
supportedAction=['pass','drop']

DIR_RESULT='/home/x112097/RESULT/RM/'

class RouteMapError(Exception):
	"Classe Exception pour grep-ip"
	
	def __init__(self,code,*args):
		self.message={}
		
		self.message[0]=f'Mode not supported:{args[0]}'
		self.message[1]=f'action not supported:{args[0]}'
		self.message[2]=f'mode hostname: prefix-list not present:{args[0]}'
		self.message[3]=f'Route-map: action not supported:{args[0]}'
		super(RouteMapError, self).__init__(self.message[code])

class routeMapEntry(object):
	def __init__(self,mode="",action="",**kargs):
		
		if mode:
			if mode not in supportedMode:
				print(f'Supported mode:{" ".join(supportedMode)}',file=sys.stderr)
				raise RouteMapError(0,mode)
			
		if action not in supportedAction:
			print(f'Supported action:{" ".join(supportedAction)}',file=sys.stderr)
			raise RouteMapError(1,action)
			
		self.mode=mode
		self.action=action
		self.verbose=False
		
		if 'verbose' in kargs:
			self.verbose=True
		
		
		if mode=='address':
			prefixFile=kargs['file']
			name=Path(prefixFile).stem
			self.prefixset=prefixSet(name,prefixFile=prefixFile,verbose=self.verbose)
			
		if mode=='hostname':
			hostname=kargs['hostname']
			prefixset_name=kargs['prefix-set']
			prefixsetsObj=prefixSets(hostname,mode='yaml',verbose=self.verbose)
			if prefixset_name not in prefixsetsObj:
				raise RouteMapError(2,prefixset_name)
			self.prefixset=prefixsetsObj[prefixset_name]
			
		if mode=='list':
			listPrefixSet=kargs['prefix-set-list']
			prefixset_name=kargs['prefix-set']
			prefixsetEntries=[]
			for prefixsetStr in listPrefixSet:
				dataCur=ParsePrefixSetEntry(prefixsetStr)
				prefixCurStr=list(dataCur.keys())[0]
				filterPrefixCur=dataCur[prefixCurStr]
				prefixsetEntries.append(prefixSetEntry(prefixCurStr,filterPrefix=filterPrefixCur))
				
			self.prefixset=prefixSet(prefixset_name,PrefixSetList=prefixsetEntries,verbose=self.verbose)
			
		if not mode:
			data=kargs.get('data')
			if not data:
				self.mode='empty'
		
	def __str__(self):
		resultat=StringIO()

		resultat.write(f'action:{self.action}\n')
		resultat.write(self.prefixset.__str__())
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
	
	def match(self,prefixStr):
	
		if self.mode=='empty':
			return True
		return prefixStr in self.prefixset
		
		
			

class routeMap(object):
	def __init__(self,yaml_file):
		with open(yaml_file) as file:
			data=yaml.load(file,Loader=yaml.SafeLoader)
		
		self.entries={}
		
		for indice in data:
			modeCur=data[indice].get('mode')
			if modeCur:
				self.entries[indice]=routeMapEntry(data[indice]['mode'],data[indice]['action'],**data[indice]['data'])
			else:
				self.entries[indice]=routeMapEntry("",data[indice]['action'])
			
	def match(self,prefixStr):
		result=False
		
		for indice in self.entries:
			match_cur=self.entries[indice].match(prefixStr)
			if match_cur:
				if self.entries[indice].action=='pass':
					result=True
					break
				elif self.entries[indice].action=='drop':
					result=False
					break
				else:
					raise RouteMapError(3,mode)
			
		return result
		
	def matchList(self,prefixStrList):
		passNetList=[]
		dropNetList=[]
		for prefixStr in prefixStrList:
			if self.match(prefixStr):
				if prefixStr not in passNetList:
					passNetList.append(prefixStr)
			else:
				if prefixStr not in dropNetList:
					dropNetList.append(prefixStr)
					
		return {'pass': passNetList, 'drop':dropNetList}
		
	def __str__(self):
	
		resultat=StringIO()
		for indice in sorted(list(self.entries.keys()),key=int):
			resultat.write('\n=====\n')
			resultat.write(f'indice:{indice}\n')
			resultat.write(self.entries[indice].__str__())
			resultat.write('\n=====\n')
			resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
	
	
		
	def filterPrefixList(self,PrefixListStr):
		resultat=[]
		for prefixStr in PrefixListStr:
			if self.match(prefixStr): 
				resultat.append(prefixStr)
				
		return resultat

def getListNetFromFile(filename):
	with open(filename,'r') as file_r:
		listNet=file_r.read().split()
		return listNet
		
def saveListNetToFile(listNet,filename):
	with open(filename,'w') as file_w:
		file_w.write('\n'.join(listNet))

def ddiff(oldPrefixList,newPrefixList):
	prefixAbsent=[]
	prefixNew=[]
	
	for prefix in oldPrefixList:
		if prefix not in newPrefixList:
			prefixAbsent.append(prefix)
			
	for prefix in newPrefixList:
		if prefix not in oldPrefixList:
			prefixNew.append(prefix)		
			
	return {'new route': prefixNew ,'absent route':prefixAbsent}
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=False)
	parser.add_argument("--yaml", action="store",help="yaml containing route-map",required=True)
	group.add_argument("--prefix", action="store",help="prefix")
	group.add_argument("--file", action="store",help="file that contains prefix/network")
	parser.add_argument("--show", action="store_true",help="show all prefix-set name")
	parser.add_argument("--diff", action="store",default=False,help="file that contains old routing table prefix to make a diff")
	parser.add_argument("--save", action="store",default=False,help="tag to save filtering result")
	parser.add_argument("--xlsx", action="store",default=False,help="save to diff excel file")
	parser.add_argument("--debug", action="store_true",default=False,help="mode debug")
	args = parser.parse_args()
	
	if  args.diff  and not args.file:
		raise argparse.ArgumentError(None,'--file  is manadatory with --diff')
		
	if  args.save  and not args.file:
		raise argparse.ArgumentError(None,'--file  is manadatory with --save')
		
	if  args.xlsx  and not args.diff:
		raise argparse.ArgumentError(None,'--diff  is manadatory with --xlsx')
		
	routemap=routeMap(args.yaml)
	if args.show:
		print(routemap)
		
	if args.prefix:
		result=routemap.match(args.prefix)
		
		if result:
			print(f'{args.prefix} pass')
		else:
			print(f'{args.prefix} drop')
	if args.file:
		prefixListStr=getListNetFromFile(args.file)
		
		result=routemap.matchList(prefixListStr)
		
		ppr(result,width=5)
		timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
		
		if args.save:
			
			filename_pass=f'{DIR_RESULT}{args.save}_pass{timestamp}.TXT'
			filename_drop=f'{DIR_RESULT}{args.save}_drop{timestamp}.TXT'
			saveListNetToFile(result['pass'],filename_pass)
			saveListNetToFile(result['drop'],filename_drop)
		
		if args.diff:
			oldRoute=getListNetFromFile(args.diff)
			
			diffObj=ddiff(sorted(oldRoute),sorted(result['pass']))
			
			ppr(diffObj)
			
			diffObjForXlsx={sheet: [ [entry] for entry in data ] for sheet,data in diffObj.items() }
			if args.xlsx:
				FileResult=f'{DIR_RESULT}diff_{args.xlsx}{timestamp}.xlsx'
				xlsMatrix(FileResult,diffObjForXlsx)