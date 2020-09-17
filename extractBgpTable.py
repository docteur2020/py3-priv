#!/usr/bin/env python3.7
# coding: utf-8


from ParsingShow import ParseBgpTable,writeCsv
from ipaddress import ip_address as ipaddr
import csv
import checkroute
import sys
import os
import argparse
import pickle
import pdb

def getClassfulIP(ip__):
	resultat="INDETERMINE"
	try:
		if ipaddr(ip__) <= ipaddr('127.255.255.255'):
			resultat='A'
		elif ipaddr(ip__) >= ipaddr('128.0.0.0') and ipaddr(ip__) <= ipaddr('191.255.255.255'):
			resultat='B'
		elif ipaddr(ip__) >= ipaddr('192.0.0.0') and ipaddr(ip__) <= ipaddr('223.255.255.255'):
			resultat='C'
		elif ipaddr(ip__) >= ipaddr('224.0.0.0') and ipaddr(ip__) <= ipaddr('239.255.255.255'):
			resultat='D'
		elif ipaddr(ip__) >= ipaddr('240.0.0.0') and ipaddr(ip__) <= ipaddr('255.255.255.255'):
			resultat='E'
			
	except ValueError as E:
		print(E)
		
	return resultat
	
def getDefaultMask(ip__):
	resultat="INDETERMINE"
	Dict_class={'A':'8','B':'16','C':'24','D':'32','E':'32'}
	if ip__=='0.0.0.0':
		resultat=0
	else:
		Class__=getClassfulIP(ip__)
		try:
			resultat=Dict_class[Class__]
		except:
			pass
	return resultat
	
class NH(object):
	"Classe NextHop"
	
	def __init__(self,Code,IP):
		"Constructeur"
		self.attribut=Code
		self.nexthop=IP
	
	def __str__(self):
		"Affichage"
		return self.attribut+";"+self.nexthop
		
	def __ne__(self,other):
		return self.IP != other.IP
			
	def __eq__(self,other):
		return self.IP == other.IP
			
	def is_eBGP(self):
		result=True
		
		if 'i' in self.attribut:
			result=False
			
		return result
		
class prefix(object):
	"definit un prefix BGP"
	
	def __init__(self,reseau="0.0.0.0",nexthops=[]):
		"Constructeur"
		
		self.reseau=reseau
		self.nexthops=nexthops	
		
	
	def __str__(self):
		"Affichage"
		resultat="P:"+str(self.reseau)+":"
		for NH__ in self.nexthops:
			resultat=resultat+"NH:"+str(NH__)+";"
		
		return resultat
		
	
class PE(object):
	"definit un PE"
	def __init__(self,nom,Vrfs=[],Prefixs={},output=None,dump=None):
		"Constructeur"
		self.nom=nom
		self.Vrfs=Vrfs
		self.Prefixs=Prefixs
		
		if output:
			table__=ParseBgpTable(output)
			
			for Vrf__ in table__.keys():
				self.addVrf(Vrf__)
				self.Prefixs[Vrf__]=[]
				try:
					for entry__ in table__[Vrf__]:
						self.Prefixs[Vrf__].append(prefix(entry__[0],entry__[1]))
				except TypeError:
					self.Prefixs[Vrf__].append(prefix())
		elif dump:
			self.load(dump)
			

				
				
	def __str__(self):
		prefix_str=""
		for Vrf__ in self.Prefixs.keys():
			prefix_str=prefix_str+Vrf__+":"
			for prefix__ in self.Prefixs[Vrf__]:
				prefix_str=prefix_str+str(prefix__)
			prefix_str=prefix_str+'\n'	
			
		return(self.nom+":"+prefix_str)
	
	def __list__(self):
		result=[]
		prefix_str=""
		for Vrf__ in self.Prefixs.keys():
			prefix_str=prefix_str+Vrf__+":"
			for prefix__ in self.Prefixs[Vrf__]:
				result.append([self.nom,Vrf__,prefix__])

			
		return result
		
	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		pe__=None
		
		with open(filename,'rb') as file__:
			pe__=pickle.load(file__)
		
		try:
			self.nom=pe__.nom
			self.Vrfs=pe__.Vrfs
			self.Prefixs=pe__.Prefixs
	
			
		except:
			print('ERROR LOAD DUMP')
			
	def addVrf(self,Vrf):
		if Vrf not in self.Vrfs:
			self.Vrfs.append(Vrf)
			
	def addPrefix(self,Vrf,Prefix):
		#pdb.set_trace()
		try:
			self.Prefixs[Vrf].append(Prefix)

		except KeyError:
			self.Prefixs[Vrf]=[]
			self.Prefixs[Vrf].append(Prefix)
			
		try:
			self.Prefixs_dict[Vrf][str(Prefix.reseau)]=Prefix.nexthops
		except KeyError:
			self.Prefixs_dict[Vrf]={}
			self.Prefixs_dict[Vrf][str(Prefix.reseau)]=Prefix.nexthops
			
	def extract_only_1NH(self):
		for Vrf__ in self.Prefixs.keys():
			for prefix__ in self.Prefixs[Vrf__]:
				if len(prefix__.nexthops)==1:
					print("["+Vrf__+"]"+str(prefix__))
					
	def export_csv(self,fichier):
		writeCsv(self.__list__(),fichier)

			
			
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-o", "--output",action="store",help="Contient le fichier output")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump")
	parser.add_argument("-s", "--savefile",action="store",help="Save to dump File")
	parser.add_argument("-e", "--exportcsv",action="store",help="Résultat sous forme fichier csv",required=False)
	args = parser.parse_args()
	

		
		
	if args.output:
		pe__=PE("tig-d0",output=args.output)
		pe__.extract_only_1NH()
		
		if args.savefile:
			pe__.save(args.savefile)
			
		if args.exportcsv:
			pe__.export_csv(args.exportcsv)
			
	elif args.dumpfile:
		pe__=PE("tig-d4",dump=args.dumpfile)
		pe__.extract_only_1NH()
		
		if args.exportcsv:
			pe__.export_csv(args.exportcsv)
			
	
			
				
	
		
	
