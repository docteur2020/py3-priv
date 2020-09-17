#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


from ParsingShow import ParseRunInterfaceDeeperFile
from dictdiffer import diff
import pyparsing as pp
import argparse
from pprint import pprint
import pdb
import ntpath
import re
import sys
import yaml

import os.path, time

def parseSed(Str__):
	resultat=[]
	Sed=pp.Literal('s/').suppress()+pp.Word(pp.alphanums)+pp.Literal('/').suppress()+pp.Word(pp.alphanums)+pp.Literal('/').suppress()+pp.Optional(pp.Literal('g')).suppress()
	
	try:
		resultat=Sed.parseString(Str__,parseAll=True).asList()
	except pp.ParseException as e:
		print("Erreur parsing l'option replace")
		print("respecter la forme sed pour remplacer s/.../.../")
		sys.exit(1)
	
	return resultat
	
def replace_dict(dict__,str__,equipement):
	resultat=str__
	for key__ in dict__[equipement].keys():
		if re.search('[a-zA-Z]'+key__+'$',str__) or re.search('\s'+key__+'$',str__):
			resultat=str__.replace(key__,dict__[equipement][key__])
			break;
	return resultat

def filter_info(list_parser,filter=None,replace="",equipement=""):
	resultat={}
	
	if replace:
		if filter:
			for entry in list_parser[0].keys():
				if re.search(filter,entry):
					new_entry=replace_dict(replace,entry,equipement)
					resultat[new_entry]=list_parser[0][entry]
	
		else:
			for entry in list_parser[0].keys():
				new_entry=replace_dict(replace,entry)
				resultat[new_entry]=list_parser[0][entry]
	else:
		if filter:
			for entry in list_parser[0].keys():
				if re.search(filter,entry):
					resultat[entry]=list_parser[0][entry]
		else:
			for entry in list_parser[0].keys():
				resultat[entry]=list_parser[0][entry]
				
				
	return resultat


def print_diff(list_diff):
	resultat=[]
	for entry in list_diff:
		resultat.append(entry)
		
	return resultat
	
def print_time_file(file__):
	print("last modified "+ntpath.basename(file__)+":  "+time.ctime(os.path.getmtime(file__)))
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file1')
	parser.add_argument('file2')
	parser.add_argument("--filter1", action="store",help="filtre sur les interfaces (regex) file 1",required=False)
	parser.add_argument("--filter2", action="store",help="filtre sur les interfaces (regex) file 2",required=False)
	parser.add_argument("-r", "--replace", action="store",help="fichier yaml",required=False)
	parser.add_argument("-e", "--equipement", action="store",default='SC2ASWIPP001',help="fichier yaml",required=False)
	
	args = parser.parse_args()
	print('\n')
	print_time_file(args.file1)
	print_time_file(args.file2)
	print('\n')
	
	Remplacement={}
	if args.replace:
		with open(args.replace, 'r' ) as model_yml:
			Remplacement = yaml.load(model_yml,Loader=yaml.SafeLoader)
			
	result=diff(filter_info(ParseRunInterfaceDeeperFile(args.file1),filter=args.filter1,replace=Remplacement,equipement=args.equipement),filter_info(ParseRunInterfaceDeeperFile(args.file2),filter=args.filter2,equipement=args.equipement))
	
	pprint(print_diff(result))
	
