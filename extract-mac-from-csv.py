#!/usr/bin/env python3.7
# coding: utf-8

import re
import csv
import argparse
import pdb


class hostnames(object):
	def __init__(self,file_csv):
	
		macs={}
		with open(file_csv, 'r') as csvfile:
			csv_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
			self.macs={}

			for row in csv_reader:
				hostname=row[0]
				mac__1=self.mac_to_cisco(row[2])
				ip__1=row[3]
				mac__2=self.mac_to_cisco(row[4])
				ip__2=row[5]
				mac__3=self.mac_to_cisco(row[6])
				ip__3=row[7]
				mac__4=self.mac_to_cisco(row[8])
				ip__4=row[9]
				if mac__1 != 'NULL' and ip__1 != '0.0.0.0':
					if mac__1 not in macs.keys():
						macs[mac__1]=[[hostname,ip__1]]
					else:
						if [hostname,ip__1] not in macs[mac__1]:
							macs[mac__1].append([hostname,ip__1])
				if mac__2 != 'NULL' and ip__2 != '0.0.0.0':
					if mac__2 not in macs.keys():
						macs[mac__2]=[hostname,[ip__2]]
					else:
						if [hostname,ip__2] not in macs[mac__2]:
							macs[mac__2].append([hostname,ip__2])
				if mac__3 != 'NULL' and ip__3 != '0.0.0.0':
					if mac__3 not in macs.keys():
						macs[mac__3]=[hostname,[ip__3]]
					else:
						if [hostname,ip__3] not in macs[mac__3]:
							macs[mac__3].append([hostname,ip__3])
						
				if mac__4 != 'NULL' and ip__4 != '0.0.0.0':
					if mac__4 not in macs.keys():
						macs[mac__4]=[hostname,[ip__4]]
					else:
						if [hostname,ip__4] not in macs[mac__4]:
							macs[mac__4].append([hostname,ip__4])
			
			self.macs=macs
		
	def mac_to_cisco(self,mac_srv):
		
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
			else:
				resultat='NULL'
		
				
		else:
			resultat='NULL'


		return resultat
		
	def get_info_mac(self,mac__):
		resultat="NONE"
		try:
			resultat=self.macs[mac__]
		except KeyError:
			pass
			
		return  resultat
		
	def get_info_macs(self,file_mac):
		with open(file_mac,'r') as fich__:
			for mac in fich__:
				mac__=mac.strip()
				print(mac__+";"+str(self.get_info_mac(mac__)))
				

				
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--csv",action="store",help="Contient le fichier resultat en csv",required=True)
	parser.add_argument("-l", "--liste_mac",action="store",help="Contient la liste des macs a traiter",required=False)
	args = parser.parse_args()
	
	if args.csv:
		CSV=hostnames(args.csv)
		print("OK")

		if args.liste_mac:
			print("MAC trouve")
			CSV.get_info_macs(args.liste_mac)
		