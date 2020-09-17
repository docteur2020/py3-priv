#!/usr/bin/env python3.7
# -*- coding: utf-8 -*- 

from __future__ import unicode_literals

import time
from time import gmtime, strftime , localtime
import threading
import sys
import os
import argparse
import pdb
import re
from io import StringIO 
from io import BytesIO
from pexpect import pxssh
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect , exceptions
import pickle
from ipcalc import *
import pyparsing as pp

PAER="192.64.10.129"

def processFile(fileName):
    listOfIPs=[]
    try:
        o=open(fileName,'r')
    except Exception as e:
        print("'/!\\ Error during '%s' opening. Msg: '%s' /!\\"%(fileName,e),file=sys.stderr)
        sys.exit(1)

    for line in o:
        line=line.rstrip('\r\n')
        line=re.sub(r'\s+','',line)
        line=re.sub(r'#.*$','',line)
        if not line:
            continue
        listOfIPs.append(line.rstrip('\r\n'))

    o.close()
    return listOfIPs


class mpingip(object):
	"lance un ping via un rebond"
	
	def __init__(self,bastion,network,verbose=False):
		self.bastion=bastion
		self.network=network
		self.verbose=verbose
		self.timeout=500
		self.up=[]
		self.down=[]
		self.proxy=pxssh.pxssh()
		self.rebond()
		self.netping()
		self.resultat=self.FormatageOutput()
		
	def FormatageOutput(self):
	
		resultat=[]
		octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
		ipAddress=pp.Combine(octet + ('.'+octet)*3)
		ligne=pp.Suppress(pp.Literal('|'))+ipAddress+pp.Suppress(pp.Literal('|'))+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
		
		parserResult__=ligne.scanString(self.resultat_raw)
		
		for result in parserResult__:
			try:
				resultat.append(result[0][0])
			except IndexError as e:
				pass
		
		
		return resultat
		
	def netping(self):
		regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#','\r[a-zA-Z]\\S+\$','\n[a-zA-Z]\\S+\$','\$']
		data_output = BytesIO()
		self.proxy.logfile_read = data_output
		now=time.time()
		time_ms=repr(now).split('.')[1][:3]
		try:
			self.proxy.sendline('multiping  '+self.network+" -u")
			expect_value=self.proxy.expect(["RTT\(ms\)","Error"],timeout=self.timeout)
			if expect_value==0:
				self.proxy.sendcontrol('c')
				self.proxy.expect(regex_match)
				time_=strftime("%Y%m%d_%Hh%Mm%Ss.", localtime())+time_ms
				self.resultat_raw=data_output.getvalue().decode('UTF-8')
			if expect_value==1:
				self.resultat_raw=""
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login")
			self.status="FAILED PING:"+str(e)+'=='+self.ip
			print(str(e))
		
		except ExceptionPexpect as ep:
			print("pexpect failed on login")
			self.status="FAILED MPING:"+str(e)+'=='+self.network
			print(str(ep))
		
		except TIMEOUT:
			print("Timeout...")
			self.status=self.status="FAILED PING:"+"TIMEOUT SSH"+'=='+self.network
			
		self.proxy.close()
		
	def rebond(self):
		try:
			regex_match=['\r[a-zA-Z]\\S+#','\n[a-zA-Z]\\S+#']
			if self.verbose:
				self.proxy.logfile = sys.stdout.buffer
			self.proxy.login("192.64.10.129",'x112097','B2rn1s12345!')
				
		except pxssh.ExceptionPxssh as e:
			print("pxssh failed on login:")
			self.status="FAILED:"+str(e)
			print(str(e))
			

def saveListToFile(list__,filename):

	with open(filename,'w+') as ResultFile:
		ResultFile.write("\n".join(list__))
		

def main():
	parser=argparse.ArgumentParser(description="extract host IP ICMP up")
	parser.add_argument('--file','-f',dest='file',action='store',help='File containing 1 IP per line.',required=True)
	parser.add_argument('--result','-r',dest='result',action='store',help='File host UP',required=True)
	parser.add_argument('--verbose','-V',dest='verbose',action='store_true',default=False,help='File host UP')
	args=parser.parse_args()
	
	resultat=[]
	for net__ in processFile(args.file):
		resCurObj=mpingip(PAER,net__,verbose=args.verbose)
		resultat+=resCurObj.resultat
		time.sleep(0.8)
	
	saveListToFile(resultat,args.result)
	print(str(resultat))

if __name__ == '__main__':
    main()