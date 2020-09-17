#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import re
import sys
import os
from ipcalc import Network , IP
import argparse
import pdb
import random


class IpError(Exception):
	"Classe Exception pour le format IP"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		
		self.message[0]=u'Erreur inconnue ou non traitée'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un réseau IPV4 valide'
		super(IpError, self).__init__(self.message[code])
 


def print_verbose(line,option_v=False,level=1):

	if option_v:
		if option_v >= level:
			print(line)
	#print("OPTION_V",str(option_v))


		
 
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--Verbose",help="Mode Debug Verbose",action="count",required=False)
	parser.add_argument("-i","--ips",action="store",help="Fichier contenant les IP",required=True)
	parser.add_argument("-n","--network",action="store",help="Fichier contenant les réseaux",required=True)
	parser.add_argument("-s","--save",action="store",help="Fichier de sauvegarde des IP extraites",required=False)

	args = parser.parse_args()
	
				
	with open(args.network) as file_network:
		try:
			liste_network=[ Network(net__) for net__ in file_network.read().split() ]
		except:
			raise IpError(code=2,value1="voir fichier")
			
	with open(args.ips) as file_ips:
		try:
			liste_ip=[ IP(ip__) for ip__ in file_ips.read().split() ]
		except:
			raise IpError(code=1,value1="voir fichier")
		
	net__dict={}
	for net__ in liste_network:
		net__dict[str(net__)]=[]
		for ip__ in liste_ip:
			if ip__ in net__:
				net__dict[str(net__)].append(str(ip__))
				
				
	print_verbose(str(net__dict),option_v=args.Verbose,level=2)
	
	ips_extracted=[]
	
	for net__ in net__dict:
		if net__dict[net__]:
			ips_extracted.append(random.choice(net__dict[net__]))
			
	print_verbose(str(ips_extracted),option_v=args.Verbose,level=1)
	
	if args.save:
		with open(args.save,'w') as filesave:
			filesave.write("\n".join(ips_extracted))