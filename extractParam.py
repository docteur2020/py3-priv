#!/usr/bin/env python3.7
# coding: utf-8

import pyparsing as pp
import argparse
import os
import pdb

def getParam(string__):
	resultat=[]
	Param=pp.Combine(pp.Literal('<')+pp.Word(pp.alphanums+'-_/')+pp.Literal('>'))
	resultat_pyparse=Param.scanString(string__)
	
	for parsingEntry in resultat_pyparse:
		try:
			if parsingEntry[0].asList()[0][1]:
				resultat.append(parsingEntry[0].asList()[0])
			else:
				Resultat[ parsingEntry[0].asList()[0][0].replace('\r','')]=parsingEntry[0].asList()[0][1]
		except KeyError as E:
			print(E)
		except IndexError as E:
			print(E)
			pdb.set_trace()

	
	return resultat

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	
	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file_src')
		mode="FILE"

	
	else:
		mode="STDIN"

	args = parser.parse_args()
	
	if mode=="FILE":
		with open(args.file_src,'r') as file:
			all_lines=file.read()
	else:
		all_lines=sys.stdin.read()
	
	print(str(set(getParam(all_lines))))
	
