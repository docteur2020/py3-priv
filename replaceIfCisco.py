#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import pyparsing as pp
import argparse
import re
import pdb
import csv
import glob



if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	

	parser.add_argument("-r", "--repertoire",action="store",help="Contient les configurations NxOS anciennes equipements IOS")
	parser.add_argument("-c", "--correspondance",action="store",help="Fichier avec la correspondance:old equipement;old interface;new equipement;new interface")
	group1.add_argument("-v", "--vrf",action="store_true",help="Parse les show vrf")
	group1.add_argument("-a", "--arp",action="store_true",help="Parse les show ip arp")
	group1.add_argument("-m", "--mac",action="store_true",help="Parse les show mac")
	group1.add_argument("-d", "--description",action="store_true",help="Parse les show inerface description")
	mode_desc.add_argument("-D", "--Descr",action="store",help="Fichier ou repertoire description")
	mode_desc.add_argument("-M", "--Mac",action="store_true",help="Parse les show mac")
	mode_desc.add_argument("-A", "--All_desc",action="store_true",help=u"Affiche tous les ports meme sans informations")
	mode_desc.add_argument("-C", "--Complement_ARP",action="store",help=u"Fichier ou repertoire ARP Cisco/nexus",required=False)
	parser.add_argument("-c", "--csvFichier",action="store",help="fichier resultat en csv",required=False)