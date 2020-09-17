#!/usr/bin/env python3.7
# coding: utf-8

import argparse


from checkFabricpathVlan  import ExtractInfoVlan , Vlan

if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	parser.add_argument("-r", "--repertoire",action="store",help="repertoire contenant les configurations sh run",required=True)
	parser.add_argument("--host1",action="store",help="equipement 1 old",required=True)
	parser.add_argument("--host2",action="store",help="equipement 2 cible",required=True)
	parser.add_argument("-n","--nat",action="store",help="NAT Vlan File",required=False)
	
	args = parser.parse_args()
	
	Vl__=ExtractInfoVlan(repertoire=args.repertoire)
	
	liste_to_press=Vl__.diff(args.host1,args.host2)
	
	print("Vlan to suppress:")
	for vlan__ in liste_to_press:
		print(vlan__)
		
	if args.nat:
		liste_warning=Vl__.check_vlan_presence(args.host1,args.host2,args.nat)
		
		print("Vlan in warning:")
		for vlan__ in liste_warning:
			print(vlan__)
			
		print("Deep check:")
		Vl__.deep_diff(args.host1,args.host2,args.nat)
	