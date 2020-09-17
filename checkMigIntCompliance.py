#!/usr/bin/env python3.7
# -*- coding: utf-8 -*- 

from ParsingShow import DC,writeCsvRaw
import csv
import re
import argparse
import pdb
import json
from ParseVlanListe import liste_vlans,vlan
import yaml
from mkconfigport2 import translate_vlan

def init_interfaces(fichier,dump):
	result=[]
	dc=DC()
	dc.load(dump)
	with open(fichier,'r') as file_info_port:
		for ligne in file_info_port:
			ligne_col=[ x for x in  re.split(',|;| ',ligne)  if x ]
			#pdb.set_trace()
			equipement_src=ligne_col[0].lower()
			interface_src=ligne_col[1]
			equipement_dst=ligne_col[2].lower()
			interface_dst=ligne_col[3].replace('\n','')
			info_src=dc.extractInterface(equipement_src,interface_src)
			info_dst=dc.extractInterface(equipement_dst,interface_dst)
			result.append([[equipement_src,interface_src,info_src],[equipement_dst,interface_dst,info_dst]])
		
	return result
	

def checkConnected(interfaces):
	messages={}
		
	for interface in interfaces:
		" Vérificaton si les interfaces sources sont bien en connected"
		#pdb.set_trace()
		status=eval(interface[0][2][6])[1]
		if status=="connected":
			try:
				messages[interface[0][0]][interface[0][1]]=(True,"SRC CONNECTED OK")
			except KeyError:
				messages[interface[0][0]]={}
				messages[interface[0][0]][interface[0][1]]=(True,"SRC CONNECTED OK")
		else:
			try:
				messages[interface[0][0]][interface[0][1]]=(False,"SRC NOT CONNECTED KO:"+status)
			except KeyError:
				messages[interface[0][0]]={}
				messages[interface[0][0]][interface[0][1]]=(False,"SRC NOT CONNECTED KO:"+status)
				
		" Vérificaton si les interfaces destinations sont bien en NOT connected"
		status=eval(interface[1][2][6])[1]
		if status=="notconnec":
			try:
				messages[interface[1][0]][interface[1][1]]=(True,"DST NOT USED OK")
			except KeyError:
				messages[interface[1][0]]={}
				messages[interface[1][0]][interface[1][1]]=(True,"DST NOT USED OK")
		else:
			try:
				messages[interface[1][0]][interface[1][1]]=(False,"DST IN USE  KO:"+status)
			except KeyError:
				messages[interface[1][0]]={}
				messages[interface[1][0]][interface[1][1]]=(False,"DST IN USE KO:"+status)	
	
	
	return messages
	
def checkConfig(interfaces,VlansNat=None):
	messages={}
	Message_cur=None
	message_desc=None
	bool_desc=None
	message_po=None
	bool_po=None
	message_switchport=None
	bool_switchport=None
	message_switchport_type=None
	bool_switchport_type=None
	message_switchport_vlan=None
	bool_switchport_vlan=None
	
	for interface in interfaces:
		" Vérificaton si les interfaces sources sont bien en connected"
		description_src=interface[0][2][2]
		description_dst=interface[1][2][2]
		po_src=eval(interface[0][2][5])
		po_dst=eval(interface[1][2][5])
		switchport_src=eval(interface[0][2][7])
		switchport_dst=eval(interface[1][2][7])
		Message_cur=None
		"Vérification de la description"


		if description_src.rstrip()==description_dst.rstrip():
			message_desc="CONFIG DST DESCRIPTION OK"
			bool_desc=True
		else:
			message_desc="CONFIG DST DESCRIPTION KO:SRC "+description_src+'!='+description_dst
			bool_desc=False
			
		"Vérification de la fonctionnalité Po"
		if po_src==None and po_dst==None:
			message_po="CONFIG DST PO OK:NONE"
			bool_po=True
		elif po_src!=None and po_dst!=None:
			if po_src[2]==po_dst[2]:
				message_po="CONFIG DST PO OK:"+po_dst[2]
				bool_po=True
			else:
				message_po="CONFIG DST PO KO BAD PROTOCOL :"+po_src[2]+'(SRC)!='+po_dst[2]+'(DST)'
				bool_po=False
			
		else:
			message_po="CONFIG DST PO KO:"+str(po_src)+'(SRC)!='+str(po_dst)+'(DST)'
			bool_po=False
		
		"Vérification de la fonctionnalité switchport"
		#pdb.set_trace()
		if ( switchport_src[1]=='static access' or  switchport_src[1]=='access') and ( switchport_dst[1]=='static access' or  switchport_dst[1]=='access') :
			message_switchport_type="CONFIG DST ACCESS OK"
			bool_switchport_type=True
		
			if not VlansNat:
				if switchport_src[2]==switchport_dst[2]:
					message_switchport_vlan="CONFIG DST VLAN OK"
					bool_switchport_vlan=True	
	
				else:
					message_switchport_vlan="CONFIG DST VLAN KO:"+switchport_src[2]+'(SRC)!='+switchport_dst[2]+'(DST)'
					bool_switchport_vlan=False
			else:
				vlan_nat_cur=translate_vlan(switchport_src[2],VlansNat,interface[0][0])
				if vlan_nat_cur==switchport_dst[2]:
					message_switchport_vlan="CONFIG DST VLAN OK NAT VLAN PRESENT "
					bool_switchport_vlan=True	
	
				else:
					message_switchport_vlan="CONFIG DST VLAN KO:"+vlan_nat_cur+'(SRC)!='+switchport_dst[2]+'(DST) NAT VLAN PRESENT'
					bool_switchport_vlan=False
		
		
		elif switchport_src[1]=='trunk' and  switchport_dst[1]=='trunk':
		
			message_switchport_type="CONFIG DST TRUNK OK"
			bool_switchport_type=True
			
			if not VlansNat:
				if switchport_src[2]==switchport_dst[2]:
					message_switchport_vlan="CONFIG DST NATIVE VLAN OK"
					bool_switchport_vlan=True	
	
				else:
					message_switchport_vlan="CONFIG DST NATIVE VLAN KO"+switchport_src[2]+'(SRC)'+'!='+switchport_dst[2]+'(DST)'
					bool_switchport_vlan=False
					
				if liste_vlans(switchport_src[4]).explode()==liste_vlans(switchport_dst[4]).explode():
					message_switchport_vlan+="/CONFIG DST VLAN TRUNK OK"
					bool_switchport_vlan=True	
	
				else:
					message_switchport_vlan="CONFIG DST VLAN TRUNK KO"+switchport_src[4]+u'(SRC)!='+switchport_dst[4]+'(DST)'
					bool_switchport_vlan=False
			else:
				if switchport_src[2]!='1':
					vlan_native_cur=translate_vlan(switchport_src[2],VlansNat,interface[0][0])
				else:
					vlan_native_cur='1'
					
				vlan_trunk_cur=translate_vlan(switchport_src[4],VlansNat,interface[0][0])
				if vlan_native_cur==switchport_dst[2]:
					message_switchport_vlan="CONFIG DST NATIVE VLAN OK NAT PRESENTE"
					bool_switchport_vlan=True	
	
				else:
					message_switchport_vlan="CONFIG DST NATIVE VLAN KO"+vlan_native_cur+'(SRC)'+'!='+switchport_dst[2]+'(DST) NAT PRESENT'
					bool_switchport_vlan=False
					
				if vlan_trunk_cur==switchport_dst[4]:
					message_switchport_vlan+="/CONFIG DST VLAN TRUNK OK"
					bool_switchport_vlan=True	
	
				else:
					message_switchport_vlan="CONFIG DST VLAN TRUNK KO"+vlan_trunk_cur+u'(SRC)!='+switchport_dst[4]+'(DST) NAT PRESENT'
					bool_switchport_vlan=False
			
		Message_cur={'DESCRIPTION':[message_desc,bool_desc],'SWITCHPORT':[message_switchport_type,bool_switchport_type],'VLAN':[message_switchport_vlan,bool_switchport_vlan],'PORT-CHANNEL':[message_po,bool_po],'BOOLEAN':bool_desc and bool_switchport_type and bool_switchport_vlan and bool_po,'SOURCE':[interface[0][0],interface[0][1]]}
		
		
		#pdb.set_trace()
		
		try:
			messages[interface[1][0]][interface[1][1]]=Message_cur

		except KeyError:
			messages[interface[1][0]]={}
			messages[interface[1][0]][interface[1][1]]=Message_cur
		
	
	return messages
	
def extract_interface_to_configure(messages):
	resultat=[]

	for equipement in messages.keys():
		for interface in messages[equipement]:
			if not messages[equipement][interface]['BOOLEAN']:
				resultat.append([equipement,interface,messages[equipement][interface]['SOURCE']])
			else:
				print("non traité:",interface)

	

	return resultat
	
def generate_csv_conf(interfaces,dump,fichier):
	resultat_csv=[]
	dc=DC()
	dc.load(dump)
	for interface in interfaces:
		equipement__=interface[0]
		interface__=interface[1]
		equipement_src=interface[2][0]
		interface_src=interface[2][1]
		resultat_csv.append(['None','None',equipement__.upper(),interface__]+dc.extractInterface(equipement_src,interface_src)+[dc.extractInterface(equipement__,interface__)[6]])
		#pdb.set_trace()
	writeCsvRaw(resultat_csv,fichier)

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--fichier",action="store",help="Fichier contenant les interfaces à migrer et cibles",required=True)
	parser.add_argument("-d", "--dump",action="store",help="fichier contenant le dump DC",required=True)
	parser.add_argument("-c", "--csv",action="store",help="csv pour le fichier de configuration",required=False)
	parser.add_argument("-t","--translation",action="store",help="Fichier yaml contenant la translation de Vlan ",required=False)
	
	args = parser.parse_args()
	
	Vlans_correspondance={}
	if args.translation:
		with open(args.translation, 'r' ) as model_yml:
			Vlans_correspondance = yaml.load(model_yml,Loader=yaml.SafeLoader)
	
	
	info_interfaces=init_interfaces(args.fichier,args.dump) 
	
	print('Check du statut des interfaces')
	print(json.dumps(checkConnected(info_interfaces),indent=3))
	print('Check des configurations existantes')
	if args.translation:
		print(json.dumps(checkConfig(info_interfaces,Vlans_correspondance),indent=3))
		Messages=checkConfig(info_interfaces,Vlans_correspondance)
	else:
		print(json.dumps(checkConfig(info_interfaces),indent=3))
		Messages=checkConfig(info_interfaces)
	print('récupération des interfaces à configurer')
	
	liste_interface=extract_interface_to_configure(Messages)
	print(liste_interface)
	#print(info_interfaces)
	#pdb.set_trace()
	
	if args.csv:
		print('Sauvegarde du fichier de configuration dans '+args.csv)
		generate_csv_conf(liste_interface,args.dump,args.csv)
	
	
	
