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
import glob
from pathlib import Path

from xlsxDictWriter import xlsMatrix

DIR_LOG="/home/x112097/LOG"

PATH_YAML='/home/x112097/yaml/prefixSet/bck/'

def saveResult(result,saveName):
		suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
		filename=PATH_YAML+'/'+saveName+suffix
		with open(filename,'w') as yml_w:
			 yaml.dump(result,yml_w ,default_flow_style=False)
			 

def getLastResult(saveName):
	return max(glob.glob(f'{PATH_YAML}/{saveName}_*.yml'),key=os.path.getctime)
	
def getEquipementFromFilename(Str):
	Name=Path(Str).name
	resultat=None
	NomFile1=pp.Word(pp.alphanums+'-')+pp.Literal('_').suppress()+pp.Word(pp.nums,min=8,max=8).suppress()+pp.Literal('_').suppress()+pp.Word(pp.nums+'hms').suppress()+pp.Literal('.log').suppress()
	NomFile2=pp.Word(pp.alphanums+'-_')+pp.Literal('.log').suppress()
	NomFile3=pp.Word(pp.alphanums+'-_')+pp.Suppress(pp.Optional(pp.CaselessLiteral('.dns')+pp.Word(pp.nums,min=2,max=2)+pp.Literal('socgen.log')))
	NomFile=pp.MatchFirst([NomFile1,NomFile2,NomFile3])
	resultat=NomFile.parseString(Name).asList()[0]
	
	return resultat
	
def ParsePrefixSetEntry(Str):
	Resultat={}
	virgule=pp.Suppress(pp.Literal(','))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	prefix=pp.Combine(ipAddress+pp.Literal('/')+slash)
	KeyFilter=pp.Literal('ge')|pp.Literal('le')|pp.Literal('eq')
	FilterList=pp.dictOf(KeyFilter,slash)
	filterSetEntry=pp.dictOf(prefix,pp.Optional(FilterList,default=None)+pp.Optional(virgule))


	Resultat=filterSetEntry.parseString(Str).asDict()

		
	return Resultat

def ParsePrefixSet(FileOrStr,mode="file"):
	Resultat={}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress(pp.Literal('Listing for all Prefix Set objects'))
	virgule=pp.Suppress(pp.Literal(','))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	prefix=pp.Combine(ipAddress+pp.Literal('/')+slash)
	KeyFilter=pp.Literal('ge')|pp.Literal('le')|pp.Literal('eq')
	FilterList=pp.dictOf(KeyFilter,slash)
	filterSetEntry=pp.dictOf(prefix,pp.Optional(FilterList,default=None)+pp.Optional(virgule))
	Name=pp.Literal('prefix-set').suppress()+pp.Word(pp.alphanums+'_-. \/()=[]:{},')
	endSet=pp.Literal('end-set').suppress()
	BlocPrefixSet=pp.Optional(Show)+pp.SkipTo('prefix-set').suppress()+pp.dictOf(Name,filterSetEntry+endSet+pp.Optional(pp.Literal('!')))

	if mode=='str':
		Resultat=BlocPrefixSet.parseString(FileOrStr).asDict()
	elif mode=='file':
		Resultat=BlocPrefixSet.parseFile(FileOrStr).asDict()
		
	return Resultat
	
class prefixSetEntry(object):
	def __init__(self,prefix,filterPrefix=None):
		self.prefix=prefix
		self.prefixObj=IPNetwork(self.prefix)
		if filterPrefix:
			self.eq=filterPrefix.get('eq')
			self.le=filterPrefix.get('le')
			self.ge=filterPrefix.get('ge')

		else:
			self.eq=None
			self.le=None
			self.ge=None
			
		if isinstance(self.eq,str):
			self.eq=int(self.eq)
			
		if isinstance(self.le,str):
			self.le=int(self.le)
			
		if isinstance(self.ge,str):
			self.ge=int(self.ge)
			
	def __contains__(self,prefix):
		prefixObj=IPNetwork(prefix)
		
		if self.eq==None and self.le==None and self.ge==None:
			return self.prefixObj == prefixObj
			
		if self.eq:
			return prefixObj in self.prefixObj and self.eq==prefixObj.prefixlen
			
		if self.ge and self.le:
			return prefixObj in self.prefixObj and self.ge<=prefixObj.prefixlen and self.le>=prefixObj.prefixlen
			
		if self.ge:
			return prefixObj in self.prefixObj and self.ge<=prefixObj.prefixlen
			
		if self.le:
			return prefixObj in self.prefixObj and self.le>=prefixObj.prefixlen
			
		assert True,"impossible case"
		
	def __str__(self):
		if self.eq==None and self.le==None and self.ge==None:
			return self.prefix
			
		if self.eq:
			return f"{self.prefix} eq {self.eq}"
			
		if self.ge and self.le:
			return f"{self.prefix} ge {self.ge} le {self.le}"
			
		if self.ge:
			return f"{self.prefix} ge {self.ge}"
			
		if self.le:
			return f"{self.prefix} le {self.le}"
			
		assert True,"impossible case"
		
		
	def __repr__(self):
		if self.eq==None and self.le==None and self.ge==None:
			return self.prefix
			
		if self.eq:
			return f"{self.prefix} eq {self.eq}"
			
		if self.ge and self.le:
			return f"{self.prefix} ge {self.ge} le {self.le}"
			
		if self.ge:
			return f"{self.prefix} ge {self.ge}"
			
		if self.le:
			return f"{self.prefix} le {self.le}"
			
		assert True,"impossible case"
	
		
		
		
	
class prefixSet(object):
	def __init__(self,name="",PrefixSetList=[],prefixFile='',verbose=False):
		self.name=name
		if PrefixSetList:
			self.prefixSetList=PrefixSetList
		elif prefixFile:
			self.prefixSetList=[]
			with open(prefixFile) as file__:
				prefixStrList=[ entry.strip() for entry in file__.readlines() ]
				base=os.path.basename(prefixFile)
				self.name=os.path.splitext(base)[0]
				for prefix__ in prefixStrList:
					dataCur=ParsePrefixSetEntry(prefix__)
					prefixCurStr=list(dataCur.keys())[0]
					filterPrefixCur=dataCur[prefixCurStr]
					self.prefixSetList.append(prefixSetEntry(prefixCurStr,filterPrefix=filterPrefixCur))
					
		self.verbose=verbose
			
	def __contains__(self,prefixStr):
		result=False
		
		for prefix in self.prefixSetList:
			if prefixStr in prefix:
				if self.verbose:
					print(f'match prefix-set:{self.name} entry:{prefix.__str__()}')
				return True
		
		return result
		
	def search(self,prefix):
		for entry in self.prefixSetList:
			if prefix  in entry:
				return (True,self.prefixSetList.index(entry),self.name,entry.__str__())
		return False
		
	def __str__(self):
		return "\n".join([ prefix.__str__()  for prefix in self.prefixSetList])
		
	def __repr__(self):
		return self.__str__()
		
	def save(self):
		saveResult({'name':self.name,'prefix-set':[ str(entry) for entry in self.prefixSetList]},f'{PATH_YAML}prefix-set_{self.name}')

class prefixSets(object):
	def __init__(self,file,mode='txt',verbose=False):
		self.prefixSetDict={}
		if mode=='txt':
			self.all_prefix_set=ParsePrefixSet(file)
		elif mode=='yaml':

			lastResult=getLastResult(file)
			with open(lastResult) as yml:
				self.all_prefix_set=yaml.load(yml,Loader=yaml.SafeLoader)
		else:
			print('prefix-set mode not supported',file=sys.stderr)
			sys.exit(1)
		self.verbose=verbose

		for prefixSetName in self.all_prefix_set:
			PrefixSetListCur=[ prefixSetEntry( key,item) for key,item in self.all_prefix_set[prefixSetName].items()]
			self.prefixSetDict[prefixSetName]=prefixSet(prefixSetName,PrefixSetList=PrefixSetListCur,verbose=self.verbose)

	def getPrefixSetsName(self):
		return list(self.prefixSetDict.keys())
		
	def __getitem__(self, item):
         return self.prefixSetDict[item]
		 
	def __contains__(self,item):
		return item in self.prefixSetDict
		
	def match(self,prefixsetName,prefix):
		if prefixsetName not in self.prefixSetDict:
			print(f'prefixName not present in prefix-set list')
			return False
		
		return prefix in self.prefixSetDict[prefixsetName]
		
	
	def printthisPrefixSet(self,name):
	
		if name not in self.prefixSetDict:
			print(f'prefixName not present in prefix-set list')
			return False
			
		ppr(self.prefixSetDict[name])
		
	def save(self,filename):
		saveResult(self.all_prefix_set,filename)


if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--name", action="store",help="prefix")
	parser.add_argument("--prefix", action="store",help="prefix")
	parser.add_argument("--file", action="store",help="file contains prefix-list IOS-XE format",required=True)
	parser.add_argument("--show", action="store_true",help="show all prefix-set name")
	parser.add_argument("--save", action="store_true",default=False,help="save prefix-set")
	parser.add_argument("--yaml", action="store_true",default=False,help="yaml tag, probably a hostname")
	parser.add_argument("--debug", action="store_true",default=False,help="mode debug")
	args = parser.parse_args()
	
	rootLogger = logging.getLogger('Logger prefixFilter')
	timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
	fileHandler = logging.FileHandler(f"{DIR_LOG}/prefixFilter{timestamp}.log")
	customHandler = logging.StreamHandler()
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	fileHandler.setFormatter(formatter)
	rootLogger.addHandler(fileHandler)
	rootLogger.setLevel(logging.INFO)
	
	if  args.prefix and not args.name:
		raise argparse.ArgumentError(None,'--name  is manadatory with --prefix')
		
	if  (args.name  and not args.prefix) and (args.name  and not args.show):
		raise argparse.ArgumentError(None,'--prefix or --show is manadatory with --name')
	
	if args.debug:
		consoleHandler = logging.StreamHandler()
		consoleHandler.setFormatter(formatter)
		rootLogger.addHandler(consoleHandler)
		rootLogger.setLevel(logging.DEBUG)
	
	if not args.yaml:
		prefixSetsObj=prefixSets(args.file,verbose=args.debug)
	else:
		prefixSetsObj=prefixSets(args.file.lower(),mode='yaml',verbose=args.debug)
	
	if args.show and not args.name:
		ppr(prefixSetsObj.getPrefixSetsName())
	elif args.show and args.name:
		prefixSetsObj.printthisPrefixSet(args.name)
		
		
	if args.prefix and not args.name:
		result=prefixSetsObj.match(args.name,args.prefix)
		ppr(result)
	elif args.prefix and args.name:
		if args.name in prefixSetsObj.prefixSetDict:
			result=prefixSetsObj.prefixSetDict[args.name].search(args.prefix)
			print(result)
		else:
			print(f'{args.name} prefix-set unknwown')
			
	if args.file and args.save:
		hostname=getEquipementFromFilename(args.file)
		prefixSetsObj.save(hostname)
		
		