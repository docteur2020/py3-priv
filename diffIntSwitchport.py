#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


from ParsingShow import ParseSwitchPort
from dictdiffer import diff
import pyparsing as pp
import argparse
from pprint import pprint
import pdb
import ntpath
import re
import sys

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

def filter_info(list_parser,filter=None,replace=""):
	resultat={}
	if replace:
		tobereplaced=parseSed(replace)
		if filter:
			for entry in list_parser.keys():
				if re.search(filter,entry):
					resultat[entry.replace(tobereplaced[0],tobereplaced[1])]=list_parser[entry]
		else:
			for entry in list_parser.keys():
				resultat[entry.replace(tobereplaced[0],tobereplaced[1])]=list_parser[entry]
	else:
		if filter:
			for entry in list_parser.keys():
				if re.search(filter,entry):
					resultat[entry]=list_parser[entry]
		else:
			for entry in list_parser.keys():
				resultat[entry]=list_parser[entry]
				
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
	parser.add_argument("-r", "--replace", action="store",help="remplace notation sed s// uniquement sur file1",required=False)
	
	args = parser.parse_args()
	print('\n')
	print_time_file(args.file1)
	print_time_file(args.file2)
	print('\n')
	result=diff(filter_info(ParseSwitchPort(args.file1),filter=args.filter1,replace=args.replace),filter_info(ParseSwitchPort(args.file2),filter=args.filter2))
	
	pprint(print_diff(result))
	
