#!/usr/bin/env python3.7
# coding: utf-8


from __future__ import unicode_literals


import argparse
import pdb
import dns.resolver
from ParsingShow import DC
from ParsingShow  import ParseLldpNeighborDetailString , ParseStatusCisco , getLongPort 
from connexion import *
from extractMacFromCsvQuador import hostnames
import csv
from cdpEnv import DC_cdp,cdpEntries,cdpEntry,interconnexions,interconnexion
from getArpFirewall import *
import pandas as pd
from initMacOUI import *

HEAD=['switch','interface','description','Mac','IP','Reverse DNS','Info quador','LLDP']
HEAD_LONG=['EQUIPEMENT','INTERFACE','DESCRIPTION','MAC','IP','PORT-CHANNEL','STATUS=[DESC,STATUS,VLAN,DUPLEX,SPEED]','SWITCHPORT=[STATUS,MODE,ACCESS VLAN,NATIVE VLAN,TRUNK VLAN]','DESCRIPTION PO','INFO QUADOR','LLDP INFO']
TMP='/home/x112097/TMP'

def extract_int_fex(liste_interface):
	resultat=[]
	for interface__ in liste_interface:
		if re.search('[Ee]th1[0-9][0-9]/[0-9]/[0-9]',interface__):
			resultat.append(interface__)
						
	return resultat
	
def exclude_int_fex(liste_interface):
	resultat=[]
	for interface__ in liste_interface:
		if not re.search('[Ee]th1[0-9][0-9]/[0-9]/[0-9]',interface__):
			resultat.append(interface__)
						
	return resultat
	
def filter_int_fex(liste_interface,regex):
	resultat=[]
	for interface__ in liste_interface:
		if re.search(regex,interface__):
			resultat.append(interface__)
						
	return resultat
	
def writeCsv(list_result,fichier_csv):
	
	with open(fichier_csv,'w+') as csvfile:
		csvwriter=csv.writer(csvfile,delimiter=';',quotechar='"',quoting=csv.QUOTE_ALL)
		for entry in list_result:
			csvwriter.writerow(entry)
	
	return None
	
def writeExcel(list_result,fichier_excel):
	
	pd.DataFrame(list_result).to_excel(fichier_excel, header=False, index=False)
	
	return None
	
def getReverseDns(ListIP):
	resultat=[]
	
	for IP in ListIP:
		name_cur=None
		try:
			name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),'192.16.207.80').answer[0].__str__().split()[-1] 
		except IndexError:
			try:
				name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),'184.12.21.17').answer[0].__str__().split()[-1]
			except IndexError:
				pass
		resultat.append(name_cur)
		
	return resultat
	
def getLigneCsv(ListInfos):
	return ';'.join([ str(info).strip() for info in ListInfos ])
	
def getAllSwitch(fichier):
	switchs=[]
	with open(args.fichier,'r') as fich__:
		for ligne in fich__:
			column=ligne.split(';')
			switch=str(eval(column[0])).strip()
			if switch not in switchs and switch !='EQUIPEMENT':
				switchs.append(switch)
			
	#print(args.fichier)
	#print(str(switchs))
	
	return switchs
	
def getLLDPNeighbor(switchs):
		
	lldp__={}
	for switch in switchs:
		con_get_lldp_cur=connexion(equipement(switch),None,None,None,'SSH',"TMP/"+switch.lower()+"_shlldpneighbordetail.log","TMP","show lldp neighbor detail",timeout=300,verbose=False)
		lldp_cur=con_get_lldp_cur.launch_withParser(ParseLldpNeighborDetailString)
		lldp__[switch]=lldp_cur

	return lldp__

def getInterfaceStatusConnected(switch):
	con_get_status_cur=connexion(equipement(switch),None,None,None,'SSH',"TMP/"+switch.lower()+"_shlldpneighbordetail.log","TMP","show interface status up",timeout=300,verbose=False)
	status_cur=con_get_status_cur.launch_withParser(ParseStatusCisco)
	
	return status_cur
	
def get_cdpneigbor(switch,cdp__):
	return cdp__.getNeighbors(switch)
	
def init_interface(interface_all,interface_cdp):
	resultat=[]
	for interface in interface_all:
		if re.search('^Eth',interface) and getLongPort(interface) not in interface_cdp:
			resultat.append(interface)
			
	return resultat

		
def get_cdpneigbor_switch(switch,cdp__):
	
	resultat=[]
	
	try:
		for interface in cdp__.getNeighbors(switch).keys():
			if re.search('-CLS-|-CFD-|ODIN|PRDSWI|HPDSWI',cdp__.getNeighbors(switch)[interface].hostname):
				resultat.append(interface)
	except AttributeError:
		pass
		
	return resultat
	
def getLLDPInfo(switch,interface,lldps):
	resultat=None
	
	try:
		resultat=lldps[switch][interface]
	except KeyError:
		pass
		
	return resultat
	
def initFormatImpact_short(resultat_csv,hosts_quador,lldps__,fw_arp_json,translate=""):
	resultat_new_csv=[]
	
	if translate:
		ouidb=OUIContainer()
	
	resultat_new_csv.append(HEAD)
	for entry in resultat_csv:
		try:
			ips_liste=addIPFirewall(entry[4],fw_arp_json)
			if isinstance(ips_liste, list):     
				if ips_liste:
					temp_liste_mac_traite=[]
					if isinstance(ips_liste[0], dict):
						for ips in ips_liste:
							if ips:
								for mac in ips.keys():
									if ips[mac]:
										if mac not in temp_liste_mac_traite:
											Liste_IP_cur=list(set([ ip__[3] for ip__ in ips[mac] ]))
											if translate:
												ligne_csv=getLigneCsv([entry[0],entry[1],entry[2],ouidb.translate(mac),Liste_IP_cur,getReverseDns(Liste_IP_cur),str(hosts_quador.get_info_mac(mac)),getLLDPInfo(entry[0].upper(),entry[1],lldps__)])
											else:
												ligne_csv=getLigneCsv([entry[0],entry[1],entry[2],mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),str(hosts_quador.get_info_mac(mac)),getLLDPInfo(entry[0].upper(),entry[1],lldps__)])
											print(ligne_csv)
											resultat_new_csv.append(ligne_csv.split(';'))
											temp_liste_mac_traite.append(mac)

									else:
										Liste_IP_cur=[]
										if not re.search('-CLS-|-CFD-|CLSODIN',entry[2]):
											if mac not in temp_liste_mac_traite:
												if translate:
													ligne_csv=getLigneCsv([entry[0],entry[1],entry[2],ouidb.translate(mac),Liste_IP_cur,getReverseDns(Liste_IP_cur),str(hosts_quador.get_info_mac(mac)),getLLDPInfo(entry[0].upper(),entry[1],lldps__)])
												else:
													ligne_csv=getLigneCsv([entry[0],entry[1],entry[2],mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),str(hosts_quador.get_info_mac(mac)),getLLDPInfo(entry[0].upper(),entry[1],lldps__)])
												print(ligne_csv)
												resultat_new_csv.append(ligne_csv.split(';'))
												temp_liste_mac_traite.append(mac)
								
											
										
					else:
						if not re.search('-CLS-|-CFD-|CLSODIN',entry[2]):
							ligne_csv=getLigneCsv([entry[0],entry[1],entry[2],None,None,None,None,getLLDPInfo(entry[0].upper(),entry[1],lldps__)])
							print(ligne_csv)
							resultat_new_csv.append(ligne_csv.split(';'))
			else:	
				print("N/A")
			
			
		except SyntaxError as e:
			print("Syntax Error"+str(e))
			pass
		except NameError as e:
			print("Name Error:"+str(e))
			pass
		
		
	return resultat_new_csv
	
def initQuadorList(liste_mac,hosts_quador):
	resultat={}
	try:
		for mac in eval(liste_mac):
			info_cur=hosts_quador.get_info_mac(mac[1])
			if info_cur:
				resultat[mac[1]]=str(hosts_quador.get_info_mac(mac[1]))
	except ValueError:
		pdb.set_trace()
		
	except IndexError:
		pdb.set_trace()
		
	except TypeError:
		resultat=None
	
	
	return resultat
	
def initFormatImpact(resultat_csv,hosts_quador,lldps__,fw_arp_json):
	resultat_new_csv=[]
	resultat_new_csv.append(HEAD_LONG)
	for entry in resultat_csv:
		quador_cur=initQuadorList(entry[3],hosts_quador)
		lldp_info=getLLDPInfo(entry[0].upper(),entry[1],lldps__)
		new_ip=addIPFirewall(entry[4],fw_arp_json)
		entry[4]=new_ip
		if not re.search('-CLS-|-CFD-|CLSODIN|PRDSWI|HPDSWI',entry[2]):
			resultat_new_csv.append(entry+[quador_cur,lldp_info])
	
	return resultat_new_csv
	
def addIPFirewall(ips,fw_arp_json):
	fw_arp=load_json_arp(fw_arp_json)
	resultat=[]
	ips__=eval(ips)
	new_entry=None
	if ips__:
		for ip in ips__:
			new_entry=None
			if ip:
				try:
					mac_cur=ip.keys().__iter__().__next__()
					if not ip[mac_cur]:
						try:
							new_entry_cur=fw_arp[cisco_to_mac(mac_cur)]
							new_entry={mac_cur:[[new_entry_cur['firewall'],'N/A','N/A',new_entry_cur['ip']]]}
						except KeyError:
							new_entry={mac_cur:None}
					else:
						new_entry=ip
				except ValueError:
					pdb.set_trace()
				except AttributeError:
					pdb.set_trace()
				except TypeError:
					pdb.set_trace()
			else:
				new_entry=None
					
			resultat.append(new_entry)
	else:
		resultat=None
			
	
	return resultat
	

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group2=parser.add_mutually_exclusive_group(required=False)
	group3=parser.add_mutually_exclusive_group(required=False)
	group1.add_argument("-f", "--fichier",action="store",help="Contient le fichier",required=False)
	parser.add_argument("-q", "--quador",action="store",help="Contient le fichier dump quador",required=False)
	parser.add_argument("-l", "--lldp",action="store_true",help="Ajoute les informations LLDP",required=False)
	parser.add_argument("-x", "--xclude",action="store_true",help="Ajoute les informations LLDP",required=False)
	group2.add_argument("-s", "--save",action="store",help="Sauvegarde dans CSV",required=False)
	group1.add_argument("-e","--equipment",action="store",help="Equipement pour lequel on fait l'etude d'impact",required=False)
	parser.add_argument("-a","--arpfw",action="store",help="Les entrees ARP firewall en json",required=True)
	parser.add_argument("-d","--dump",action="store",help="Info DC format dump",required=False)
	parser.add_argument("-c","--cdps",action="store",help="Info CDP format dump",required=False)
	parser.add_argument("-o", "--short",action="store_true",help="Affichage short",required=False)
	parser.add_argument("-t", "--translate",action="store_true",help="Translate les macs",required=False)
	group2.add_argument("-X", "--excel",action="store",help="Sauvegarde dans xls",required=False)
	group3.add_argument("--fexonly",action="store_true",help="Extrait que les interfaces FEX",required=False)
	group3.add_argument("--nofex",action="store_true",help="Extrait que les interfaces non FEX",required=False)
	group3.add_argument("-r", "--regex",action="store",help="Filtre sur les interfaces",required=False)
	
	args = parser.parse_args()
	
	resultat=[]
	resultat.append(HEAD)
	
	if not args.equipment:
	
		if args.lldp:
			switchs__=getAllSwitch(args.fichier)
			lldps__=getLLDPNeighbor(switchs__)
			print(str(lldps__))
		
		if args.quador:
			HOSTS_=hostnames(dump=args.quador)
			
		if args.fichier:
			with open(args.fichier,'r') as fich__:
				for ligne in fich__:
					column=ligne.split(';')
					try:
						ips_liste=eval(eval(column[4]))
						if isinstance(ips_liste, list):     
							if ips_liste:
								if isinstance(ips_liste[0], dict):
									for ips in ips_liste:
										if ips:
											for mac in ips.keys():
												if ips[mac]:
													if args.quador:
														Liste_IP_cur=list(set([ ip__[3] for ip__ in ips[mac] ]))
														if args.lldp:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),str(HOSTS_.get_info_mac(mac)),getLLDPInfo(eval(column[0]),eval(column[1]),lldps__)])
														else:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),str(HOSTS_.get_info_mac(mac))])
														
	
													else:
														if args.lldp:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),getLLDPInfo(eval(column[0]),eval(column[1]),lldps__)])
														else:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur)])
												else:
													Liste_IP_cur=[]
													if args.quador:
														if args.lldp:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),str(HOSTS_.get_info_mac(mac)),getLLDPInfo(eval(column[0]),eval(column[1]),lldps__)])
														else:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),str(HOSTS_.get_info_mac(mac))])
													else:
														if args.lldp:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur),getLLDPInfo(eval(column[0]),eval(column[1]),lldps__)])
														else:
															ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),mac,Liste_IP_cur,getReverseDns(Liste_IP_cur)])
													
														
													
								else:
									if args.quador:
										ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),None,None,None])
									else:
										ligne_csv=getLigneCsv([eval(column[0]),eval(column[1]),eval(column[2]),None,None])							
						else:	
							print("N/A")
						print(ligne_csv)
						resultat.append(ligne_csv.split(';'))
					except SyntaxError as e:
						print("Syntax Error"+str(e))
						pass
					except NameError as e:
						print("Name Error:"+str(e))
						pass
		if args.save:
			writeCsv(resultat,args.save)
	else:
		if not args.quador or not args.dump or not args.cdps or not args.arpfw:
			parser.error("Les options -q -d -c -a sont obligatoire avec l'option -e")
			os.exit(3)
		else:
			dc__=DC()
			dc__.load(args.dump)
			cdp__=DC_cdp(dump=args.cdps)
			hosts_quador=hostnames(dump=args.quador)
			status__=getInterfaceStatusConnected(args.equipment)
			lldps__=getLLDPNeighbor([args.equipment])
			cdp_entries__=get_cdpneigbor(args.equipment,cdp__)
			cdp_entries__otherswitch=get_cdpneigbor_switch(args.equipment,cdp__)
			liste_interface=init_interface(status__.keys(),cdp_entries__otherswitch)
			#print(str(status__))
			#print(str(cdp_entries__))
			#print(str(cdp_entries__otherswitch))
			#print(liste_interface)
			
			if args.fexonly:
				liste_interface=extract_int_fex(liste_interface)
			elif args.nofex:
				liste_interface=exclude_int_fex(liste_interface)
			
			if args.regex:
				liste_interface=filter_int_fex(liste_interface,args.regex)
				
				
			
			resultat_csv=dc__.extractInterfaces_from_list([ [ args.equipment,interface ] for interface in liste_interface ])
			#print(resultat_csv)
			if args.short:
				if args.translate:
					resultat=initFormatImpact_short(resultat_csv,hosts_quador,lldps__,args.arpfw,translate=args.translate)
				else:
					resultat=initFormatImpact_short(resultat_csv,hosts_quador,lldps__,args.arpfw)
			else:
				resultat=initFormatImpact(resultat_csv,hosts_quador,lldps__,args.arpfw)
			if args.save:
				writeCsv(resultat,args.save)
			
			if args.excel:
				writeExcel(resultat,args.excel)
			
			
		

						
