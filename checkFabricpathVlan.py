#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import re
import pdb
import glob
import sys
import pickle 
import os
import random

from ParsingShow  import ParseVlanRunFile , getEquipementFromFilename
from natVlanConfig import initVlanNat

def writeConfig(config_str,fichier):

	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
	return None

class Vlan:
	"Classe vlan, nom et id"
	def __init__(self,id,name="NONAME",mode="CLASSICAL"):
		"Constructeur"
		self.id = id
		self.name=name
		self.mode=mode
		
	def __str__(self):
		"Affichage"
		return "Vl:"+self.id.__str__()+" name :"+self.name+" mode :"+self.mode
 
	
class ExtractInfoVlan:
	"extrait les informations d'un repertoire contenant les configurations"
	def __init__(self,repertoire="",dump=""):
		self.vlans_DC={}
		self.vlans_FP={}
		self.vlans_FP_missing={}
		if repertoire:
			Liste_file_show_run=glob.glob(repertoire+'/*.log')
			for file_show_run in Liste_file_show_run:
				file_show_run__=file_show_run.split('/')[-1]
				equipement__=getEquipementFromFilename(file_show_run__).upper()
				self.vlans_DC[equipement__]=ParseVlanRunFile(file_show_run)
  
		if dump:
				self.load(dump)
		
		#pdb.set_trace()

		
	def __str__(self):
		"Affichage"
		result=""
		for equipement in self.vlans_DC:
			result+=str(self.vlans_DC[equipement])+'\n'+'\n'
			
		return result
	
	def save(self,filename):
			with open(filename,'wb') as file__:
					pickle.dump(self,file__)
	
	def load(self,filename):
			dc=None
	
			with open(filename,'rb') as file__:
					dc=pickle.load(file__)
	
			try:
					self.vlans_DC=dc.self.vlans_DC
	
			except:
					print('Error load dump')

	
	def setVlanFP(self):
		for equipement__ in self.vlans_DC.keys():
			for vlan__ in self.vlans_DC[equipement__].keys():
				try:
					if self.vlans_DC[equipement__][vlan__]['mode']=='fabricpath':
						if vlan__ not in self.vlans_FP.keys():
							self.vlans_FP[vlan__]=[]
							self.vlans_FP[vlan__].append(equipement__)
						else:
							self.vlans_FP[vlan__].append(equipement__)
				except KeyError:
					print(vlan__+":")
					print(str(self.vlans_DC[equipement__]))
					pdb.set_trace()
					
	def getVlanFP(self):
		return self.vlans_FP
		
	def setVlanFP_missing(self):
		Liste_equipement=self.vlans_DC.keys()
		for vlan__ in self.vlans_FP.keys():
			if vlan__=='2565':
				pdb.set_trace()
			Liste_equipement_missing_cur=list(set(Liste_equipement)-set(self.vlans_FP[vlan__]))
			if Liste_equipement_missing_cur:	
				self.vlans_FP_missing[vlan__]=Liste_equipement_missing_cur
				
	def getVlanFP_missing(self):
		return self.vlans_FP_missing
		
	def getConfVlan(self,vlan__,OrderedListEquipment=[]):
	
		ConfigVlan=""
		if OrderedListEquipment:
			finish_wo_break=False
			for equipement__ in OrderedListEquipment:
				try:
					entry_cur=self.vlans_DC[equipement__][vlan__]
					if entry_cur['mode']=='fabricpath':
						ConfigVlan="vlan "+vlan__+'\n'
						ConfigVlan+=" mode "+entry_cur['mode']+'\n'
						if entry_cur['name']:
							ConfigVlan+=" name "+entry_cur['name']+'\n'
						break;
					finish_wo_break=True
				except KeyError:
					pass
		
		else:
			for equipement__ in random.shuffle(self.vlans_FP.keys()):
				try:
					entry_cur=self.vlans_DC[equipement__][vlan__]
					if entry_cur['mode']=='fabricpath':
						ConfigVlan="vlan "+vlan__+'\n'
						ConfigVlan+=" mode "+entry_cur['mode']+'\n'
						if entry_cur['name']:
							ConfigVlan+=" name "+entry_cur['name']+'\n'
						break;
				except KeyError:
					pass
		
		finish_wo_break_2=False			
		if finish_wo_break:
			temp_list=list(self.vlans_FP.keys())
			random.shuffle(temp_list)
			for equipement__ in temp_list:
				try:
					entry_cur=self.vlans_DC[equipement__][vlan__]
					if entry_cur['mode']=='fabricpath':
						ConfigVlan="vlan "+vlan__+'\n'
						ConfigVlan+=" mode "+entry_cur['mode']+'\n'
						if entry_cur['name']:
							ConfigVlan+=" name "+entry_cur['name']+'\n'
						break;
						finish_wo_break_2=True
				except KeyError:
					pass
					
		if finish_wo_break_2:
			pdb.set_trace()
				
								
		return ConfigVlan
		
	def initConfigPatch(self,OrderedListEquipment=[]):
	
		ConfigPatch={}
		
		for vlan__ in self.vlans_FP_missing.keys():
			ConfigVlanCur=self.getConfVlan(vlan__,OrderedListEquipment)
			for equipement__ in self.vlans_FP_missing[vlan__]:
				if equipement__ not in ConfigPatch.keys():
					ConfigPatch[equipement__]=ConfigVlanCur+'\n'
				else:
					ConfigPatch[equipement__]+=ConfigVlanCur+'\n'
		
		return ConfigPatch
		
	def diff(self,host_old,host_cible):
	
		vlan_to_suppress=[]
		
		try:
			vlans_old=self.vlans_DC[host_old]
		except  KeyError:
			print("Il faut recuperer la config de "+host_old)
			sys.exit(2)
		try:
			vlans_cible=self.vlans_DC[host_cible]
		except  KeyError:
			print("Il faut recuperer la config de "+host_cible)
			sys.exit(3)
			
		for vlan__ in vlans_old.keys():
			if vlan__ not in vlans_cible.keys():
				vlan_to_suppress.append(vlan__)
				
				
		return vlan_to_suppress
		
	def check_vlan_presence(self,host_old,host_cible,nat_file):
	
		vlans_warning=[]
		try:
			vlans_old=self.vlans_DC[host_old]
		except  KeyError:
			print("Il faut recuperer la config de "+host_old)
			sys.exit(2)
		try:
			vlans_cible=self.vlans_DC[host_cible]
		except  KeyError:
			print("Il faut recuperer la config de "+host_cible)
			sys.exit(3)
			
		vlans_correspondance=initVlanNat(nat_file)
		
		for vlan__ in vlans_old.keys():
			if vlan__ in vlans_correspondance.keys():
				vlan__cur=vlans_correspondance[vlan__]
			else:
				vlan__cur=vlan__
			if vlan__cur not in vlans_cible.keys():
				vlans_warning.append(vlan__cur)
				
		return vlans_warning
		
		
	def deep_diff(self,host_old,host_cible,nat_file):
	
		vlan_to_suppress=[]
		vlans_correspondance=initVlanNat(nat_file)
		
		try:
			vlans_old=self.vlans_DC[host_old]
		except  KeyError:
			print("Il faut recuperer la config de "+host_old)
			sys.exit(2)
		try:
			vlans_cible=self.vlans_DC[host_cible]
		except  KeyError:
			print("Il faut recuperer la config de "+host_cible)
			sys.exit(3)
			
		for vlan__ in vlans_old.keys():
			if vlan__ not in vlans_cible.keys():
				vlan_to_suppress.append(vlan__)
				if vlan__ not in vlans_correspondance.keys():
					print('WARNING:'+vlan__+" NOT MAPPED AND WILL BR SUPPRESS")
				
				
		return vlan_to_suppress
	
			
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--repertoire",action="store",help="repertoire contenant les configurations sh run")
	parser.add_argument("-d", "--destination",action="store",help="repertoire contenant les configurations correctives")
	
	args = parser.parse_args()
	
	if args.repertoire:
		DC_vlan=ExtractInfoVlan(args.repertoire)
		
		#print(DC_vlan)
		
		DC_vlan.setVlanFP()
		
		#print(DC_vlan.getVlanFP())
		
		DC_vlan.setVlanFP_missing()
		
		print(DC_vlan.getVlanFP_missing())
		
		ConfigPatch=DC_vlan.initConfigPatch(['SC2ASV-CDN-CFD-VDC02','SC1STX-CDN-CFD-VDC02','SC1STX-CDN-CFD2-VDC02','SC2CLK-CDN-CFD-VDC02','SC1STX-CDN-L2DCI-VDC03','SC2ASV-CDN-L2DCI-VDC03'])
		
	if args.destination:
		if not os.path.exists(args.destination):
			os.makedirs(args.destination)
			
			for equipement__ in ConfigPatch:
				writeConfig(ConfigPatch[equipement__],args.destination+"/"+equipement__+'.CFG')

		
		

			
