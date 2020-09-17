#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals

import re
import sys
import os
from ipcalc import Network , IP
import argparse
import pdb
import dns.resolver
import glob
from ipEnv import ifEntries , interface
import colored

PATH_IP_DUMP="/home/x112097/IP/DUMP/CISCO-ALL/"
LISTE_DNS=['192.16.207.80','184.12.21.17']

def getReverseDns(IP):
		resultat=[]
		for DNS in LISTE_DNS:
			name_cur=None
			try:
				name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),DNS).answer[0].__str__().split()[-1]
			except IndexError:
				pass
			if name_cur:
				resultat.append(name_cur)
		return resultat
		
def orange(text):
	return colored.fg('orange_1')+text+colored.attr('reset')

class trIpError(Exception):
	"Classe Exception pour grep-ip"
	
	def __init__(self,code=0,value1="None",value2="None"):
		self.message={}
		
		self.message[0]=u'Erreur inconnue ou non traitée'
		self.message[1]=u'La valeur:'+value1+u' n\'est pas une adresse IPV4 valide'
		self.message[2]=u'La valeur:'+value1+u' n\'est pas un réseau IPV4 valide'
		super(trIpError, self).__init__(self.message[code])
 
def genere_mask_list():
	return [ Network("0.0.0.0/"+str(i)).netmask().__str__() for i in range(0,33) ]
	
def genere_wildcard_list():
	return [ netmask_to_wildcard(Network("0.0.0.0/"+str(i)).netmask()) for i in range(0,33) ]
	
def get_last_dump():
	return max(glob.glob(PATH_IP_DUMP+'/*'),key=os.path.getctime)

def print_verbose(line,option_v=False,level=1):

	if option_v:
		if option_v >= level:
			print(line)
	#print("OPTION_V",str(option_v))
	
def netmask_to_wildcard(netmask):
	# print(str(IP(int(IP('255.255.255.255'))-int(netmask))))
	return str(IP(int(IP('255.255.255.255'))-int(netmask)))
	
def wildcard_to_netmask(wildcard):
	# print(str(IP(int(IP('255.255.255.255'))-int(netmask))))
	return str(IP(int(IP('255.255.255.255'))-int(wildcard)))
	
def translate_ip_cname(lines,option_v=False,option_c=False,option_d=False):

	mask_possible=genere_mask_list()
	wildcard_possible=genere_wildcard_list()
	number=0
	number_line_list_printed=[]
	pattern_network_mask_or_wildcard='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])(\s+|[a-z]+|[A-Z]+)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])'
	pattern_network_net='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])/([0-9]|[12][0-9]|[3][0-2])(\s+|$)'
	pattern_ip='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])'
	regex_network_mask_or_wildcard= re.compile(pattern_network_mask_or_wildcard)
	regex_network_net=re.compile(pattern_network_net)
	regex_ip=re.compile(pattern_ip)
	lastDump=get_last_dump()
	print_verbose('FICHIER DUMP:'+lastDump,option_v)
	DC_IP=ifEntries(dump=lastDump)
	
	for line in lines.splitlines() : 
		#print_verbose(mask_possible)
		print_verbose("\nLINE:"+line,option_v,level=2)
		ip_list =  regex_ip.finditer(line)
		number=number+1
		
		ips_filtered=[]
		
		modifiedLine=line
		if ip_list:
			for ip in ip_list:
				print_verbose("IP LIST"+ip.__str__(),option_v)
			

				print_verbose("\n=====================",option_v)
				print_verbose("Valid IP address present",option_v)
				print_verbose("=====================",option_v)
				print_verbose(ip.__str__(),option_v)
				
				try:
					Network(ip.group(0)+"/32").__str__()
				except:
					raise grepIpError(code=2,value1=ip.group(0)+"/32")
				
				ip_cur_line=ip.group(0)
				if ip_cur_line not in mask_possible and ip_cur_line not in wildcard_possible:
					print_verbose("ip_cur_line is not mask or a wildcard:"+ip_cur_line,option_v)
					cname__=DC_IP.searchIP(ip_cur_line)
					if option_d:
						reverse_dns=getReverseDns(ip_cur_line)
						if cname__ and reverse_dns:
							cname__+="|"+"|".join(reverse_dns)
						elif not cname__ and reverse_dns:
							cname__="|".join(reverse_dns)
					if cname__:
						print_verbose("IP present in dump:"+cname__,option_v)
						print_verbose("CNAME:"+cname__,option_v)
						if option_d:
							print_verbose("REVERSE_DNS:"+str(reverse_dns),option_v)
						if option_c:
							modifiedLine=modifiedLine.replace(ip_cur_line,orange(str({ip_cur_line:cname__})))
						else:
							modifiedLine=modifiedLine.replace(ip_cur_line,orange(cname__))
					else:
						print_verbose("IP not present in dump:"+ip_cur_line,option_v)
				
			
			print(modifiedLine)
		
		else:
			print_verbose("\nno valid IP present",option_v)
			print(line)
						
			

	print_verbose(u'Ligne affichée (numéro):\n'+str(number_line_list_printed),option_v)
		


if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--Verbose",help="Mode Debug Verbose",action="count",required=False)
	parser.add_argument("-c", "--complement",help="Affiche l'IP",action="store_true",required=False)
	parser.add_argument("-d", "--dnsreverse",help="Affiche le reverse DNS",action="store_true",required=False)
	
	all_lines=""
	
	if os.isatty(0):
		parser.add_argument('file')
		mode="FILE"

	else:
		mode="STDIN"
		
	args = parser.parse_args()
	
	if mode=="FILE":
		print_verbose('File:'+args.file,args.Verbose)
		param_file=args.file
		with open(param_file,'r') as file:
				all_lines=file.read()

	elif mode=="STDIN":
		param_file=None

		
	
	print_verbose("Argument Verbose:"+args.Verbose.__str__(),args.Verbose)
	all_lines=sys.stdin.read()
	translate_ip_cname(all_lines,args.Verbose,args.complement,args.dnsreverse)
	
