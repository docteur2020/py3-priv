#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import re
import sys
import os
import argparse
import pdb



if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--Verbose",help="Mode Debug Verbose",action="count",required=False)
	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file')
		mode="FILE"

	else:
		mode="STDIN"
		
	args = parser.parse_args()
	
	if mode=="FILE":
		param_file=args.file
		with open(param_file,'r') as file:
			all_lines=file.read()

	elif mode=="STDIN":
		param_file=None
		all_lines=sys.stdin.read()

	indice=1
	ligne_traite={}
	
	nb_line_suppressed=0
	for line in all_lines.split('\n'):
		comp=','.join(line.split(',')[3:])
		try:
			sequence=int(eval(line.split(',')[0]))
		except:
			print(line)
			continue
		if comp not in ligne_traite.keys():
			ligne_traite[comp]=line
			new_sequence='"'+str(sequence-nb_line_suppressed)+'"'
			print(','.join([new_sequence]+line.split(',')[1:]))
		else:
			nb_line_suppressed+=1
		
	if args.Verbose:
		print("\n\nNombre de ligne supprimées:"+str(nb_line_suppressed))