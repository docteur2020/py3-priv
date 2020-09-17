#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import argparse
import pdb
import dns.resolver

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
		resultat.append((IP,name_cur))
		
	return resultat
	
	
def rprint(resultat):
	for entry in resultat:
		print(entry[0]+';'+str(entry[1]))
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-f", "--fichier",action="store",help="Contient le fichier",required=False)
	parser.add_argument("-o", "--output",action="store",help="Contient le fichier",required=False)
	args = parser.parse_args()
	
	if args.fichier:
		with open(args.fichier,"r") as ip_fich:
			liste_ip_str=ip_fich.read().split()
			
			#print(liste_ip_str)
			
			resultat=getReverseDns(liste_ip_str)
			
			rprint(resultat)