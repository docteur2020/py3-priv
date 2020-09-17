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
from ParseVlanListe import vlan as Vlan , liste_vlans
import yaml

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
def test_interface_fex(interface__):
	resultat=False
	if re.search('Ethernet1[0-9][0-9]/[0-9]/[0-9]',interface__):
		resultat=True
	return resultat
	
def insert_native_vlan(string__,vlan__):
	resultat=io.StringIO()
	str__list=string__.split('\n')
	for ligne in str__list:
		if not re.search('switchport trunk allowed vlan',ligne):
			resultat.write(ligne+'\n')
		else:
			resultat.write(' switchport trunk native vlan '+vlan__+'\n')
			resultat.write(ligne+'\n')
	
	return resultat.getvalue()
		
def suppress_vlan_all(string__):
	resultat=io.StringIO()
	str__list=string__.split('\n')
	for ligne in str__list:
		if re.search('switchport trunk allowed vlan ALL',ligne):
			pass
		else:
			resultat.write(ligne+'\n')
	
	return resultat.getvalue()
class NextPo(object):
	
	def __init__(self,FirstPo):
		self.Po=str(int(FirstPo)-1)
		
	def __next__(self):
		Po_int=int(self.Po)
		Po_int+=1
		
		self.Po=str(Po_int)
		
		return  self.Po
		
class NextPos(object):

	def __init__(self,FirstPos):
		self.Pos={}
		
		for type_po in FirstPos.keys():
			self.Pos[type_po]=NextPo(FirstPos[type_po])
			
	def next_po(self,type_po):
		return  self.Pos[type_po].__next__()
		
class PortChannel(object):
	
	def __init__(self,equipement,liste_interface,id=0):
		self.equipement=equipement
		self.interfaces=liste_interface
		self.id=id
		self.interface_fex=test_interface_fex(liste_interface[0][1])
	
	def __str__(self):
		return self.equipement+":"+str(self.interfaces)+" id:"+self.id
		
	def __eq__(self,other):
		result=False
		if self.equipement==other.equipement and sorted(self.interfaces)==sorted(other.interfaces):
			result=True
			
	
		return result
			
	def testVPC(self,typeFex):
		result=False
		liste_eq_src=[]
		Test_VPC_Potentiel=False
		for interface__ in self.interfaces:
			if interface__[0] not in liste_eq_src:
				liste_eq_src.append(interface__[0])
		if len(liste_eq_src)>=2:
			Test_VPC_Potentiel=True
		if typeFex=="DUAL_HOMED_FEX" and self.interface_fex:
			result=False
		elif Test_VPC_Potentiel:
			result=True
			
		return result
			
	def TestInterfacePo(self,equipement__,interface__):
		resultat=False
		
		for int__ in self.interfaces:
			if (equipement,interface__)==int__:
				resultat=True
				break
				
		return resultat	
		
	def __contains__(self,interface):
		
		result=False
		
		for interface__ in self.interfaces:
			if interface__==self.interface[1]:
				result=True
			
		return result
		
		
class PortChannels(object):
	
	def __init__(self):
		self.liste=[]
		self.new_po={}
		self.new_poid={}
		
		
	def __contains__(self,portchannel):
		result=False
		for po in self.liste:
			if po == portchannel:
				result=True
			
		return result
		
	def add(self,portchannel):
		self.liste.append(portchannel)
		

		
	def __str__(self):
		affichage=""
		for po in self.liste:
			affichage+=po.__str__()+'\n'
			
		return affichage
		
	def TestInterfacePo(self,equipement__,interface__):
		resultat=False
		
		for po__ in self.liste:
			if po__.TestInterfacePo(equipement__,interface__):
				resultat=True
				break
				
		return resultat	
		
	def init_po_new(self,interfaces_old_new,types_fex,iterPo__):

		new_portchannels=[]
		
		print('interfaces_old_new:'+str(interfaces_old_new))
		
		for portchannel in self.liste:
			new_interfaces=[]
			Test_same_equipement=True
			Liste_new_equipement=[]
			Test_VPC_potentiel=False
			portchannel_new_cur=None
			
			Po__cur_dst=[]
			vpc_cur=False
			for interface__ in portchannel.interfaces:
				try:
					equipement_cur_new=interfaces_old_new[portchannel.equipement][interface__]['EQUIPEMENT']
					interface_cur_new=interfaces_old_new[portchannel.equipement][interface__]['INTERFACE']
					Po__cur_dst.append((equipement_cur_new,interface_cur_new))
					type_fex_cur=types_fex[equipement_cur_new]
					type_interface_fex_cur=testInterfaceFex(interface_cur_new)
					if equipement_cur_new not in Liste_new_equipement:
						Liste_new_equipement.append(equipement_cur_new)
					interface_id=interface__
				except KeyError as e:
					print("Warning:"+portchannel.equipement+" "+interface__+":interconnexion non prevue")
				
				
			if len(Liste_new_equipement) >= 2:
				Test_VPC_potentiel=True
				
			#initialisation du PoID
			
			print("po:", portchannel.__str__())
				
			
			if type_fex_cur=='CLASSICAL_FEX':
				Poid_cur=iterPo__[interfaces_old_new[portchannel.equipement][interface_id]['EQUIPEMENT']]['VPC_Po_to_Servers'].__next__()
				if Test_VPC_potentiel:
					vpc_cur=True
					for host__ in Po__cur_dst:
						new_portchannels.append(PortChannel(host__[0],Po__cur_dst,Poid_cur))
			
			elif type_fex_cur=='DUAL_HOMED_FEX':
				if type_interface_fex_cur:
					try:
						Poid_cur=iterPo__[interfaces_old_new[portchannel.equipement][interface_id]['EQUIPEMENT']]['Po_on_FEX'].__next__()
					except KeyError as e:
						print("bp1")
						print(e)

				else:
					try:
						Poid_cur=iterPo__[interfaces_old_new[portchannel.equipement][interface_id]['EQUIPEMENT']]['VPC_Po_to_Servers'].__next__()
						vpc_cur=True
					except KeyError as e:
						print("bp2")
						print(e)
		
			else:
				print('Mode non pris en charge')
				os.exit(30)
			
			if vpc_cur:
				for host__ in Po__cur_dst:
					new_portchannels.append(PortChannel(host__[0],Po__cur_dst,Poid_cur))
			else:
				portchannel_new_cur=PortChannel(equipement_cur_new,Po__cur_dst,Poid_cur)			
				new_portchannels.append(portchannel_new_cur)
		
		print('New Po')
		PoID_new={}
		Po_new={}
		

		#'initialisation de new_poid permet d\'avoir un id a partir de l\equipement et de l\'interface' 
		for po___ in new_portchannels:
			equipement_cur=po___.equipement
			if equipement_cur not in PoID_new.keys():
				PoID_new[equipement_cur]={}

			for interface_cur in po___.interfaces:
				PoID_new[equipement_cur][interface_cur[1]]=po___.id


				
		print('PoID_new:'+str(PoID_new))
		
		self.new_poid=PoID_new
		
		'initialisation de la liste des po  self.new_po' 
		
		#pdb.set_trace()
		
		for po___ in new_portchannels:
			equipement_cur=po___.equipement
			
			if equipement_cur not in Po_new.keys():
				Po_new[equipement_cur]={}
			
			for interface_cur in po___.interfaces:
				if po___.id not in Po_new[equipement_cur].keys():
					Po_new[equipement_cur][po___.id]=[]
					
				Po_new[equipement_cur][po___.id].append(interface_cur)
				
					
		print('Po_new:'+str(Po_new))
		
		self.new_po=Po_new
		
		return PoID_new
		
	
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
	if not Macs[equipement][PoID]==Macs[other_equipement][PoID]:
		pass
	
	
	return Macs[equipement][PoID]==Macs[other_equipement][PoID]
	
def testInterfaceFex(interface__):
	result=False
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
		
def get_po_id_fex(dict_interface_po_fex,equipement,interface):
		return dict_interface_po_fex[str((equipement,interface))]
		
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
	
def translate_vlan(vlan__,vlans__,host__):
	resultat=vlan__
	
	host__cur=host__.upper()
	if host__cur not in  vlans__.keys():
		print(host__cur," pas de translation")
		pdb.set_trace()
		return vlan__
		
	isliste=re.compile('-|,')
	if not isliste.search(vlan__):
		vlan__cur=vlan__
		if vlan__cur in vlans__[host__cur].keys():
			resultat=vlans__[host__cur][vlan__cur]

	else:
		test_nat=False
		vlans_cur=vlan__
		new_vlans_cur=[]
		for vlan___ in liste_vlans(vlans_cur).explode():
			try:
				if Vlan(int(vlan___)) in liste_vlans(",".join(vlans__[host__cur].keys())):
					test_nat=True
			except ValueError as e:
				pdb.set_trace()
				print(e)
			except TypeError as e:
				pdb.set_trace()
				print(e)
		if test_nat:
			for vlan___ in liste_vlans(vlans_cur).explode():
				if Vlan(int(vlan___)) in liste_vlans(",".join(vlans__[host__cur].keys())):
					new_vlans_cur.append(vlans__[host__cur][vlan___])
				else:
					new_vlans_cur.append(vlan___)
			new_vlans_cur.sort(key=int)
			resultat=",".join(new_vlans_cur)


	return resultat
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-i","--interface",action="store",help="Fichier contenant les informations sur les interfaces",required=True,default="EXCEL/LOT6-ODIN-Vague-3-po-j12-correction-imp.csv")
	parser.add_argument("-r","--repertoire",action="store",help="Rpertoire cible pour les configurations generees",required=True,default="CONFIG/LOT6-ODIN-Vague-3-po-j12-correction-imp")
	parser.add_argument("-t","--translation",action="store",help="Fichier yaml contanent la translation de Vlan ",required=False)
	
	
	args = parser.parse_args()
	
	with open(args.interface, 'r') as csvfile:
		
		interfaces=[]
		interfaces__2=[]
		spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
		for row in spamreader:
			interfaces.append(row)
			interfaces__2.append(row)
		
	Vlans_correspondance={}
	
	if args.translation:
		with open(args.translation, 'r' ) as model_yml:
			Vlans_correspondance = yaml.load(model_yml,Loader=yaml.SafeLoader)
		
	
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
	NewInterface__={}
	iter__Po__={}
	Interface_HostSrc={}
	
	portchannels__=PortChannels()
	
	for interface in interfaces:
		#print(str(interface))
		#pdb.set_trace()
		equipement___=interface[2].replace(' ','')
		old_equipement=interface[4].replace(' ','')
		
		if equipement___ not in Interface_Switchport.keys():
			Interface_Switchport[equipement___]={}
			Interface_Status[equipement___]={}
			Interface_Status_new[equipement___]={}
			Interface_Description[equipement___]={}
			Interface_DescriptionPo[equipement___]={}
			Interface_Po[equipement___]={}
			Interface_HostSrc[equipement___]={}
			
		if old_equipement not in NewInterface__.keys():
			NewInterface__[old_equipement]={}
		
		
		int__=interface[3]
		int__legacy=interface[5]
		description=interface[6]
		status=eval(interface[10])
		descriptionPo=interface[12]
		status_new=eval(interface[13])
		vlan="none"
		speed="none"
		speed_cfg="none"
		duplex="none"
		switchport=eval(interface[11])
		Interface_HostSrc[equipement___][int__]=old_equipement
		Interface_Switchport[equipement___][int__]=switchport
		Interface_Status[equipement___][int__]=status
		Interface_Status_new[equipement___][int__]=eval(interface[13])
		Interface_Description[equipement___][int__]=description
		Interface_DescriptionPo[equipement___][int__]=descriptionPo
		Interface_Po[equipement___][int__]=eval(interface[9])
		

		
		NewInterface__[old_equipement][int__legacy]=[equipement___,int__]
		
		Liste_Po_old=[]
		if Interface_Po[equipement___][int__]:
			portchannel__cur=PortChannel(old_equipement,[ interf__[0]  for interf__ in Interface_Po[equipement___][int__][3] ] , Interface_Po[equipement___][int__][0])
			if portchannel__cur not in portchannels__:
				portchannels__.add(portchannel__cur)

		
		PoConfig=eval(interface[9])
		try:
			vlan=status[2]
			if args.translation:
				vlan=translate_vlan(status[2],Vlans_correspondance,old_equipement)
			status__=status[0]
			speed=status[4]
			duplex=status[3]
			type_switchport=switchport[1]
			vlan_native=switchport[3]
			vlan_trunk=switchport[4]
			if args.translation:
				if switchport[4] != 'ALL':
					vlan_trunk=translate_vlan(switchport[4],Vlans_correspondance,old_equipement)
					if vlan_native!='1':
						vlan_native=translate_vlan(switchport[3],Vlans_correspondance,old_equipement)
			speed_new=status_new[4]
		except IndexError as E:
			print("Erreur:"+str(interface))
			print(E)
		
		
		if type_switchport == 'static access' or type_switchport == 'access':
			type_sw_cur='ACCESS'
		elif type_switchport == 'trunk':
			type_sw_cur='TRUNK'
		elif type_switchport == 'down':
			if switchport[4]!='ALL':
				type_sw_cur='TRUNK'
			else:
				type_sw_cur='ACCESS'
		
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
				
				if vlan_native == '1':
					config_cur=configTemplate(MODEL_CONFIG_N5K_INT_TRUNK).replace(LISTE_PARAM_N5K)
				else:
					config_cur= insert_native_vlan(configTemplate(MODEL_CONFIG_N5K_INT_TRUNK).replace(LISTE_PARAM_N5K),vlan_native)
					
				if vlan_trunk=='ALL':
					config_cur=suppress_vlan_all(configTemplate(MODEL_CONFIG_N5K_INT_TRUNK).replace(LISTE_PARAM_N5K))

				
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
			
	
	print('port_channel:'+str(portchannels__))
	
	# Traitement des Po
	
	Correspondance_old_new={}
	Correspondance_new_old={}
	if Macs__:
		liste_hostname_done=[]
		result_fex={}
		for hostname  in Macs__.keys():
			other_hostname=get_other_equipement(hostname)
			if hostname not in liste_hostname_done and other_hostname not in liste_hostname_done:
				liste_hostname_done.append(hostname)
				liste_hostname_done.append(other_hostname)
				result_fex[get_first_equipement(hostname)]=getTypeFex(hostname,other_hostname)
				result_fex[hostname]=result_fex[get_first_equipement(hostname)]
				result_fex[other_hostname]=result_fex[get_first_equipement(hostname)]
				
		# initialisation de la correspondance interface old et new simple.
		
		for interface2 in interfaces__2:
			old_equipement2=interface2[4].replace(' ','')
			int__legacy2=interface2[5]
			equipement___2=interface2[2].replace(' ','')
			int__2=interface2[3]
			try:
				if old_equipement2 not in Correspondance_old_new.keys():
					Correspondance_old_new[old_equipement2]={}
					Correspondance_old_new[old_equipement2][int__legacy2]={'EQUIPEMENT':equipement___2,'INTERFACE':int__2}
				else:
					Correspondance_old_new[old_equipement2][int__legacy2]={'EQUIPEMENT':equipement___2,'INTERFACE':int__2}
					
				if equipement___2 not in Correspondance_new_old.keys():
					Correspondance_new_old[equipement___2]={}
					Correspondance_new_old[equipement___2][int__2]={'EQUIPEMENT':old_equipement2,'INTERFACE':int__legacy2}
				else:
					Correspondance_new_old[equipement___2][int__2]={'EQUIPEMENT':old_equipement2,'INTERFACE':int__legacy2}
			except KeyError as e:
				print(e)

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
		print('Pos__:'+str(Pos__))
		print('Macs__:'+str(Macs__))
		print('Dict_Po:'+str(Dict_Po))
		
		IterPo__=init_iter_po(Pos__)
		
		#init_po_id_fex_dual_homed(Dict_Po,400)
		Po_fex_cur={}
		Po_inter_used={}
		
		
		new_portchannel=portchannels__.init_po_new(Correspondance_old_new,result_fex,IterPo__)

		
		for equipement__ in portchannels__.new_po.keys():
			type_fex=result_fex[equipement__]
			for PoId__ in portchannels__.new_po[equipement__].keys():
				for interface____ in portchannels__.new_po[equipement__][PoId__]:
					POID__=PoId__
					try:
						po_status=Interface_Status[interface____[0]][interface____[1]]
						po_switchport=Interface_Switchport[interface____[0]][interface____[1]]
						po_description=Interface_DescriptionPo[interface____[0]][interface____[1]]
						int_desc=Interface_Description[interface____[0]][interface____[1]]
					except KeyError:
						pdb.set_trace()
					interface__=interface____[1]
					LISTE_PARAM_N5K=(('INTERFACE',interface__),
								('DESCRIPTION',int_desc),
								('POID',POID__))
					try:
						if Interface_Status_new[equipement__][interface__][1]=='sfpInvali':
							speed=" speed 1000\n"
						else:
							speed=None
					except KeyError:
						pdb.set_trace()
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
					
					type_sw_switchport=po_switchport[1]
					
					if type_sw_switchport == 'static access' or type_sw_switchport == 'access' or type_sw_switchport == 'down':
						type_sw_cur='ACCESS'
					elif type_sw_switchport == 'trunk':
						type_sw_cur='TRUNK'		
					test_fex_cur=test_interface_fex(interface__)
					
				#pdb.set_trace()
				

				if type_sw_cur=='ACCESS':
					vlan=po_status[2]
					if args.translation:
						vlan=translate_vlan(po_status[2],Vlans_correspondance,Interface_HostSrc[equipement__][interface__])
					LISTE_PARAM_N5K=(('POID',POID__),
									('DESCRIPTION',po_description),
									('VLAN',vlan))
					if type_fex == "CLASSICAL_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_ACCESS).replace(LISTE_PARAM_N5K)
					elif type_fex == "DUAL_HOMED_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_ACCESS_WO_VPC).replace(LISTE_PARAM_N5K)
					else:
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_ACCESS).replace(LISTE_PARAM_N5K)
				#print(config_cur)
				elif type_sw_cur=='TRUNK':
					vlan_trunk=po_switchport[4]
					if args.translation:
						vlan_trunk=translate_vlan(po_switchport[4],Vlans_correspondance,Interface_HostSrc[equipement__][interface__])
					vlan_native=po_switchport[3]
					if vlan_native!='1':
						vlan_native=translate_vlan(po_switchport[3],Vlans_correspondance,Interface_HostSrc[equipement__][interface__])
					LISTE_PARAM_N5K=(('POID',POID__),
									('DESCRIPTION',po_description),
									('VLAN_LIST',vlan_trunk))
				
					if type_fex == "CLASSICAL_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_TRUNK).replace(LISTE_PARAM_N5K)	
					elif type_fex == "DUAL_HOMED_FEX":
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_TRUNK_WO_VPC).replace(LISTE_PARAM_N5K)
					else:
						config_cur=configTemplate(MODEL_CONFIG_N5K_INT_PO_TRUNK).replace(LISTE_PARAM_N5K)
					if speed:
						config_cur+=speed
				else:
					pdb.set_trace()
				try:
					if vlan_native=='1':
						config[equipement__]=config[equipement__]+config_cur
					elif vlan_trunk=='ALL':
						config[equipement__]=config[equipement__]+suppress_vlan_all(config_cur)
					else:
						config[equipement__]=config[equipement__]+insert_native_vlan(config_cur,vlan_native)
					
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
	
	
				
			
			
		