#!/usr/bin/env python3.7
# coding: utf-8

import re
import pdb

def replaceIP(string,newIP):
	pattern_ip='([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([01][0-9][0-9]\.|[2][5][0-5]\.|[2][0-4][0-9]\.|[01][0-9][0-9]\.|[0-9][0-9]\.|[0-9]\.)([1][0-9][0-9]|[2][5][0-5]|[2][0-4][0-9]|[01][0-9][0-9]|[0-9][0-9]|[0-9])'
	regex_ip=re.compile(pattern_ip)
	ip_list =  regex_ip.finditer(string)
	if ip_list:
		resultat=string
		for ip__ in ip_list:
			resultat=resultat.replace(ip__.group(0),newIP)
	else:
		resultat=string
	
	return resultat
	
#print(replaceIP('http://1.2.3.5/','127.0.0.1:3500'))