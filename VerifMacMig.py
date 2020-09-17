#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import cache as cc
import sys
import re
import checkMigFex as comSbe
import pprint
from connexion import *

def extractMac(mac__,liste_mac):
	result=[]
	for mac_cur in liste_mac:
		if mac__[0:2]==mac_cur[0:2]:
			result.append(mac_cur)		
	return result

if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	parser.add_argument("--hostname", action="store",help="equipement pour qui on vérifie les mac",required=True)
	parser.add_argument("--switch-port",dest='switch_port',action="append",help="Ancien port avant migration format switch:port",required=True)
	parser.add_argument("--filter",action="store",help="filtre sur les ports (regex)",required=True)
	args = parser.parse_args()
	
	tag_switch="MIG_MAC_"+args.hostname.upper()
	infoMacCache=cc.Cache(tag_switch)
	infoMac=infoMacCache.getValue()
	SwitchPort={}
	for swport in args.switch_port:
		if re.search(':',swport):
			info_port_sw=swport.split(':')
			SwitchPort[info_port_sw[0]]=info_port_sw[1]
		else:
			print('Vérifier le format de l\'option --switch-port')
			print('Format switch:port')
			sys.exit(1)	
	
	if infoMacCache.isOK():
		print('les données (mac table) ont été trouvées')
		
	else:
		print('Mettre à jour le cache MAC pour '+args.hostname+ " TAG:"+tag_switch)
		sys.exit(1)
		
	InfoMacFedCur={}
	
	if args.filter:
		mac_filtered=[]
		for mac__ in infoMac:
			if re.search(args.filter,mac__[2]):
				mac_filtered.append(mac__)
	else:
		mac_filtered=infoMac
		#print("pas de filtrage, on recherche toutes les mac")
				
	#print("MAC A RECHERCHER")
	#pprint.pprint(mac_filtered)
			
		
	for Switch__ in SwitchPort.keys():
		InfoMacFedCur[Switch__]=comSbe.ResultCommande.getCommande(Switch__,cc.COMMANDES['MAC']['commandes']+" interface "+SwitchPort[Switch__],cc.COMMANDES['MAC']['parserStr'])
	
	print("Mac présentes sur le port %s de %s" , ())
	for Switch__ in SwitchPort.keys():
		print("Mac présentes sur le port %s de %s" , (Switch__,SwitchPort[Switch__]))
		pprint.pprint(str(InfoMacFedCur[Switch__]))
		
	print("Recherche des mac à clearer")
	
	mac_to_clear={}
	for Switch__ in SwitchPort.keys():
		mac_to_clear[Switch__]=[]
		for mac__fed in InfoMacFedCur[Switch__]:
			liste_mac_cur=extractMac(mac__fed,mac_filtered)
			mac_to_clear[Switch__]+=liste_mac_cur
			
	pprint.pprint(mac_to_clear)
	
	for Switch__ in mac_to_clear.keys():
		print("Commandes sur"+Switch__ +":")
		for mac in mac_to_clear[Switch__]:
			print(" clear mac address-table dynamic address %s vlan %s"  % ( mac[1] , mac[0]))
			
		
	
		
	