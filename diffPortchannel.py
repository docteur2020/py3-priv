#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


from ParsingShow import ParsePortChannelCiscoFile , getEquipementFromFilename
from dictdiffer import diff
import pyparsing as pp
import argparse
from pprint import pprint
import pdb
import ntpath
import re
import sys
import cache as cc

import os.path, time

def PoToDict(list_po):
	resultat={}
	try:
		for po in list_po:
			resultat[po[0]]=po[1:]
	except KeyError:
		pdb.set_trace()
	
	return resultat

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
	
def test_presence_fex(filter,infoPo):
	
	resultat=False
	for interface in infoPo[2]:
		if re.search(filter,interface[0]):
			resultat=True
	
	return resultat
	

def filter_info(list_parser__,filter=None,replace="",infoMig=None):
	resultat={}
	list_parser=PoToDict(list_parser__)
	if replace:
		tobereplaced=parseSed(replace)
		if filter:
			for entry in list_parser.keys():
				if test_presence_fex(filter,list_parser[entry]):
					resultat[entry.replace(tobereplaced[0],tobereplaced[1])]=list_parser[entry]
		else:
			for entry in list_parser.keys():
				resultat[entry.replace(tobereplaced[0],tobereplaced[1])]=list_parser[entry]
	elif infoMig:
		infomigPo=infoMig.getValue()
		if filter:
			for entry in list_parser.keys():
				if test_presence_fex(filter,list_parser[entry]):
					if entry in infomigPo['po']:
						resultat[infomigPo['po'][entry]]=[list_parser[entry][0].replace(entry,infomigPo['po'][entry]) ]+list_parser[entry][1:]
					else:
						resultat[entry]=list_parser[entry]
						

							
		else:
			for entry in list_parser.keys():
				if entry in infomigPo['po']:
					resultat[infomigPo['po'][entry]]=[list_parser[entry][0].replace(entry,infomigPo['po'][entry]) ]+list_parser[entry][1:]
				else:
					try:
						resultat[entry]=list_parser[entry]
					except TypeError as e:
						pdb.set_trace()
						print(e)
						raise(e)
						
		for fex__ in infomigPo['fex']:
			res_cur=resultat
			resultat=eval(str(res_cur).replace('Eth'+fex__,'Eth'+infomigPo['fex'][fex__]))
	
	else:
		if filter:
			for entry in list_parser.keys():
				if test_presence_fex(filter,list_parser[entry]):
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
	parser.add_argument("-i", "--infoMig", default=None,action="store_true",help="remplace avec les informations de migrations",required=False)
	
	args = parser.parse_args()
	print('\n')
	print_time_file(args.file1)
	print_time_file(args.file2)
	print('\n')
	
	if args.infoMig:
		try:
			host_source=getEquipementFromFilename(ntpath.basename(args.file1)).upper()
			host_dest=getEquipementFromFilename(ntpath.basename(args.file2)).upper()
			tag_cur="MIGFEX_"+host_source+"_"+host_dest
			infomig=cc.Cache(tag_cur)
			if infomig.isOK():
				print("info de migration trouvée dans le cache")
			else:
				pdb.set_trace()
				print("pas de cache")
				
		except ValueError as E:
			print(E)
			print("Verifiez le nom des fichiers le hostname doit apparaître")
			sys.exit(1)
	else:
		infomig=None
		
	result=diff(filter_info(ParsePortChannelCiscoFile(args.file1),filter=args.filter1,replace=args.replace,infoMig=infomig),filter_info(ParsePortChannelCiscoFile(args.file2),filter=args.filter2))
	
	pprint(print_diff(result))
	
