#!/bin/python3.7
# coding: utf-8

import argparse
import pdb
import yaml
import io
from pprint import pprint
import sys
import ipaddress
sys.path.insert(0,'/home/x112097/py/dmo')
import dmoPy3.aci.msc as msc
import dmoPy3.aci.socgenbase as socgenbase
import pwd
import os
from getsec import *
import pyparsing as pp
TSK="/home/x112097/CONNEXION/pass.db"

def DecPrint(headers,motif="=",size=60):
	resultat=io.StringIO()
	LIGNE=motif*size
	LEN=len(headers)
	DEB=int((size/2-LEN/2-1))
	toWrite=" "+headers+" "
	resultat.write(LIGNE+'\n')
	written=resultat.write(LIGNE[:DEB])
	written+=resultat.write(toWrite)
	resultat.write(LIGNE[written:]+'\n')
	resultat.write(LIGNE+'\n')
	return resultat.getvalue()

def ParseEpg(epg_name):
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 1 ))
	VLAN=pp.Suppress(pp.CaselessLiteral('vlan_'))+Vlan+pp.Suppress(pp.CaselessLiteral('_bd')|pp.CaselessLiteral('_epg'))
	
	return VLAN.parseString(epg_name)[0]
	
class Loader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f)

Loader.add_constructor('!include', Loader.include)
	
class sgYamlSchema(object):
	def __init__(self,yaml_file,tenant="TN001",fabric=""):
		self.yaml_in=None
		with open(yaml_file, 'r') as yml__:
			self.yaml_in=yaml.load(yml__,Loader=yaml.SafeLoader)
		self.tenant=tenant
		self.yaml_out={}
		self.initSchema()
		
		self.initSchemaTemplates()
		self.fabric=fabric
		
		if fabric:
			try:
				#pdb.set_trace()
				config_file=socgenbase.get_conf_filename(fabric)
				with open(config_file,'r') as file:
					self.config_yaml=yaml.load(file,Loader)
					self.ip_msc=self.config_yaml['msc']['servers'][0]['ip']
			except :
				print("Fabric '%s' is unknown"%fabric,file=sys.stderr)
				print("Known fabrics: '%s'")
				for (name,conf) in socgenbase.hash_of_conf_files.items():
					print(" - %s (conf file: %s)"%(name,conf),file=sys.stderr)
				print()
				print("Please edit 'hash_of_conf_file' in 'dmoPy3/aci/socgenbase.py' file to add new fabrics")
				sys.exit(1)
		else:
			print("Fabric name is mandatory")
			sys.exit(1)
		self.authdomain_msc=self.config_yaml['msc']['authdomain']
		self.user=pwd.getpwuid(os.getuid()).pw_name
		tsk=secSbe(TSK)
		self.password=tsk.tac
		self.controller=msc.Msc(self.ip_msc,user=self.user,password=self.password,authdomain=self.authdomain_msc)
		self.getTenantList()
		self.getSiteList()
		self.controller.logout()
		self.controller.tunnel.stop()
		self.initSchemaSite()
		self.initTemplateAp()
		self.initSchemaVrf()
		self.initSiteAp()
		self.initContractFilter()
		self.initTemplateEgpsBds()
		self.initTemplateEpgsContracts()
		self.initTenant()
		
	def initSchema(self):
		self.yaml_out['schema']=self.yaml_in['displayName']
		
	def initSchemaSite(self):
		resultat=[]
		for site in self.yaml_in['sites']:
			try:
				resultat.append({'template':self.sitesId[site['siteId']],'templateName':site['templateName']})
			except KeyError as E:
				pdb.set_trace()
				print(E)
		self.yaml_out['schema_sites']=resultat
		
	def initContractFilter(self):
		resultat=[]
		for template in self.yaml_in['templates']:
			for contract in template['contracts']:
				res_cur={'contract': contract['name'] , 'template': template['name']}
				if res_cur not in resultat:
					resultat.append(res_cur)
					
		self.yaml_out['templates_contracts_filters']=resultat
	

	def initTemplateEgpsBds(self):
		resultat=[]
		for template in self.yaml_in['templates']:
			for bds in template['bds']:
				if bds['l2Stretch']:
					L2STRETCH="yes"
				else:
					L2STRETCH="no"
				preferred_group="yes"
				resultat.append({'vlan_id':ParseEpg(bds['name']), 'template':template['name'],'ap':template['anps'][0]['name'], 'L2STRETCH': L2STRETCH, ' preferred_group': preferred_group, 'BD_unknown_unicast': bds['l2UnknownUnicast']})

		self.yaml_out['templates_epgs_bds']=resultat
		
	def initTemplateEpgsContracts(self):
		resultat=[]
		resultat_ct={}
		for template in self.yaml_in['templates']:
			for contract in template['contracts']:
				contrat_cur_name=contract['name']
				resultat_ct[contrat_cur_name]=[{'schema':"",'template':template['name'],'type':'consumer'},{'schema':"",'template':template['name'],'type':'provider'}]
		
		for template in self.yaml_in['templates']:
			for epg in template['bds']:
				pdb.set_trace()
				pass
				
	def initTemplateAp(self):
		resultat=[]
		for template in self.yaml_in['templates']:
			resultat.append({'template':template['name'],'ap':template['anps'][0]['name']})
		self.yaml_out['templates_ap']=resultat	
		
	def initSiteAp(self):
		resultat=[]
		resultat_int={}
				
		for site in self.yaml_in['sites']:
			
			try:
				nom_site_cur=self.sitesId[site['siteId']]
				if site['anps']:
					ap_cur=site['anps'][0]['anpRef'].split('/')[-1]
				else:
					continue
				if nom_site_cur not in resultat_int.keys():
					resultat_int[nom_site_cur]=[[site['templateName']],ap_cur]
				else:
					if ap_cur==resultat_int[nom_site_cur][1]:
						resultat_int[nom_site_cur][0].append(site['templateName'])
					else:
						print("Warning")
						pdb.set_trace()
			except KeyError as E:
				pdb.set_trace()
				print(E)
				
			except IndexError as E:
				pdb.set_trace()
				print(E)
				

				
		self.yaml_out['sites_ap']=resultat_int
		
		
	def initTenant(self):
		pdb.set_trace()
		self.yaml_out['tenant']=self.tenant
		
	def initSchemaTemplates(self):
		self.yaml_out['schema_templates']=[ {'template':template__['name']} for template__ in self.yaml_in['templates'] ]
		
	def initSchemaVrf(self):
		resultat=""
		for template in self.yaml_in['templates']:
			try:
				resultat=template['vrfs'][0]['name']
				self.yaml_out['schema_vrf_template_ref']=template['name']
				break
			except KeyError:
				pass
			except IndexError:
				pass
			
		if resultat:
			self.yaml_out['schema_vrf']=resultat
		
	def printIn(self):
		print(DecPrint("yaml in"))
		pprint(self.yaml_in)
		
	def printOut(self):
		print(DecPrint("yaml out"))
		pprint(self.yaml_out)
		
	def getTenantList(self):
		self.tenants=self.controller.get_tenants_list(json_output=True)
		
	def getSiteList(self):
		self.sites=self.controller.get_sites_list(json_output=True)
		self.sitesId={}
		for site in self.sites:
			self.sitesId[site.id]=site.name
		
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file_yml')
	parser.add_argument('--fabric',help='fabric')
	args = parser.parse_args()
	

		
	sgObj=sgYamlSchema(args.file_yml,fabric=args.fabric)
	
	sgObj.printIn()
	sgObj.printOut()
