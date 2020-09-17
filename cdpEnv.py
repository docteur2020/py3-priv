#!/usr/bin/env python3.7
# coding: utf-8


from ParsingShow import ParseCdpNeighborDetail,writeCsv,getEquipementFromFilename,getLongPort
import csv
import checkroute
import sys
import os
import argparse
import glob
import pdb
import pickle
from io import StringIO

class interconnexion(object):
	def __init__(self,host_src,port_src,host_dest,port_dest):
		self.host_source=host_src
		self.host_destination=host_dest
		self.port_source=port_src
		self.port_destination=port_dest
		
	def __eq__(self,other_interco):
		return (self.host_source==other_interco.host_source and self.host_destination==other_interco.host_destination and self.port_source==other_interco.port_source and self.port_source==other_interco.port_source ) or (self.host_source==other_interco.host_destination and self.host_destination==other_interco.host_source and self.port_source==other_interco.port_destination and self.port_source==other_interco.port_destination ) 
		
	def __str__(self):
		return self.host_source+";"+self.port_source+";"+self.host_destination+";"+self.port_destination
		

class interconnexions(object):
	def __init__(self):
		self.liste_interconnexion=[]
		
	def add_element(self,interco__):
		if interco__ not in self:
			self.liste_interconnexion.append(interco__)
			
	def __contains__(self,interco__):
		result=False
		for interco__cur in self.liste_interconnexion:
			if interco__cur == interco__:
				result=True
				
		return result
		
	def __str__(self):
		resultat=StringIO()
		for interco__ in self.liste_interconnexion:
			resultat.write(str(interco__)+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	
class cdpEntry(object):

	def __init__(self,hostname,interface_local,interface_neighbor):
		self.hostname=hostname
		self.interface=interface_local
		self.interface_neighbor=interface_neighbor
		
	def __str__(self):
		#pdb.set_trace()
		return "Interface:"+self.interface+" Hostame:"+self.hostname+"("+self.interface_neighbor+")"
		
	def __repr__(self):
		#pdb.set_trace()
		return "Interface:"+self.interface+" Hostame:"+self.hostname+"("+self.interface_neighbor+")"
		
class cdpEntries(object):

	def __init__(self,output="OUTPUT/tigr4-odin-svc-a1-cdp.log",dump="DUMP/CDP/tigr4-odin-svc-a1.dump"):
		self.entries=[]
		self.entries_dict={}
		if output:
			CDPAll=ParseCdpNeighborDetail(output)
			
			for interface in CDPAll.keys():
				self.entries.append(cdpEntry(CDPAll[interface]['Neighbor'],interface,CDPAll[interface]['Interface Neighbor']))
		if dump:
			pass
		
		for entry in self.entries:
			self.entries_dict[entry.interface]=entry
		
	def __str__(self):
		resultat=StringIO()
		for entry in self.entries:
			resultat.write(str(entry)+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
class DC_cdp(object):
	def __init__(self,repertoire="",dump=""):
		self.cdpEntries_DC={}
		if repertoire:
			Liste_file_show_cdp=glob.glob(repertoire+'/*.log')
			for file_show_cdp in Liste_file_show_cdp:
				file_show_cdp__=file_show_cdp.split('/')[-1]
				equipement__=getEquipementFromFilename(file_show_cdp__).upper()
				self.cdpEntries_DC[equipement__]=cdpEntries(output=file_show_cdp)
				#pdb.set_trace()*******
			self.interco=self.init_interconnexion()
		if dump:
			self.load(dump)
			
		#pdb.set_trace()
			
	def __str__(self):
	
		resultat=StringIO()
		for hostname in self.cdpEntries_DC.keys():
			resultat.write("Equipement:"+hostname+"\n")
			resultat.write(str(self.cdpEntries_DC[hostname]))
			
		resultat_str=resultat.getvalue()
		resultat.close()
			
		return resultat_str
		
	def init_interconnexion(self):
		resultat=interconnexions()
		for hostname in self.cdpEntries_DC.keys():
			for entry__ in self.cdpEntries_DC[hostname].entries:
				resultat.add_element(interconnexion(hostname,entry__.interface,entry__.hostname,entry__.interface_neighbor))
			
		return resultat
		
	def print_interconnexion(self):
		print(self.interco)
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
		
		try:
			self.cdpEntries_DC=dc.cdpEntries_DC
			self.interco=dc.interco

		except:
			print('ERROR')
			
	def getNeighbor(self,equipement,interface):
		resultat=None
		
		try:
			#pdb.set_trace()
			resultat=self.cdpEntries_DC[equipement.upper()].entries_dict[getLongPort(interface)]
		
		except KeyError:
			pass
			
		return resultat
		
	def getNeighbors(self,equipement):
		resultat=None
		
		try:
			#pdb.set_trace()
			resultat=self.cdpEntries_DC[equipement.upper()].entries_dict
		
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
	parser.add_argument("-s", "--save",action="store",help=u"Résultat dans fichier dump",required=False)
	args = parser.parse_args()
	
	if args.repertoire:
		A=DC_cdp(repertoire=args.repertoire)
	elif args.dumpfile:
		A=DC_cdp(dump=args.dumpfile)
		
	print(str(A))
	
	if args.save:
		A.save(args.save)
		
	A.print_interconnexion()