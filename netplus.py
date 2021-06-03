#!/usr/bin/env python3.8
# coding: utf-8

from __future__ import unicode_literals


import re
import argparse
import pdb
import io
import os
import sys
import pyparsing as pp
from netaddr import IPAddress , IPNetwork



def replaceIP( strInput,offset):
	Output=io.StringIO()
	def replace_ip(t):
		return IPAddress(t[0])+int(offset)
			

	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=(pp.Combine(octet + ('.'+octet)*3))
	ipAddress.setParseAction(replace_ip)

	for line in strInput.split('\n'):
		new_line=ipAddress.transformString(line)
		
		Output.write(new_line+'\n')
		
	outputStr=Output.getvalue()
	Output.close()

	return outputStr
			
if __name__ == '__main__':
	"Useful to Migrate IP Network"
	
	parser = argparse.ArgumentParser()

	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('offset')
		parser.add_argument('file_src')
		mode="FILE"


	else:
		parser.add_argument('offset')
		mode="STDIN"
		
	args = parser.parse_args()
		
	if mode=="FILE":
		with open(args.file_src,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		all_lines=sys.stdin.read()
	

			
	output=replaceIP(all_lines,args.offset)
	print(output)