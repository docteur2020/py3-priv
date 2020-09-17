#!/usr/bin/env python3.7
# coding: utf-8

import textfsm
import argparse


if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument('fichier',help="fichier interface à parser")
	parser.add_argument("-t","--textfsm", action="store",help="fichier textfsm",required=True)
	
	args = parser.parse_args()
	
	with open(args.fichier,'r') as file:
		all_lines=file.read()
	
	fsm = textfsm.TextFSM(open(args.textfsm))
	
	fsm_results=fsm.ParseText(all_lines)
	
	print(fsm_results)
	
