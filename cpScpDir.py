#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals



from paramiko import SSHClient
from scp import SCPClient
import argparse

BASTION="192.64.10.129"
USERNAME="x112097"

def copyScpDir(username,bastion,repertoire):
	ssh_client=SSHClient()
	ssh_client.load_system_host_keys()
	ssh_client.connect(bastion, username=username)
	scp = SCPClient(ssh_client.get_transport())
	scp.put(repertoire,recursive=True)
	scp.close()
	
if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-b", "--bastion",action="store",default=BASTION,help="Serveur SSH",required=False)
	parser.add_argument("-u", "--username",action="store",default=USERNAME,help="useraname SSH",required=False)
	parser.add_argument("-r", "--repertoire",action="store",help="repertoire to upload",required=True)
	
	args = parser.parse_args()
	
	if args.repertoire:
		copyScpDir(args.username,args.bastion,args.repertoire)
