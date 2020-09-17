#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import re
import sys
import os
from ipcalc import Network , IP
import argparse
import pdb

def genere_mask_dict():
	resultat={}
	for i in range(0,33):
		resultat[" "+Network("0.0.0.0/"+str(i)).netmask().__str__()]=str(i)
		
	return resultat
	

def genere_mask_dict_space():
	resultat={}
	for i in range(0,33):
		resultat[" "+Network(" 0.0.0.0/"+str(i)).netmask().__str__()]="/"+str(i)
		
	return resultat

class SedDictLine(object):
	"Classe template de configuration"
	def __init__(self,lines):
		self.lines=lines
		self.mask_dict=genere_mask_dict_space()
		
	def replace_mask(self):
		"Liste_parametre=Liste de couple (PARAM,VALEUR) renvoie un String"
		resultat=self.lines
		for mask in self.mask_dict.keys():
			try:
				resultat=resultat.replace(mask,self.mask_dict[mask])
			except:
				pdb.set_trace()
			
		return resultat
	
def print_verbose(line,option_v=False,level=1):

	if option_v:
		if option_v >= level:
			print(line)
			


if __name__ == '__main__':
	"Fonction principale"	
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--Verbose",help="Mode Debug Verbose",action="count",required=False)
	parser.add_argument("-n", "--nospace",action="store_true",help="remplace par le nombre de bit",required=False)
	
	if os.isatty(0):
		parser.add_argument('file')
		mode="FILE"

	else:
		parser.add_argument('network')
		mode="STDIN"
		
	args = parser.parse_args()
	
	if mode=="FILE":
		print_verbose('File:'+args.file,args.Verbose)
		param_file=args.file
		with open(param_file,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		param_file=None
		all_lines=sys.stdin.read()
		
	objDictLine=SedDictLine(all_lines)
	print(objDictLine.replace_mask())
