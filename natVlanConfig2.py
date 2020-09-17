#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import csv
import argparse
import io
import pdb
from ParsingShow  import ParseStatusCisco, ParseSwitchPortString , ParsePortChannelCisco , getLongPort , getShortPort , ParseRunInterface
from connexion import *
import re
import sys
import os
from ParseVlanListe import vlan , liste_vlans

MODEL_CONFIG_N5K_INT_ACCESS="""!
interface <INTERFACE>
 switchport access vlan <VLAN>
 spanning-tree port type edge
"""


MODEL_CONFIG_N5K_INT_TRUNK="""!
interface <INTERFACE>
 switchport trunk allowed vlan <VLAN_LIST>
 spanning-tree port type edge trunk
"""

MODEL_CONFIG_N5K_INT_PO_TRUNK="""!
interface port-channel<POID>
 switchport trunk allowed vlan <VLAN_LIST>
 spanning-tree port type edge trunk
"""

MODEL_CONFIG_N5K_INT_PO_ACCESS="""!
interface port-channel<POID>
 switchport access vlan <VLAN>
 spanning-tree port type edge
"""



	
class configTemplate(object):
	"Classe template de configuration"
	def __init__(self,str):
		self.template=str
		
	def replace(self,liste_parametre):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		
		resultat=self.template
		for (param,valeur) in liste_parametre:
			#print("PARAM:{0} VALEUR:{1}".format(param,valeur))
			try:
				resultat=resultat.replace("<"+param+">",valeur)
			except:
				#pass
				pdb.set_trace()
			
		return resultat


def writeConfig(config_str,fichier):
	
	with open(fichier,'w+') as Configfile:
		Configfile.write(config_str)
	return None
	
	
def getStatus(equipment__):

	Status=None
	
	con_get_Status_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shintstatus_.log","TMP","show interface status",timeout=300,verbose=False)
	Status=con_get_Status_cur.launch_withParser(ParseStatusCisco)
		
	return Status
	
def getSwitchport(equipment__):

	Switchport=None
	
	con_get_Switchport_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shintswitchport.log","TMP","show interface switchport",timeout=300,verbose=False)
	Switchport=con_get_Switchport_cur.launch_withParser(ParseSwitchPortString)
	
		
	return Switchport
	
def getRunningInterface(equipment__):

	Interface=None
	
	con_get_Interface_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log","TMP","show run",timeout=300,verbose=False)
	Interface=con_get_Interface_cur.launch_withParser(ParseRunInterface)
	
		
	return Interface
	
def getPortChannel(equipment__):

	Portchannel=None
	
	con_get_Portchannel_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shport_channel_summary.log","TMP","show port-channel summary",timeout=300,verbose=False)
	Portchannel=con_get_Portchannel_cur.launch_withParser(ParsePortChannelCisco)
	
		
	return Portchannel
	
def getDecomConfig(status__,channel__,interfaces__rb={},interfaces_config={}):
	
	resultat={}
	

	for equipement__ in status__.keys():
		for interface__ in status__[equipement__]:
			#print(interface__+"=="+status__[equipement__][interface__][1]+"==")
			if isinstance(interfaces_config[equipement__]['interface '+getLongPort(interface__)],list):
				if re.search('shutdown',interfaces_config[equipement__]['interface '+getLongPort(interface__)][0]):
					continue
			interfaces_config[equipement__]['interface '+getLongPort(interface__)]
			if status__[equipement__][interface__][1] in ['notconnec','disabled','xcvrInval','noOperMem'] and interfaces_config[equipement__]['interface '+getLongPort(interface__)]:
				if not re.search('^Po',interface__):
					if equipement__  in resultat.keys():
						resultat[equipement__]+="default interface "+interface__+"\n"
						if equipement__ not in interfaces__rb.keys():
							interfaces__rb[equipement__]=[interface__]
						else:
							interfaces__rb[equipement__].append(interface__)
							
					else:
						resultat[equipement__]="default interface "+interface__+"\n"
		
	for equipement_ in channel__.keys():
		for po__ in channel__[equipement_]:
			if testPoDown(po__[3]):
				if equipement__  in resultat.keys():
					resultat[equipement_]+="no interface Po"+po__[0]+"\n"
				else:
					resultat[equipement_]="no interface Po"+po__[0]+"\n"
				if equipement_ not in interfaces__rb.keys():
					interfaces__rb[equipement_]=["Po"+po__[0]]
				else:
					interfaces__rb[equipement_].append("Po"+po__[0])

		
	return resultat
	
def testPoDown(Channel__):
	Test=True
	for interface in Channel__:
		try:
			if interface[1]!='D':
				Test=False
		except KeyError:
			pass
			
	return Test
	
def getInterfacePo(channel__):
	resultat={}
	for equipement_ in channel__.keys():
		resultat[equipement_]=[]
		for po__ in channel__[equipement_]:
			try:
				for int__ in  po__[3]:
					interface_cur=int__[0]
					if interface_cur not in resultat:
						resultat[equipement_].append(interface_cur)
			except KeyError:
				pass
	return resultat
	
		
def sort_dict(dict__):
	
	result={}
	sort_keys=sorted(dict__.keys())
	for key__ in sort_keys:
		result[key__]=dict__[key__]
		
	return result
	
def initVlanNat(fichier):
	resultat={}
	with open(fichier,'r') as file__:
		for ligne in file__:
			ligne_col=ligne.split()
			try:
				resultat[ligne_col[0]]=ligne_col[1]
			except ValueError:
				pass
			except KeyError:
				pass

	return resultat
	
def getRollback(port_channel,interfaces__rb,interfaces_in_po,interfaces_config):

	resultat={}
	liste_po={}
	
	for equipement__ in interfaces__rb.keys():
		print(equipement__ )
		resultat[equipement__]=""
		liste_po[equipement__]=[]
		for interface__ in interfaces__rb[equipement__]:
			if re.search('^Po',interface__):
				liste_po[equipement__].append(interface__)
			else:
				resultat[equipement__]+="interface "+interface__+'\n'
				if interfaces_config[equipement__]["interface "+getLongPort(interface__) ]:
					resultat[equipement__]+=''.join([ ligne for ligne in interfaces_config[equipement__]["interface "+getLongPort(interface__) ] ] )

	
	for equipement__ in liste_po.keys():
		for po__ in liste_po[equipement__]:
			resultat[equipement__]+="interface "+po__+'\n'
			if interfaces_config[equipement__]["interface "+getLongPort(po__) ]:
				resultat[equipement__]+=''.join([ ligne for ligne in interfaces_config[equipement__]["interface "+getLongPort(po__) ] ] )
		
	
	return resultat
	
	
def getNewconfig(switchport__,status__,channel__,vlans__,interfaces__rb,interfaces_in_po):
	resultat={}
	for equipement__ in status__.keys():
		resultat[equipement__]=""
		for interface__ in status__[equipement__]:
			#print(interface__+"=="+status__[equipement__][interface__][1]+"==")
			if True:
				if interface__ not in interfaces_in_po[equipement__] and not re.search('^Po',interface__):
					try:
						switchport_cur=switchport__[equipement__][getLongPort(interface__)]
					except KeyError:
						print("Warning: KeyError SwxitchPort:"+getLongPort(interface__))
						continue
					type_int_cur=switchport_cur[1]
					if re.search('access',type_int_cur):
						vlan__cur=switchport_cur[2]
						if vlan__cur in vlans__.keys() and not ( vlan__cur=='1' and status__[equipement__][interface__][1] in ['notconnec','disabled','xcvrInval','noOperMem','sfpAbsent'] ):
							new_vlan_cur=vlans__[vlan__cur]
							resultat[equipement__]+="interface "+interface__+'\n'
							resultat[equipement__]+=" switchport access vlan "+new_vlan_cur+'\n'
							if equipement__ not in interfaces__rb.keys():
								interfaces__rb[equipement__]=[interface__]
							else:
								interfaces__rb[equipement__].append(interface__)
					elif re.search('trunk',type_int_cur):
						test_nat=False
						vlans_cur=switchport_cur[4]
						new_vlans_cur=[]
						#pdb.set_trace()
						for vlan__ in liste_vlans(vlans_cur).explode():
							try:
								if vlan(int(vlan__)) in liste_vlans(",".join(vlans__.keys())):
									test_nat=True
							except ValueError:
								pdb.set_trace()
						if test_nat:
							for vlan__ in liste_vlans(vlans_cur).explode():
								if vlan(int(vlan__)) in liste_vlans(",".join(vlans__.keys())):
									new_vlans_cur.append(vlans__[vlan__])
								else:
									new_vlans_cur.append(vlan__)
							resultat[equipement__]+="interface "+interface__+'\n'
							new_vlans_cur.sort(key=int)
							resultat[equipement__]+=" switchport trunk allowed vlan "+",".join(new_vlans_cur)+'\n'
							if equipement__ not in interfaces__rb.keys():
								interfaces__rb[equipement__]=[interface__]
							else:
								interfaces__rb[equipement__].append(interface__)
	
	for equipement_ in channel__.keys():
		for po__ in channel__[equipement_]:
		
			if not testPoDown(po__[3]):
				try:
					switchport_cur=switchport__[equipement__][getLongPort("Po"+po__[0])]
				except KeyError:
					print("Warning: KeyError SwitchPort:"+getLongPort("Po"+po__[0]))
					continue
				type_int_cur=switchport_cur[1]
				if re.search('access',type_int_cur):
					vlan__cur=switchport_cur[2]
					if vlan__cur in vlans__.keys():
						new_vlan_cur=vlans__[vlan__cur]
						resultat[equipement_]+="interface "+"Po"+po__[0]+'\n'
						resultat[equipement_]+=" switchport access vlan "+new_vlan_cur+'\n'
						if equipement_ not in interfaces__rb.keys():
							interfaces__rb[equipement_]=["Po"+po__[0]]
						else:
							interfaces__rb[equipement_].append("Po"+po__[0])
				elif re.search('trunk',type_int_cur):
					test_nat=False
					vlans_cur=switchport_cur[4]
					new_vlans_cur=[]
					#pdb.set_trace()
					for vlan__ in liste_vlans(vlans_cur).explode():
						if vlan(int(vlan__)) in liste_vlans(",".join(vlans__.keys())):
							test_nat=True
					if test_nat:
						for vlan__ in liste_vlans(vlans_cur).explode():
							if vlan(int(vlan__)) in liste_vlans(",".join(vlans__.keys())):
								new_vlans_cur.append(vlans__[vlan__])
							else:
								new_vlans_cur.append(vlan__)
						new_vlans_cur.sort(key=int)
						resultat[equipement_]+="interface "+"Po"+po__[0]+'\n'
						resultat[equipement_]+=" switchport trunk allowed vlan "+",".join(new_vlans_cur)+'\n'
						if equipement_ not in interfaces__rb.keys():
							interfaces__rb[equipement_]=["Po"+po__[0]]
						else:
							interfaces__rb[equipement_].append("Po"+po__[0])
					
	return resultat
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-e","--equipements",action="store",help="Liste Equipement",required=True)
	parser.add_argument("-r","--repertoire",action="store",help="Répertoire cible pour les configurations generees",required=True)
	parser.add_argument("-t","--translation",action="store",help="Fichier contenant les translations de vlan",required=True)
	
	args = parser.parse_args()
	
	"Ajout de répertoires"
	if not os.path.exists(args.repertoire):
		os.makedirs(args.repertoire)
	if not os.path.exists(args.repertoire+"/DECOM"):
		os.makedirs(args.repertoire+"/DECOM")
	if not os.path.exists(args.repertoire+"/ROLLOUT"):
		os.makedirs(args.repertoire+"/ROLLOUT")
	if not os.path.exists(args.repertoire+"/ROLLBACK"):
		os.makedirs(args.repertoire+"/ROLLBACK")
			
	config={}
	config_cur=""
	
	Pos__={}
	Macs__={}

	
	Interface_Switchport={}
	Interface_Status={}
	Interface_Portchannel={}
	Intercace_modifiees={}
	Vlans_correspondance={}
	Interface_Config={}
	
	equipements=args.equipements.split(":")

	
	for equipement__ in equipements:
		print("Récupération des données pour "+equipement__)
		status_cur=getStatus(equipement__)
		switchport_cur=getSwitchport(equipement__)
		portchannel_cur=getPortChannel(equipement__)
		interface_cur=getRunningInterface(equipement__)
		
		Interface_Status[equipement__]=status_cur
		Interface_Switchport[equipement__]=switchport_cur
		Interface_Portchannel[equipement__]=portchannel_cur
		Interface_Config[equipement__]=interface_cur
			
			
		
	#print(str(Interface_Status))
	#print(str(Interface_Switchport))
	#print(str(Interface_Portchannel))
	#print(str(Interface_Config))
	
	ConfigDecom=getDecomConfig(Interface_Status,Interface_Portchannel,Intercace_modifiees,Interface_Config)
	
	"Génération Configuration Décom"
	for equipement__ in ConfigDecom.keys():
		 writeConfig(ConfigDecom[equipement__],args.repertoire+"/DECOM/"+equipement__.upper()+".cfg")
		 
	
	Vlans_correspondance=initVlanNat(args.translation)
	
	Liste_interface_in_po=getInterfacePo(Interface_Portchannel)
	
	#print(str(Vlans_correspondance))
	print(str(Liste_interface_in_po))
	
	ConfigNew=getNewconfig(Interface_Switchport,Interface_Status,Interface_Portchannel,Vlans_correspondance,Intercace_modifiees,Liste_interface_in_po)
	ConfigRollback=getRollback(Interface_Portchannel,Intercace_modifiees,Liste_interface_in_po,Interface_Config)
	
	"Génération Configuration RollOut/Rollback"
	for equipement__ in ConfigNew.keys():
		 writeConfig(ConfigNew[equipement__],args.repertoire+"/ROLLOUT/"+equipement__.upper()+".cfg")
		 
	for equipement__ in ConfigRollback.keys():
		 writeConfig(ConfigRollback[equipement__],args.repertoire+"/ROLLBACK/"+equipement__.upper()+".cfg")
		
	print(str(Intercace_modifiees))
	for equip_ in Intercace_modifiees:
		print(len(Intercace_modifiees[equip_]))
	
	