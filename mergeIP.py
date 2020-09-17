#!/usr/bin/env python3.7
# -*- coding: utf-8 -*- 

import argparse
import supernets
import pdb

if __name__ == '__main__':
	
	"Fonction principale"
	parser = argparse.ArgumentParser()	
	parser.add_argument("-i", "--input_file",action="store",type=str,help="Fichier contenant la liste de reseaux")
	parser.add_argument("-o", "--output_file",action="store",type=str,help="Fichier de resultat contenant la liste summarize") 
	args = parser.parse_args()
	
	resultat=supernets.main__(args.input_file,args.output_file)
	
	print(resultat)


	