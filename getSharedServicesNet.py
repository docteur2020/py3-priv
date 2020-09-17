#!/usr/bin/env python3.7
# coding: utf-8

import argparse
from connexion import *
from ParsingShow  import ParseBgpTableXRStr
import cache as cc
from time import gmtime, strftime , localtime
import pdb

DIR_RESULT='/home/x112097/RESULT/RVP_SHAREDSERVICES/BGP'

def getBgpInterface(equipment__,vrf,options):

	BGPTable=None
	
	commande=f'sh bgp vrf {vrf} {options}'
	con_get_BGPTable_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shbgp_rvp_shared_services.log","TMP",commande,timeout=300,verbose=False)
	BGPTable=con_get_BGPTable_cur.launch_withParser(ParseBgpTableXRStr)
	
	return BGPTable
	
def main(equipment__):
	BGPCur=getBgpInterface(equipment__,'RIX','regexp ^64908')
	AllPrefix=[ entry[0] for entry in BGPCur['RIX'] ]
	timestamp=strftime("_%Y%m%d_%Hh%Mm%Ss", localtime())
	FileResult=f"{DIR_RESULT}/{equipment__}{timestamp}.txt"
	with open(FileResult,'w+') as file_w:
		file_w.write("\r\n".join(AllPrefix))
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-e","--equipment",action="store",help="PE",default='ORI-C1')
	args = parser.parse_args()
	
	main(args.equipment)