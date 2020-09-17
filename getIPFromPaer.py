#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import argparse
import pdb
import sys
import os
from pexpect import pxssh
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect , exceptions
import pyparsing as pp


from ping3ip import pingip , pingResult

PAER="192.64.10.129"

def ExtractIPfromTrace(trace_or_log):
	resultat=None
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	bytes=pp.Suppress(pp.Word(pp.nums+"()")+pp.Literal('bytes of data.'))
	IP=pp.Suppress(pp.Literal('PING')+pp.Word(pp.alphanums+"._-")+pp.Literal("("))+ipAddress+pp.Literal(")")+bytes
	
	try:
		resultat__parse=next(IP.scanString(trace_or_log))
		resultat=resultat__parse[0][0]
	except StopIteration:
		print("Nom inconnu")
		pass
	
	return resultat
	
def getIPFromtrace(equipement,verbose=False):
	resultat=None
	A_result=pingResult()
	A__=pingip(PAER,equipement,count=2,verbose=verbose,occurence=1,description="test ip paer:"+equipement,resultat=A_result)
	A__.start()
	A__. attendre_fin()
	resultat=ExtractIPfromTrace(A__.resultat_brut[0][1])
	
	return resultat
	

if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	parser.add_argument("-e", "--equipment",action="store",type=str, help="Nom de l'équipement",required=True)
	parser.add_argument("-V", "--Verbose",action="store_true",help="Affiche le stdout / Verbose",required=False)
	
	args = parser.parse_args()
	print(getIPFromtrace(args.equipment,args.Verbose))