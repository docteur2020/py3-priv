#!/usr/bin/env python3.7
# coding: utf-8


from ParsingShow import ParseInterfaceTransceiver,writeCsv,getEquipementFromFilename
import pyparsing as pp
from io import StringIO
from cdpEnv import *
import argparse
import glob
import pdb
import pickle
import re

class transceiver(object):
	def __init__(self,modele,revision,SN,PN,CVI):
		self.modele=modele
		self.revision=revision
		self.SN=SN
		self.ProductNumber=PN
		self.CiscoVendorID=CVI
		
	def __str__(self):
		return "MODELE:"+self.modele+";VERSION:"+self.revision+";SN:"+self.SN+";PN:"+self.ProductNumber+";Cisco Vendor ID:"+self.CiscoVendorID
		
class transceiverEntries(object):

	def __init__(self,output="",dump="",dict=""):
		self.entries={}
		if output:
			try:
				SFPAll=ParseInterfaceTransceiver(output)
			except pp.ParseException as ppError:
				print("Erreur parsing du fichier:"+output)
				print(ppError)
				pass
				
			#pdb.set_trace()
			
			for interface in SFPAll.keys():
				try:
					PN=SFPAll[interface]['part number']
					
				except KeyError:
					PN="UNKNOWN"
					
				try:
				
					CVI=SFPAll[interface]['cisco vendor id']
					
				except KeyError:
					CVI="UNKNOWN"	
					
					
				try:
					self.entries[interface]=transceiver(SFPAll[interface]['type'],SFPAll[interface]['revision'],SFPAll[interface]['serial number'],PN,CVI)
				except KeyError:
					pass
					
		if dump:
			pass
			
		if dict:
			self.entries=dict
		
	def __str__(self):
		resultat=StringIO()
		for interface in self.entries.keys():
			resultat.write(interface+":"+str(self.entries[interface])+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
class interconnexion_transceiver(interconnexion):
	def __init__(self,host_src,port_src,host_dest,port_dest,sfp_src,sfp_dst):
		super().__init__(host_src,port_src,host_dest,port_dest)
		self.sfp_src=sfp_src
		self.sfp_dst=sfp_dst
	
	def __str__(self):
		resultat=StringIO()
		for ligne in super().__str__().splitlines():
			resultat.write(ligne+";"+str(self.sfp_src)+";"+str(self.sfp_dst))
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
class DC_sfp(object):
	def __init__(self,repertoire="",dump="",DC_dict={}):
		self.sfpEntries_DC={}
		
		if repertoire:
			Liste_file_show_sfp=glob.glob(repertoire+'/*.log')
			for file_show_sfp in Liste_file_show_sfp:
				file_show_sfp__=file_show_sfp.split('/')[-1]
				equipement__=getEquipementFromFilename(file_show_sfp__).upper()
				self.sfpEntries_DC[equipement__]=transceiverEntries(output=file_show_sfp)
				
		if dump:
			self.load(dump)
			
		if DC_dict:
			self.sfpEntries_DC=DC_dict
				
	def __str__(self):
	
		resultat=StringIO()
		for hostname in self.sfpEntries_DC.keys():
			resultat.write("Equipement:"+hostname+"\n")
			resultat.write(str(self.sfpEntries_DC[hostname]))
			
		resultat_str=resultat.getvalue()
		resultat.close()
			
		return resultat_str
		
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
			
		try:
			self.sfpEntries_DC=dc.sfpEntries_DC

		except:
			print('ERROR')	
		
	
	def rechercheEntries(self,modele="",version="",pn="",sn=""):
		
		resultat={}
		for hostname in self.sfpEntries_DC.keys():
			resultat_cur={}
			for interface in self.sfpEntries_DC[hostname].entries.keys():
				if modele and sn:
					if re.search(':',modele):
						liste_modele=modele.split(':')
						for modele_cur in liste_modele:
							if self.sfpEntries_DC[hostname].entries[interface].SN<=sn and self.sfpEntries_DC[hostname].entries[interface].modele==modele_cur:
								resultat_cur[interface]=self.sfpEntries_DC[hostname].entries[interface]
					else:	
						if self.sfpEntries_DC[hostname].entries[interface].SN<=sn and self.sfpEntries_DC[hostname].entries[interface].modele==modele:
							resultat_cur[interface]=self.sfpEntries_DC[hostname].entries[interface]
						#pdb.set_trace()
				elif modele:
					if re.search(':',modele):
						#pdb.set_trace()
						liste_modele=modele.split(':')
						for modele_cur in liste_modele:
							if self.sfpEntries_DC[hostname].entries[interface].modele==modele_cur:
								resultat_cur[interface]=self.sfpEntries_DC[hostname].entries[interface]
				
					else:
						if self.sfpEntries_DC[hostname].entries[interface].modele==modele:
							resultat_cur[interface]=self.sfpEntries_DC[hostname].entries[interface]
				
				elif pn:
					if self.sfpEntries_DC[hostname].entries[interface].ProductNumber==pn:
						resultat_cur[interface]=self.sfpEntries_DC[hostname].entries[interface]
						
				elif sn:
					if self.sfpEntries_DC[hostname].entries[interface].SN<=sn:
						resultat_cur[interface]=self.sfpEntries_DC[hostname].entries[interface]
					
			if resultat_cur:
				#pdb.set_trace()
				resultat[hostname]=transceiverEntries(dict=resultat_cur)
					
		return DC_sfp(DC_dict=resultat)
		
	def init_interconnexions(self,dump_cdp,DC_SFP_Initial=None):
		interconnexions__=interconnexions()
		DC_CDP=DC_cdp(dump=dump_cdp)
		
		if DC_SFP_Initial:
			DC_SFP__=DC_SFP_Initial
		
		else:
			DC_SFP__=self
			
		for hostname in self.sfpEntries_DC.keys():
			for interface in self.sfpEntries_DC[hostname].entries.keys():
				cdp_cur=DC_CDP.getNeighbor(hostname,interface)
				sfp_cur=self.getSFP(hostname,interface)
	
				if cdp_cur:
					sfp_cur_neigh=DC_SFP__.getSFP(cdp_cur.hostname,cdp_cur.interface_neighbor)
					if sfp_cur_neigh:
						interconnexions__.add_element(interconnexion_transceiver(hostname,interface,cdp_cur.hostname,cdp_cur.interface_neighbor,sfp_cur,sfp_cur_neigh))
					else:
						#pdb.set_trace()
						print("Problème pour trouver le SFP: "+cdp_cur.hostname+" interface: "+cdp_cur.interface_neighbor)
				
				else:
					print("Neighbor non trouvé pour "+hostname+" "+interface+" "+str(sfp_cur))
						
		return interconnexions__
		
	
	def getSFP(self, hostname,interface):
		resultat=None
		
		try:
			resultat=self.sfpEntries_DC[hostname].entries[interface]
		except KeyError:
			pass
			
		return resultat
		

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-r", "--repertoire",action="store",help="Répertoire contenant les output show cdp neighbor detail")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump type cdp")
	parser.add_argument("-e", "--exportcsv",action="store",help=u"Résultat sous forme fichier csv",required=False)
	parser.add_argument("-p", "--pn",action="store",help=u"Filtre sur le product number",required=False)
	parser.add_argument("-m", "--modele",action="store",help=u"Filtre sur le modèle",required=False)
	parser.add_argument("-S", "--sn",action="store",help=u"Filtre sur le product serial number",required=False)
	parser.add_argument("-s", "--save",action="store",help=u"Résultat dans fichier dump",required=False)
	parser.add_argument("-c", "--cdp",action="store",help=u"dump de type CDP",required=False)
	args = parser.parse_args()
	
	if args.repertoire:
		A=DC_sfp(repertoire=args.repertoire)
	elif args.dumpfile:
		A=DC_sfp(dump=args.dumpfile)
	
	if args.save:
		A.save(args.save)
	
	if 	args.sn and args.modele:
		B=A.rechercheEntries(sn=args.sn,modele=args.modele)
		
		if args.cdp:
			interco=B.init_interconnexions(args.cdp,A)
			print(str(interco))
		
	elif args.pn:
		B=A.rechercheEntries(pn=args.pn)
	
		if args.cdp:
			interco=B.init_interconnexions(args.cdp,A)
			print(str(interco))
		else:
			print(B)
	elif args.sn:
		B=A.rechercheEntries(sn=args.sn)
		
		if args.cdp:
			interco=B.init_interconnexions(args.cdp,A)
			print(str(interco))
		else:
			print(B)
			
			
	elif args.modele:
		B=A.rechercheEntries(modele=args.modele)
		
		if args.cdp:
			interco=B.init_interconnexions(args.cdp,A)
			print(str(interco))
		else:
			print(B)		
	

	
	else:
		if args.cdp:
			interco=A.init_interconnexions(args.cdp)
			
			print(str(interco))
		print(A)
	#print(B)