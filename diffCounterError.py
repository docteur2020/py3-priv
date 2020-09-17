#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


from ParsingShow import ParseIntCounterError
from dictdiffer import diff
import argparse
from pprint import pprint
import pdb
import ntpath
import glob
import os.path, time
import pyparsing as pp


def getEquipementFromFilename(str):
	resultat=None
	NomFile1=pp.Word(pp.alphanums+'-')+pp.Literal('_').suppress()+pp.Word(pp.nums,min=8,max=8).suppress()+pp.Literal('_').suppress()+pp.Word(pp.nums+'hms').suppress()+pp.Literal('.log').suppress()
	NomFile2=pp.Word(pp.alphanums+'-_')+pp.Literal('.log').suppress()
	NomFile3=pp.Word(pp.alphanums+'-_')+pp.Suppress(pp.Optional(pp.CaselessLiteral('.dns')+pp.Word(pp.nums,min=2,max=2)+pp.Literal('socgen.log')))
	NomFile=pp.MatchFirst([NomFile1,NomFile2,NomFile3])
	resultat=NomFile.parseString(str).asList()[0]
	
	return resultat
	
def init_dict_equipement_file(rep):
	equipements_res={}
	for files_dir in rep:
		file_cur=files_dir.split('/')[-1]
		equipement_cur=getEquipementFromFilename(file_cur)
		equipements_res[equipement_cur]=files_dir
		
	return equipements_res
	
def compare_file(file1,file2):
		print('\n')
		print_time_file(file1)
		print_time_file(file2)
		print('\n')
		result=diff(ParseIntCounterError(file1),ParseIntCounterError(file2))
		
		pprint(add_diff(list(result)))

def add_diff(list_diff):
	resultat=[]
	for entry in list_diff:
		resultat.append(entry+('diff',int(entry[2][1])-int(entry[2][0])))
		
	return resultat
	
def print_time_file(file__):
	print("last modified "+ntpath.basename(file__)+":  "+time.ctime(os.path.getmtime(file__)))
	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file1')
	parser.add_argument('file2')
	parser.add_argument('-d', '--directory',action="store_true", help='directory mode')
	
	args = parser.parse_args()
	
	if not args.directory:
		print('\n')
		print_time_file(args.file1)
		print_time_file(args.file2)
		print('\n')
		result=diff(ParseIntCounterError(args.file1),ParseIntCounterError(args.file2))
		
		pprint(add_diff(list(result)))
		
	else:
		liste_dir1=glob.glob(args.file1+'/*.log')
		liste_dir2=glob.glob(args.file2+'/*.log')	
		
		equipements__1=init_dict_equipement_file(liste_dir1)
		equipements__2=init_dict_equipement_file(liste_dir2)

		
		for equipement__ in equipements__1.keys():
			print("\n")
			print("*"*30)
			print("Equipement:",equipement__.upper())
			try:
				compare_file(equipements__1[equipement__],equipements__2[equipement__])
			except KeyError as e:
				print(e)
				print("compléter les log de:",equipement__)
				pass
