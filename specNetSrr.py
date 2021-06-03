#!/usr/local/bin/python3.9
# coding: utf-8

import pdb
import argparse
from pprint import pprint as ppr
from pprint import pformat as pprs
import sys
sys.path.insert(0,'/Users/sandro.bernis/py')
import jinja2
from xlsxToDict import *
import os

TEMPLATE_DIR="/Users/sandro.bernis/TEMPLATE/J2"
CONFIG_DIR="/Users/sandro.bernis/CONF"

VRFID={ 'SERVIER_DEFAULT': { 'id':'10', 'bes1':'156' , 'bes2':'157'}, 
   'toip' : { 'id':'11', 'bes1':'158' , 'bes2':'159'},
   'ConvInet' : { 'id':'12', 'bes1':'160' , 'bes2':'161'},
   'Inet':{ 'id':'13', 'bes1':'162' , 'bes2':'163'},
   'Bio':{ 'id':'14', 'bes1':'164' , 'bes2':'165'},
   'affvidrest':{ 'id':'15', 'bes1':'166' , 'bes2':'167'},
   'Offload':{ 'id':'16', 'bes1':'168' , 'bes2':'169'},
   'Offload-Biogaran':{ 'id':'17', 'bes1':'170' , 'bes2':'171'},
   'Orion':{ 'id':'18', 'bes1':'174' , 'bes2':'175'},
   'AccessCtrl':{ 'id':'19', 'bes1':'342' , 'bes2':'343'},
   'GDVidSur':{ 'id':'20', 'bes1':'3191' , 'bes2':'3192'},
   'ACI':{ 'id':'100', 'bes1':'176' , 'bes2':'177'},
}
POD={'surval':'1' ,'gidy':'2' ,'croissy':'6'}
def writeConfig(config_str,fichier):
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)

def getTagBes(hostname,vrf='ACI',vrfdata=VRFID):
	if hostname[-1]=='1':
		return vrfdata[vrf]['bes1']
	elif  hostname[-1]=='2':
		return vrfdata[vrf]['bes2']

def pod(hostname,podid=POD):
	for site in podid:
		if site in hostname:
			return podid[site]
			
			
class equipmentConfig(object):
	def __init__(self,dir,params,template):
		'''params:dict, template:jinja2 file'''
		self.params=params
		self.j2File=template
		#Loader Jinja
		self.loader = jinja2.FileSystemLoader(TEMPLATE_DIR+'/'+dir)
		self.env = jinja2.Environment( loader=self.loader)
		#add filter here
		vpcDomain=lambda t:str(int(t[-2])+100)
		vpcPriority=lambda t: '4096' if t[-1]=='X' else '8192'
		priority=lambda t: '1' if t[-1]=='X' else '10'
		ipOnly=lambda t: str(IPNetwork(t).ip)
		self.env.filters['getTagBes']=getTagBes
		self.env.filters['getIdBes']=lambda y:y[-1]
		self.env.filters['pod']=pod
		### template object
		self.template=self.env.get_template(os.path.basename(self.j2File))
			
		# config initialization
		self.config=self.template.render(self.params)
		
	def getConfig(self):
		return self.config
		
class n9kConfig(equipmentConfig):
	def __init__(self,params):
		'''params:dict'''
		self.j2File='SRR/n9k.j2'
		super().__init__('SRR',params,self.j2File)
		
class srrConfig(object):
	def __init__(self,excelFile,tag='DEFAULT'):
		self.xslxContainerObj=xlsContainer(excelFile)
		self.datas=self.xslxContainerObj.datas
		self.tag=tag
		self.configType=list(self.datas.keys())
		self.equipments=list(self.datas[self.configType[0]][0].keys())
		del self.equipments[self.equipments.index('vrf')]
		self.initDataByEquipment()
		self.vrfid=VRFID
		self.configDir=CONFIG_DIR+'/SRR/'+self.tag
		self.initN9ksConfig()
		
	def initN9ksConfig(self):		
		self.n9ksConfig={}
		for n9k in self.equipments:
			self.n9ksConfig[n9k]=n9kConfig({'hostname':n9k,'vrfs':self.datasByHost[n9k],'vrfinfo':self.vrfid})

	
	def initDataByEquipment(self):
		self.datasByHost={}
		for typeData in self.datas:
			for entry in self.datas[typeData]:
				for host in self.equipments:
					if host not in self.datasByHost:
						self.datasByHost[host]={}
					if entry['vrf'] not in self.datasByHost[host]:
						self.datasByHost[host][entry['vrf']]={typeData:entry[host]}
					else:
						self.datasByHost[host][entry['vrf']][typeData]=entry[host]
					

	def writeCfg(self):
		if not os.path.exists(self.configDir):
			os.makedirs(self.configDir)
			
		for equipment__ in self.n9ksConfig:
			writeConfig(self.n9ksConfig[equipment__].getConfig(),self.configDir+'/'+equipment__+'.CFG')
			
		
		
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("--excel",  action="store",help="fichier excel contenant les informations",required=True)
	parser.add_argument("--tag",  action="store",default='DEFAULT',help="tag",required=False)	
	args = parser.parse_args()
	
	configObj=srrConfig(args.excel,args.tag)
	
	ppr(configObj.datas)
	
	print(configObj.equipments)
	
	ppr(configObj.datasByHost)
	
	if args.tag:
		configObj.writeCfg()
