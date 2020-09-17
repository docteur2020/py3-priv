#!/usr/bin/env python3.7
# coding: utf-8


from ParsingShow import ParseArpCiscoFile,writeCsv,getEquipementFromFilename
import pyparsing as pp
from io import StringIO
import argparse
import glob
import pdb
import pickle
import re
from random import shuffle
import pdb
from ParseVlanListe import liste_vlans,vlan
from getArpUnicorn import *
import aci.Fabric as ACISbe
from pprint import pprint as ppr

class arpEntry(object):
	def __init__(self,ip,mac,interface):
		self.ip=ip
		self.mac=mac
		self.interface=interface
		
	def __str__(self):
		return "IP:"+self.ip+";INTERFACE:"+self.interface+";MAC:"+self.mac
		
		
class arpEntries(object):

	def __init__(self,output="",dump="",Dict=""):
		self.entries={}
		if output:
			try:
				AllArp=ParseArpCiscoFile(output)
			except pp.ParseException as ppError:
				print("Erreur parsing du fichier:"+output)
				print(ppError)
				pass
				
			for VRF in AllArp.keys():
				self.entries[VRF]=[]
				for arp__ in AllArp[VRF]:
					try:
						if arp__:
							self.entries[VRF].append(arpEntry(arp__[0],arp__[1],arp__[2]))
					except TypeError as e:
						pdb.set_trace()
						print(e)
				
					
		if dump:
			pass
			
		if Dict:
			self.entries=Dict
			
		
	def __str__(self):
		resultat=StringIO()
		for VRF in self.entries.keys():
			resultat.write(VRF+":")
			for arp__ in self.entries[VRF]:
				resultat.write(str(arp__)+'\n')
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str

class DC_arp(object):
	def __init__(self,repertoire="",dump="",DC_dict={}):
		self.ArpEntries_DC={}
		
		if repertoire:
			Liste_file_show_arp=glob.glob(repertoire+'/*.log')
			for file_show_arp in Liste_file_show_arp:
				file_show_arp__=file_show_arp.split('/')[-1]
				equipement__=getEquipementFromFilename(file_show_arp__).upper()
				self.ArpEntries_DC[equipement__]=arpEntries(output=file_show_arp)
				
		if dump:
			self.load(dump)
			
		if DC_dict:
			self.ArpEntries_DC=DC_dict
				
	def __str__(self):
	
		resultat=StringIO()
		for hostname in self.ArpEntries_DC.keys():
			resultat.write("Equipement:"+hostname+"\n")
			resultat.write(str(self.ArpEntries_DC[hostname]))
			
		resultat_str=resultat.getvalue()
		resultat.close()
			
		return resultat_str
		
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def getIPbyVlan(self):
		result_arpByVlan={}
		for hostname in self.ArpEntries_DC.keys():
			for VRF in self.ArpEntries_DC[hostname].entries.keys():
				for arp__ in self.ArpEntries_DC[hostname].entries[VRF]:
					if ( arp__.mac != 'incomplete' or arp__.mac != 'INCOMPLETE' or arp__.mac != 'Incomplete' ) and re.search('[Vv]lan',arp__.interface):
						try:
							result_arpByVlan["["+VRF+"]"+arp__.interface].append(arp__.ip)
						except KeyError:
							result_arpByVlan["["+VRF+"]"+arp__.interface]=[arp__.ip]
							
		return 	result_arpByVlan	
		
	
	def init_ping_file(self):
		ipsByvlan=self.getIPbyVlan()
		for interface in ipsByvlan.keys():
			shuffle(ipsByvlan[interface])
			try:
				if len(ipsByvlan[interface]) > 2:
					print(ipsByvlan[interface][0]+" "+interface)
					print(ipsByvlan[interface][1]+" "+interface)
				else:
					print(ipsByvlan[interface][0]+" "+interface)
			except IndexError as indexerror:
				print(indexerror)
				pdb.set_trace()
				
	def init_ping_file_oneIPbyVrf(self,liste_vlans__=None):
		ipsByvlan=self.getIPbyVlan()
		ListeVRF=[]
		if liste_vlans__:
			liste_vlan_cur=liste_vlans(liste_vlans__)
		for interface in ipsByvlan.keys():
			shuffle(ipsByvlan[interface])
			VRF_cur=interface.split(']')[0].replace('[','')
			if VRF_cur not in ListeVRF:
				ListeVRF.append(VRF_cur)
				try:
					if len(ipsByvlan[interface]) > 2:
						print(ipsByvlan[interface][0]+" "+interface)
						print(ipsByvlan[interface][1]+" "+interface)
					else:
						print(ipsByvlan[interface][0]+" "+interface)
				except IndexError as indexerror:
					print(indexerror)
					pdb.set_trace()
		

			
		
	def load(self,filename):
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
			
		try:
			self.ArpEntries_DC=dc.ArpEntries_DC

		except:
			print('ERROR LOAD DUMP')	
		

def init_ping_file_from_endpoint(endpoints__,arp__):
	ips__=[]
	for node in endpoints__:
		for interface in endpoints__[node]:
			if 'OTV' in interface:
				continue
			for endpoint in endpoints__[node][interface]:
				comment_cur='_'.join([node,interface,*endpoint [0:2],endpoint[5]])
				if endpoint[4]!='0.0.0.0':
					ip_cur=endpoint[4]
				else:
					try:
						ip_cur=arp__[endpoint[3]][0]['ip']
					except KeyError:
						continue
				ips__.append([ip_cur,comment_cur])
				
	#ppr(ips__)
	for ip in ips__:
		print(ip[0],ip[1])
		
	return ips__

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-r", "--repertoire",action="store",help="Répertoire contenant les output show arp")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump type cdp")
	group1.add_argument("--fabric", action="store",help="Aci Fabric")
	parser.add_argument("-e", "--exportcsv",action="store",help=u"Résultat sous forme fichier csv",required=False)
	parser.add_argument("-s", "--save",action="store",help=u"Résultat dans fichier dump",required=False)
	parser.add_argument("--site",action="store",help=u"Uniqumeent avec l'option fabric, site",required=False)
	parser.add_argument("-p", "--pingfile",action="store",help=u"Ping File",required=False)
	parser.add_argument("--pingfileall",action="store",help=u"Ping File",required=False)
	parser.add_argument("-P", "--printing",action="store_true",help=u"Ping File",required=False)
	parser.add_argument("-v", "--vlans",action="store_true",help=u"liste vlans",required=False)
	args = parser.parse_args()
	
	if args.fabric and not args.site:
		raise argparse.ArgumentError(None,'--fabric  nécessite --site ')
	
	if args.repertoire:
		A=DC_arp(repertoire=args.repertoire)
	elif args.dumpfile:
		A=DC_arp(dump=args.dumpfile)
	elif args.fabric:
		listeFabric=ACISbe.Fabric.getFabricName()
		if args.fabric not in listeFabric:
			print('Fabric inconnu',file=sys.stderr)
			print('Fabrics connues:',str(listeFabric))
			sys.exit(1)
		listeSite=ACISbe.Fabric.getExistingSite(args.fabric)
		if args.site not in listeSite:
			print('site inconnu',file=sys.stderr)
			print('Sites connus:',str(listeSite))
			sys.exit(1)
		
		endpoints=ACISbe.Fabric.getEndpointFromeCache(args.fabric,args.site)
		arps_unicorns=load_json_arp(getLastDumpArp())
		ips__=init_ping_file_from_endpoint(endpoints,arps_unicorns)
		#print(endpoints)
		#print(arps_unicorns)
	
	if args.save:
		A.save(args.save)
	
	if args.pingfile:
		A.init_ping_file_oneIPbyVrf()
	elif args.pingfileall:
		A.init_ping_file()
		
	if args.printing:
		print(str(A))