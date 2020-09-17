#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import re
import xlrd
import argparse
import pdb
import io
import os
import sys
import jinja2
import ipaddress
from paramiko import SSHClient
from scp import SCPClient


TEMPLATE_FABRIC_DIR="/home/x112097/TEMPLATE/J2"
TEMPLATE_FABRIC='fabricACI.j2'
TEMPLATE_LEAF_MONO='leafMono.j2'
TEMPLATE_INT_LEAF='leafInterface.j2'
TEMPLATE_LEAF_DUAL='leafDual.j2'
REPERTOIRE_SCP="ANSIBLE/HCS-CISCO-ACI-master"
BASTION="192.64.10.129"
USERNAME="x112097"

def copyScpDir(username,bastion,repertoire,remote_path="."):
	ssh_client=SSHClient()
	ssh_client.load_system_host_keys()
	ssh_client.connect(bastion, username=username)
	scp = SCPClient(ssh_client.get_transport())
	scp.put(repertoire,remote_path=remote_path,recursive=True)
	scp.close()

class FabricACI(object):
	def __init__(self,xls_file):
		wb=xlrd.open_workbook(xls_file)
		sh = wb.sheet_by_name(u'GLOBAL')
		
		loader = jinja2.FileSystemLoader(TEMPLATE_FABRIC_DIR)
		env = jinja2.Environment( loader=loader)
		env.filters['getneighbor']=self.getNeighbor
		env.filters['listInttoStr']=self.listInttoStr
		#self.template=env.get_template(os.path.basename(TEMPLATE_FABRIC))
		self.templates={'apic':env.get_template(os.path.basename(TEMPLATE_FABRIC)), 'leaf_mono':env.get_template(os.path.basename(TEMPLATE_LEAF_MONO)),'leaf_dual':env.get_template(os.path.basename(TEMPLATE_LEAF_DUAL)),'leaf_if':env.get_template(os.path.basename(TEMPLATE_INT_LEAF))}
		for rownum in range(0,sh.nrows):
			ligne_cur=sh.row_values(rownum)
			if isinstance(ligne_cur[1],float):
				super().__setattr__(ligne_cur[0].lower(),str(int(ligne_cur[1])))
			elif re.match('^<.*>$',ligne_cur[1]):
				wb_cur=ligne_cur[1].replace('>','').replace('<','')
				sh_cur = wb.sheet_by_name(wb_cur)
				super().__setattr__(ligne_cur[0].lower(),self.getDictFromSheet(sh_cur))
			else:
				super().__setattr__(ligne_cur[0].lower(),ligne_cur[1].strip())
		
		self.fabric=self.fabric_perimeter
		self.mtce_group=self.setMaintenanceGroup()
		self.initTenantDict()
		self.initSwitch()
		self.initLeafGroup()
		self.initSpineGroup()
		self.initNodeDict()
		self.setInterfaceL3Out()
		self.setVPCInterface()
		self.initFilenameYml()
		self.initLeafVpcIf()
		self.initVrfDict()
		
	@staticmethod
	def getDictFromSheet(sh__):
		resultat=[]
		lignes=[]
		
		for rownum in range(0,sh__.nrows):
			lignes.append(sh__.row_values(rownum))

		
		for ligne in lignes[1:]:
			dict_cur={}
			
			column_id=-1
			for value in ligne:
				#column_id=ligne.index(value)
				column_id+=1
				header=lignes[0][column_id]
				if value=='RET-APC-DC5-2B1-0001':
					pdb.set_trace()
				if isinstance(value,float):
					dict_cur[header]=str(int(value))
				else:
					dict_cur[header]=value.strip()
			resultat.append(dict_cur)

			
		return resultat
		
	@staticmethod
	def getNeighbor(ip__):
		IP__=ipaddress.IPv4Interface(ip__)
		result=None
		if IP__.ip.__int__()%2==1:
			result=str((IP__+1).ip)
		else:
			result=str((IP__-1).ip)
			
			
		return result
		
	@staticmethod
	def listInttoStr(liste__):
		return str(liste__).replace("\'","\"")
		
	
	def setMaintenanceGroup(self):
		result={}
		for node in self.switchs:
			#pdb.set_trace()
			if re.match('^[1-9][0-9][0-9]$',node['nodeId']):
				key_cur="Leaf_"+node['nodeId'][0]+"0x"
				if key_cur not in result:
					result[key_cur]={'name':'NODES_'+node['nodeId'][0]+'XX','nodeId':[node['nodeId']]}
				else:
					result[key_cur]['nodeId'].append(node['nodeId'])
					
			elif re.match('1[0-9][0-9][0-9]$',node['nodeId']):
				result['Spine_'+node['nodeId']]={'name':'SPINE_'+node['nodeId'],'nodeId':[node['nodeId']]}
				
		return result
		
	def setVPCInterface(self):
		self.vpc_int=[]
		
		for vpc in self.vpcs:
			liste_interface_cur=vpc['interface'].split(',')
			for interface in liste_interface_cur:
				self.vpc_int.append({'name':vpc['name'],'interface':interface,'leaf1':vpc['leaf1'],'leaf2':vpc['leaf2']})
				
		
		
	def initSwitch(self):
		self.leafs=[]
		self.spines=[]
		for node in self.switchs:
			#pdb.set_trace()
			if re.match('^[1-9][0-9][0-9]$',node['nodeId']):
				self.leafs.append({'name':node['name'],'nodeId':node['nodeId'],'serial':node['serial'],'podId':node['podId'],'type':node['type']})
			elif re.match('1[0-9][0-9][0-9]$',node['nodeId']):
				self.spines.append({'name':node['name'],'nodeId':node['nodeId'],'serial':node['serial'],'podId':node['podId'],'type':node['type']})
	
	@staticmethod
	def getOtherLeaf(leaf):
		result=""
		if re.match('^1[0-9][0-9]$',leaf):
			result=re.sub('^1([0-9][0-9])$','2'+r'\1',leaf)
		elif re.match('^2[0-9][0-9]$',leaf):
			result=re.sub('^2([0-9][0-9])$','1'+r'\1',leaf)
		elif re.match('^[3-9][0-9]1$',leaf):
			result=re.sub('([3-9][0-9])1$',r'\1',leaf)+"2"
		elif re.match('^[3-9][0-9]2$',leaf):
			result=re.sub('([3-9][0-9])2$',r'\1',leaf)+"1"
					
		return result
		
	def setInterfaceL3Out(self):
		result=[]
		temp_list=[]
		for l3out in self.l3outs:
			if (l3out['int'],l3out['leaf1']) not in temp_list:
				result.append({'interface':l3out['int'],'node':l3out['leaf1']})
				temp_list.append((l3out['int'],l3out['leaf1']))
			if (l3out['int'],l3out['leaf2']) not in temp_list:
				result.append({'interface':l3out['int'],'node':l3out['leaf2']})
				temp_list.append((l3out['int'],l3out['leaf2']))
			
		self.interfacesl3out=result
		
			
	def testPresenceNodeId(self,nodeId__):
		test=False
		for node in  self.switchs:
			if node['nodeId']==nodeId__:
				test=True
		return test
		
	def initLeafGroup(self):
		self.leafDuals=[]
		self.Allleafs=[]
		for leaf in self.leafs:
			OtherLeafNodeId=self.getOtherLeaf(leaf['nodeId'])
			if leaf['nodeId'] not in self.Allleafs:
				self.Allleafs.append(leaf['nodeId'])
			if self.testPresenceNodeId(OtherLeafNodeId)==False:
				print("Warning Leaf non dual")
			else:
				if [leaf['nodeId'],OtherLeafNodeId] not in self.leafDuals and [OtherLeafNodeId,leaf['nodeId']] not in self.leafDuals :
					self.leafDuals.append([leaf['nodeId'],OtherLeafNodeId])
					
	def initSpineGroup(self):
		self.allspine=[]
		for spine in self.spines:
			if spine not in self.allspine:
				self.allspine.append(spine['nodeId'])
				
	def initLeafVpcIf(self):
		self.leafsVpcIf=[]
		for vpc in self.vpcs:
			if [vpc['leaf1'],vpc['leaf2']] not in self.leafsVpcIf:
				self.leafsVpcIf.append([vpc['leaf1'],vpc['leaf2']] )
			
	
	def initVrfDict(self):
		self.Vrf_by_vlans={}
		for epg in self.epgs:
			self.Vrf_by_vlans[epg['vlan_id']]=epg['vrf']
						
	def initConfigFile(self):
		result={}
		for modele in self.templates.keys():
			if modele!='leaf_if':
				result[modele]=self.templates[modele].render(self.__dict__)
			else:
				for leafPod_if in self.leafsVpcIf:
					self.leaf1_cur=leafPod_if[0]
					self.leaf2_cur=leafPod_if[1]
					print(self.__dict__)
					result['leaf_'+'_'.join(leafPod_if)]=self.templates[modele].render(self.__dict__)
				
		
		self.configs=result

		
	def initTenantDict(self):
		self.tenant_dict={}
		for tenant in self.tenants:
			self.tenant_dict[tenant['name']]=tenant['alias']
			
	def initNodeDict(self):
		self.node_dict={}
		for node in self.switchs:
			self.node_dict[node['nodeId']]=node
			
	def initFilenameYml(self):
		self.filename={}
		self.filename["apic"]='ACI_'+self.fabric_perimeter+'_FABRIC.yml'
		self.filename["leaf_mono"]='ACI_'+self.fabric_perimeter+'_LEAF_template_mono.j2'
		self.filename["leaf_dual"]='ACI_'+self.fabric_perimeter+'_LEAF_template_dual.j2'
		
		for leaf_ in self.leafDuals:
			self.filename['_'.join(leaf_)]='ACI_'+self.fabric_perimeter+'_LEAF_'+'-'.join(leaf_)+'.yml'
			
	
	def affiche_config(self):
		for type in self.configs.keys():
			print(type+":")
			print(self.configs[type])
			
	def writeConfig(self,config_str,fichier):
		with open(fichier,'w+') as Configfile:
			Configfile.write(config_str)

			
	def recConfig(self,repertoire):
		for type in self.templates.keys():
			if type!='leaf_if':
				self.writeConfig(self.configs[type],repertoire+'/'+self.filename[type])
			else:
				for leafPod_if in self.leafsVpcIf:
					self.writeConfig(self.configs['leaf_'+'_'.join(leafPod_if)],repertoire+'/'+self.filename['_'.join(leafPod_if)])
			

	def __str__(self):
		return str(self.__dict__)
		
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-x", "--xls",action="store",help="mode fichier Excel",required=True)
	parser.add_argument("-r", "--repertoire",action="store",help="repertoire contenant les yaml ACI",required=True)
	parser.add_argument("-b", "--bastion",action="store_true",help="copy du repertoire vers le bastion",required=False)
	
	args = parser.parse_args()
	
	if args.xls:
		ACI__=FabricACI(args.xls)
		print(ACI__)
		
		ACI__.initConfigFile()
		ACI__.affiche_config()
		
		
	if args.repertoire:
		if not os.path.exists(args.repertoire):
			os.makedirs(args.repertoire)
			
		if not os.path.exists(args.repertoire+"/"+ACI__.fabric_perimeter):
			os.makedirs(args.repertoire+"/"+ACI__.fabric_perimeter)
		
		ACI__.recConfig(args.repertoire+"/"+ACI__.fabric_perimeter)
		
		if args.bastion:
			copyScpDir(USERNAME,BASTION,args.repertoire+"/"+ACI__.fabric_perimeter,remote_path=REPERTOIRE_SCP)


		