#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import csv
import argparse
import io
import pdb
from ParsingShow  import ParseShNextPo, ParseShFexString
from connexion import *
import re
import sys

MODEL_CONFIG_N5K_INT_ACCESS="""!
interface <INTERFACE>
 description <DESCRIPTION>
 switchport access vlan <VLAN>
 spanning-tree port type edge
 no snmp trap link-status
"""


MODEL_CONFIG_N5K_INT_TRUNK="""!
interface <INTERFACE>
 description <DESCRIPTION>
 switchport mode trunk
 switchport trunk allowed vlan <VLAN_LIST>
 spanning-tree port type edge trunk
 no snmp trap link-status
"""

MODEL_CONFIG_N5K_INT_PO_TRUNK="""!
interface port-channel<POID>
 description <DESCRIPTION>
 switchport mode trunk
 switchport trunk allowed vlan <VLAN_LIST>
 spanning-tree port type edge trunk
 vpc <POID>
"""

MODEL_CONFIG_N5K_INT_PO_ACCESS="""!
interface port-channel<POID>
 description <DESCRIPTION>
 switchport access vlan <VLAN>
 spanning-tree port type edge
 no snmp trap link-status
 vpc <POID>
"""

MODEL_CONFIG_N5K_INT_PO_TRUNK_WO_VPC="""!
interface port-channel<POID>
 description <DESCRIPTION>
 switchport mode trunk
 switchport trunk allowed vlan <VLAN_LIST>
 spanning-tree port type edge trunk
"""

MODEL_CONFIG_N5K_INT_PO_ACCESS_WO_VPC="""!
interface port-channel<POID>
 description <DESCRIPTION>
 switchport access vlan <VLAN>
 spanning-tree port type edge
 no snmp trap link-status
"""

MODEL_CONFIG_N5K_INT_ETH_PO="""!
interface <INTERFACE>
 description <DESCRIPTION>
 channel-group <POID> mode active
"""

MODEL_CONFIG_N5K_INT_ETH_PO_ON="""!
interface <INTERFACE>
 description <DESCRIPTION>
 channel-group <POID>
"""

class NextPo(object):
	
	def __init__(self,FirstPo):
		self.Po=str(int(FirstPo)-1)
		
	def __next__(self):
		Po_int=int(self.Po)
		Po_int+=1
		
		self.Po=str(Po_int)
		
		return  self.Po
	
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
	
def testVpc(Macs,PoID,equipement):

	other_equipement=get_other_equipement(equipement)
	#pdb.set_trace()
	if not Macs[equipement][PoID]==Macs[other_equipement][PoID]:
		pass
	
	
	return Macs[equipement][PoID]==Macs[other_equipement][PoID]
	
def testInterfaceFex(interface__):
	result=False
	#pdb.set_trace()
	if re.match('[Ee]+t+h+1[0-9][0-9]/1/[0-9]',interface__):
		result=True
		
	return result
		
def get_other_equipement(equipement__):
	suffixe=equipement__[:-1]
	id=equipement__[-1:]
	
	if id=='1':
		other_id="2"
	elif id=='2':
		other_id="1"
	else:
		pdb.set_trace()
		
	other_equipement=suffixe+other_id
	
	return other_equipement
	
def get_prefix_equipement(equipment__):
	return equipment__[:-1]
	
def get_first_equipement(equipement__):
	suffixe=equipement__[:-1]
	id=equipement__[-1:]
	resultat=None
	if id=='1':
		resultat=equipement__
	elif id=='2':
		other_id="1"
		resultat=suffixe+other_id
	else:
		pdb.set_trace()
		
	return resultat
	
def getIntVpc(Macs,PoID,equipement):

	resultat=None
	suffixe=equipement[:-1]
	id=equipement[-1:]
	
	if id=='1':
		other_id="2"
	elif id=='2':
		other_id="1"
		
	other_equipement=suffixe+other_id
	
	if Macs[equipement][PoID][1]==Macs[other_equipement][PoID][1]:
		resultat={equipement:{PoID:Macs[other_equipement][PoID]} }
	
	return resultat	
	
def getFirstPo(equipment__):

	PoID=None
	
	con_get_NextPo_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+"_shNextPo_"+equipment__.lower()+".log","TMP","shNextPo",timeout=300,verbose=False)
	PoID=con_get_NextPo_cur.launch_withParser(ParseShNextPo)
	# try:
	# 	con_get_NextPo_cur=connexion(equipement(equipement__),None,None,None,'SSH',"TMP/"+"_shNextPo_"+equipement__.lower()+".log","TMP","shNextPo",timeout=300,verbose=False)
	# 	PoID=con_get_NextPo_cur.launch_withParser(ParseShNextPo)
	# except Exception as e:
	# 	print("Erreur Connexion...")
	# 	print((str(e)))
	# 	sys.exit(2)
		
	return PoID
	
def getTypeFex(equipment__1,equipment__2):
	TYPE=None
	con_get_fex__1=connexion(equipement(equipment__1),None,None,None,'SSH',"TMP/"+equipment__1+"_shFex_"+equipment__1.lower()+".log","TMP","sh fex",timeout=300,verbose=False)
	con_get_fex__2=connexion(equipement(equipment__2),None,None,None,'SSH',"TMP/"+equipment__2+"_shFex_"+equipment__2.lower()+".log","TMP","sh fex",timeout=300,verbose=False)
	Fex_lst__1=con_get_fex__1.launch_withParser(ParseShFexString)
	Fex_lst__2=con_get_fex__2.launch_withParser(ParseShFexString)
	
	print(Fex_lst__1)
	print(Fex_lst__2)
	
	if Fex_lst__1:
		FirstFexId=list(Fex_lst__1.keys())[0]
		if Fex_lst__1[FirstFexId][3] == Fex_lst__2[FirstFexId][3]:
			TYPE="DUAL_HOMED_FEX"
		else:
			TYPE="CLASSICAL_FEX"
			
	print(TYPE)
	
	return TYPE
	

def getTypePo(Po_dict,PoID,type_fex="CLASSICAL_FEX",):

	#pdb.set_trace()
	Interface_Dict=Po_dict[PoID][PoID]
	Type=None
	if len(Interface_Dict.keys()) == 2 and type_fex=="CLASSICAL_FEX":
		Type='VPC_Po_to_Servers'
	elif len(Interface_Dict.keys()) == 2 and type_fex=="DUAL_HOMED_FEX":
		Type='Non_VPC_Po_to_Servers'
	elif len(Interface_Dict.keys()) == 1:
		Type='Non_VPC_Po_to_Servers'
	else:
		print("Type Po non pris en charge")
		sys.exit(4)
		
	return Type
	
def init_iter_po(Pos__):
	FirstPo={}
	IterPo={}
	#print(str(IterPo))
	for equipement_ in Pos__.keys():
		#pdb.set_trace()
		Po_cur=getFirstPo(equipement_)
		FirstPo[equipement_]=Po_cur
		IterPo[equipement_]={}
		for TypePo in Po_cur.keys():
			IterPo[equipement_][TypePo]=NextPo(Po_cur[TypePo])
		
	#print(str(IterPo))
	return IterPo
	
def init_po(Pos__,Macs__):
	
	
		
	ListMac_traite={}
	ListMac_traite_human={}
	
	#pdb.set_trace()
	
	temp_poID={}
	temp_poID_incr=NextPo('0')
	for equipement__ in Macs__.keys():
		for PoID in Macs__[equipement__]:
			Interface_Mac_cur_Liste=Macs__[equipement__][PoID]
			
			for Interface_cur,Mac_cur in Interface_Mac_cur_Liste:
				Mac_cur_str=str(Mac_cur)
				if Mac_cur_str not in ListMac_traite:
					temp_PoID_cur=temp_poID_incr.__next__()
					temp_poID[Mac_cur_str]=temp_PoID_cur
					try:
						
						if equipement__ in ListMac_traite[Mac_cur_str][temp_PoID_cur]:
							ListMac_traite[Mac_cur_str][temp_PoID_cur][equipement__].append(Interface_cur)
							ListMac_traite_human[temp_PoID_cur][temp_PoID_cur][equipement__].append(Interface_cur)
						else:
							ListMac_traite[Mac_cur_str][temp_PoID_cur][equipement__]=[Interface_cur]
							ListMac_traite_human[temp_PoID_cur][temp_PoID_cur][equipement__]=[Interface_cur]
					except KeyError as e:
						#pdb.set_trace()
						#print(str(e))
						try:
							ListMac_traite[Mac_cur_str]={temp_poID[Mac_cur_str]:{equipement__:[Interface_cur]}}
							ListMac_traite_human[temp_poID[Mac_cur_str]]={temp_poID[Mac_cur_str]:{equipement__:[Interface_cur]}}
						except Error as e:
							#pdb.set_trace()
							print('Coucou')
							print(str(e))
	
						
				else:
					try:
						#pdb.set_trace()
						if equipement__ in ListMac_traite[Mac_cur_str][temp_poID[Mac_cur_str]]:
							ListMac_traite[Mac_cur_str][temp_poID[Mac_cur_str]][equipement__].append(Interface_cur)
							ListMac_traite_human[temp_poID[Mac_cur_str]][temp_poID[Mac_cur_str]][equipement__].append(Interface_cur)
						else:
							ListMac_traite[Mac_cur_str][temp_poID[Mac_cur_str]][equipement__]=[Interface_cur]
							ListMac_traite_human[temp_poID[Mac_cur_str]][temp_poID[Mac_cur_str]][equipement__]=[Interface_cur]
					except KeyError as e:
						ListMac_traite[Mac_cur_str][temp_poID[Mac_cur_str]]={equipement__:[Interface_cur]}
						ListMac_traite_human[temp_poID[Mac_cur_str]][temp_poID[Mac_cur_str]]={equipement__:[Interface_cur]}
						print('Coucou2')
						print(str(e))
	
						
			
	# print(str(ListMac_traite))
	# print(str(temp_poID))
	# print("\n\n")
	print('STR_LISTE_MAC_HUMAN:'+str(ListMac_traite_human))
	
	return sort_dict(ListMac_traite_human)

def init_po_id_fex_dual_homed(Po__,id_initiale):
	dict_interface_poID={}
	NEXT_PO=NextPo(id_initiale)
	for id__ in Po__.keys():
		for id___ in Po__[id__].keys():
			for equipement__ in Po__[id__][id___].keys():
				#pdb.set_trace()
				if str((get_prefix_equipement(equipement__), Po__[id__][id___][equipement__][0])) not in dict_interface_poID.keys() and not testInterfaceFex(Po__[id__][id___][equipement__][0]):
					PO_CUR=NEXT_PO.__next__()
					dict_interface_poID[str((get_prefix_equipement(equipement__), Po__[id__][id___][equipement__][0]))]=PO_CUR
					dict_interface_poID[str((get_prefix_equipement(equipement__), Po__[id__][id___][equipement__][1]))]=PO_CUR
					
	print('dict_interface_poID:'+str(dict_interface_poID))
		
	return dict_interface_poID
		
def get_po_id_fex(dict_interface_po_fex,equipement,interface)
		return dict_interface_po_fex[str((equipement,interface))]
		
def sort_dict(dict__):
	
	result={}
	sort_keys=sorted(dict__.keys())
	for key__ in sort_keys:
		result[key__]=dict__[key__]
		
	return result
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-i","--interface",action="store",help="Fichier contenant les informations sur les interfaces",required=True,default="EXCEL/LOT6-ODIN-Vague-3-po-j12-correction-imp.csv")
	parser.add_argument("-r","--repertoire",action="store",help="Rpertoire cible pour les configurations generees",required=True,default="CONFIG/LOT6-ODIN-Vague-3-po-j12-correction-imp")
	
	args = parser.parse_args()
	
	with open(args.interface, 'r') as csvfile:
		
		interfaces=[]
		spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
		for row in spamreader:
			interfaces.append(row)
		
	config={}
	config_cur=""
	
	Pos__={}
	Macs__={}

	
	Interface_Switchport={}
	Interface_Status={}
	Interface_Status_new={}
	Interface_Description={}
	Interface_DescriptionPo={}
	Interface_Po={}
	
	for interface in interfaces:
		#print(str(interface))
		#pdb.set_trace()
		equipement___=interface[2].replace(' ','')
		if equipement___ not in Interface_Switchport.keys():
			Interface_Switchport[equipement___]={}
			Interface_Status[equipement___]={}
			Interface_Status_new[equipement___]={}
			Interface_Description[equipement___]={}
			Interface_DescriptionPo[equipement___]={}
			Interface_Po[equipement___]={}
			
			
		int__=interface[3]
		description=interface[6]
		status=eval(interface[10])
		descriptionPo=interface[12]
		status_new=eval(interface[13])
		vlan="none"
		speed="none"
		speed_cfg="none"
		duplex="none"
		switchport=eval(interface[11])
		
		Interface_Switchport[equipement___][int__]=switchport
		Interface_Status[equipement___][int__]=status
		Interface_Status_new[equipement___][int__]=eval(interface[13])
		Interface_Description[equipement___][int__]=description
		Interface_DescriptionPo[equipement___][int__]=descriptionPo
		Interface_Po[equipement___][int__]=eval(interface[9])
		
		PoConfig=eval(interface[9])
		try:
			vlan=status[2]
			status__=status[0]
			speed=status[4]
			duplex=status[3]
			type_switchport=switchport[1]
			vlan_trunk=switchport[4]
			speed_new=status_new[4]
		except IndexError as E:
			print("Erreur:"+str(interface))
			print(E)
		
		
		if type_switchport == 'static access' or type_switchport == 'access' or type_switchport == 'down':
			type_sw_cur='ACCESS'
		elif type_switchport == 'trunk':
			type_sw_cur='TRUNK'
		
		if PoConfig == None:
			if type_sw_cur=='ACCESS':
				
	
				LISTE_PARAM_N5K=(('INTERFACE',int__),
								('DESCRIPTION',description),
								('VLAN',vlan))
				
				config_cur=configTemplate(MODEL_CONFIG_N5K_INT_ACCESS).replace(LISTE_PARAM_N5K)
				#print(config_cur)
			elif type_sw_cur=='TRUNK':
				LISTE_PARAM_N5K=(('INTERFACE',int__),
								('DESCRIPTION',description),
								('VLAN_LIST',vlan_trunk))
				
				config_cur=configTemplate(MODEL_CONFIG_N5K_INT_TRUNK).replace(LISTE_PARAM_N5K)

				
			try:
				config[equipement___]=config[equipement___]+config_cur
			except KeyError:
				config[equipement___]=config_cur
				
			if status_new[1]=='sfpInvali':
				config[equipement___]+=" speed 1000\n"

				
			
		else:
			Po_id_cur=PoConfig[0]
			try:
				Pos__[equipement___]
			except KeyError:
				Pos__[equipement___]={}
				
			try:
				Pos__[equipement___][Po_id_cur].append(int__)
			except KeyError:
				Pos__[equipement___][Po_id_cur]=[int__]	

			Mac_cur=(int__,eval(interface[7]))
			try:
				Macs__[equipement___]
			except KeyError:
				Macs__[equipement___]={}
			
			try:
				Macs__[equipement___][Po_id_cur].append(Mac_cur)
			except KeyError:
				Macs__[equipement___][Po_id_cur]=[Mac_cur]
			

	liste_hostname_done=[]
	result_fex={}
	for hostname  in Macs__.keys():
		other_hostname=get_other_equipement(hostname)
		if hostname not in liste_hostname_done and other_hostname not in liste_hostname_done:
			liste_hostname_done.append(hostname)
			liste_hostname_done.append(other_hostname)
			result_fex[get_first_equipement(hostname)]=getTypeFex(hostname,other_hostname)
		
	print(result_fex)
	
	for hostname  in Macs__.keys():
		try:
			if result_fex[hostname]=="CLASSICAL_FEX":
				for Poid in Macs__[hostname]:
					test=testVpc(Macs__,Poid,hostname)
					print("Recherche Po en vPC pour "+hostname+" "+Poid+":"+str(test))
			elif result_fex[hostname]=="DUAL_HOMED_FEX":
				for Poid in Macs__[hostname]:
					test=False
					print("Po Srv non en VPC pour "+hostname+" "+Poid+":"+str(test))
		except KeyError as Err__:
			print(Err__)
			
			
			
		
			
	Dict_Po=init_po(Pos__,Macs__)
	
	IterPo__=init_iter_po(Pos__)
	
	init_po_id(Dict_Po,400)
	Po_fex_cur={}
	Po_inter_used={}
	for PoId in sorted(Dict_Po.keys()):
		print("POID:"+str(sorted(Dict_Po[PoId].keys())))
		for PoId__ in sorted(Dict_Po[PoId].keys()):
			#pdb.set_trace()
			for equipement__ in sorted(Dict_Po[PoId][PoId__].keys()):
				type_fex=result_fex[get_first_equipement(equipement__)]
				POID__=IterPo__[equipement__][getTypePo(Dict_Po,PoId__,type_fex)].__next__()
				print("POID__:"+equipement__+":"+POID__)
				print("INTERFACE:"+str(sorted(Dict_Po[PoId][PoId__][equipement__])))
				for interface__ in sorted(Dict_Po[PoId][PoId__][equipement__]):
					po_status=Interface_Status[equipement__][interface__]
					po_switchport=Interface_Switchport[equipement__][interface__]
					po_description=Interface_DescriptionPo[equipement__][interface__]
					LISTE_PARAM_N5K=(('INTERFACE',interface__),
							('DESCRIPTION',Interface_Description[equipement__][interface__]),
							('POID',POID__))
					print(Interface_Po[equipement__][interface__])
					if Interface_Status_new[equipement__][interface__][1]=='sfpInvali':
						speed=" speed 1000\n"
					else:
						speed=None
					type_Po=Interface_Po[equipement__][interface__][2]
					if type_Po=='None':
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_ETH_PO_ON).replace(LISTE_PARAM_N5K)
					else:
						print(type_Po)
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_ETH_PO).replace(LISTE_PARAM_N5K)
					try:
						config[equipement__]=config[equipement__]+config_cur
					except KeyError:
						config[equipement__]=config_cur
					Po_fex_cur[POID__]=testInterfaceFex(interface__)
				#pdb.set_trace()	
				
				print(Po_fex_cur)
				type_sw_switchport=po_switchport[1]
				if type_sw_switchport == 'static access' or type_sw_switchport == 'access' or type_sw_switchport == 'down':
					type_sw_cur='ACCESS'
				elif type_sw_switchport == 'trunk':
					type_sw_cur='TRUNK'		
					
				#pdb.set_trace()
				if type_sw_cur=='ACCESS':
					vlan=po_status[2]
					LISTE_PARAM_N5K=(('POID',POID__),
									('DESCRIPTION',po_description),
									('VLAN',vlan))
					if type_fex == "CLASSICAL_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_ACCESS).replace(LISTE_PARAM_N5K)
					elif type_fex == "DUAL_HOMED_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_ACCESS_WO_VPC).replace(LISTE_PARAM_N5K)
				#print(config_cur)
				elif type_sw_cur=='TRUNK':
					vlan_trunk=po_switchport[4]
					LISTE_PARAM_N5K=(('POID',POID__),
									('DESCRIPTION',po_description),
									('VLAN_LIST',vlan_trunk))
				
					if type_fex == "CLASSICAL_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_TRUNK).replace(LISTE_PARAM_N5K)	
					elif type_fex == "DUAL_HOMED_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_TRUNK_WO_VPC).replace(LISTE_PARAM_N5K)
					if speed:
						config_cur+=speed
						
				try:
					config[equipement__]=config[equipement__]+config_cur
				except KeyError:
					config[equipement__]=config_cur
				
				
				
	repertoire_cur=args.repertoire
	if not os.path.exists(repertoire_cur):
		os.makedirs(repertoire_cur)
							
	for equipement___ in config.keys():
		file_cur=repertoire_cur+"/"+equipement___+".cfg"
		writeConfig(config[equipement___],file_cur)
		print(equipement___)
		print(config[equipement___])
		
	#print(str(Pos__))
	#print(str(Macs__))
	
	
				
			
			
		