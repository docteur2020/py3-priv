#!/usr/bin/env python3.7
# coding: utf-8

import re
import csv
import xlrd
import argparse
import pdb
import pyparsing as pp
import io
import pickle
import csv
import glob



class hostnames(object):
	def __init__(self,repertoire="",dump=""):
	
		self.macs={}
		hexint = pp.Word(pp.hexnums,exact=2)
		macAddress = (pp.Combine(hexint + (':'+hexint)*5)).setParseAction(lambda tokens: self.mac_to_cisco(tokens[0]))
		if repertoire:
			Liste_file_quador=glob.glob(repertoire+'/*.csv')+glob.glob(repertoire+'/*.CSV')
			for file_quador in Liste_file_quador:
				with open(file_quador , 'r') as fich__:
					for ligne in fich__:
						column=ligne.split(';')
						try:
							
							mac_cur=column[5]
							if macAddress.parseString(mac_cur):
								if column[7]:
									self.macs[self.mac_to_cisco(mac_cur)]={'asset_id': column[7] , 'hostname':column[8] , 'model':column[9].strip() }
						except IndexError:
							pdb.set_trace()
						except pp.ParseException:
							pass
							
		elif dump:
			self.load(dump)
			
		
	def __str__(self):
		resultat=io.StringIO()
		
		for mac__ in self.macs.keys():
			resultat.write(mac__+":Info=>"+str(self.macs[mac__])+"\n")
		
		return resultat.getvalue()
		
	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		hostnames__=None
		
		with open(filename,'rb') as file__:
			hostnames__=pickle.load(file__)
			
		try:
			self.macs=hostnames__.macs
			
		except:
			print('ERROR LOAD DUMP')
	
	@staticmethod	
	def mac_to_cisco(mac_srv):
		
		resultat=mac_srv
		if mac_srv != 'NULL':
			if re.search("-",mac_srv):
				mac_cisco=mac_srv.split('-')
				try:
					resultat=(mac_cisco[0]+mac_cisco[1]+"."+mac_cisco[2]+mac_cisco[3]+"."+mac_cisco[4]+mac_cisco[5]).lower()
				except IndexError:
					pdb.set_trace()
			elif re.search(":",mac_srv):
				mac_cisco=mac_srv.split(':')
				try:
					resultat=(mac_cisco[0]+mac_cisco[1]+"."+mac_cisco[2]+mac_cisco[3]+"."+mac_cisco[4]+mac_cisco[5]).lower()
				except IndexError:
					pdb.set_trace()
			elif re.search("\.",mac_srv):
				resultat=mac_srv
			else:
				resultat='NULL'
		
				
		else:
			resultat='NULL'


		return resultat
		
	def get_info_mac(self,mac__):
		resultat=None
		try:
			resultat=self.macs[self.mac_to_cisco(mac__)]
		except KeyError:
			pass
			
		return  resultat
		
	def get_info_macs(self,macs__):
		for mac in macs__:
			mac__=mac.strip()
			print(mac__+";"+str(self.get_info_mac(mac__)))
				
				
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-r", "--repertoire",action="store",help="Contient les fichiers cador")
	parser.add_argument("-l", "--liste_mac",action="store",help="liste des macs a traiter",required=False)
	group1.add_argument("-d", "--dump",action="store",help="Chargement du dump")
	parser.add_argument("-s", "--save",action="store",help="Sauvegarde dans le fichier dump",required=False)
	parser.add_argument("-p", "--printing",action="store_true",help="Affichage",required=False)
	args = parser.parse_args()
	
	if args.repertoire:
		HOSTS__=hostnames(repertoire=args.repertoire)

		if args.liste_mac:
			print("MAC trouve")
			HOSTS__.get_info_macs(args.liste_mac.split(','))
			
		if args.save:
			print("Sauvegarde dans fichier DUMP:"+args.save)
			HOSTS__.save(args.save)
			
		if args.printing:
			print(HOSTS__.__str__())
			
	elif args.dump:
		HOSTS__=hostnames(dump=args.dump)
		print("Affichage")
		print(HOSTS__)
		if args.liste_mac:
			print("MAC trouve")
			HOSTS__.get_info_macs(args.liste_mac.split(','))
		if args.printing:
			print(HOSTS__.__str__())
	
