#!/usr/bin/env python3.7
# coding: utf-8

import time
from sshtunnel import SSHTunnelForwarder
import requests
import argparse
import pdb
import socks


PAER="192.64.10.129"
LOCALHOST="127.0.0.1"
REMOTE_USER = 'x112097'
REMOTE_HOST =  PAER
REMOTE_PORT = 22
LOCAL_HOST =  LOCALHOST
LOCAL_PORT = 5000
SOCKS_PROXY_PORT=5000
KEY='home/x112097/.ssh/id_rsa'


class SshSocks5(SSHTunnelForwarder):
	def __init__(self, remote_host__, remote_port__, remote_user__, ssh_private_key__,local_bind_address__,local_bind_port__ ):
		s=socks.socksocket()
		s.set_proxy(socks.SOCKS5,LOCAL_HOST,SOCKS_PROXY_PORT)
		super().__init__(ssh_address_or_host=(remote_host__, remote_port__), ssh_username=remote_user__,  ssh_password ="B2rn1s12345!", remote_bind_address=(local_bind_address__,local_bind_port__),local_bind_address=("196.82.128.233",),)
		


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-b", "--bastion",  action="store",default=REMOTE_HOST,help="Socks5 Server",required=False)
	parser.add_argument("-p", "--port",     action="store",default=REMOTE_PORT,help="Socks5 Server port",required=False)
	parser.add_argument("-L", "--localport",action="store",default=LOCAL_PORT,help=u"Proxy Server Port IP for localhost",required=False)
	args = parser.parse_args()

	SOCK5__ = SshSocks5(args.bastion, args.port, REMOTE_USER,KEY,LOCAL_HOST,int(args.localport))
	SOCK5__.start()
	time.sleep(300)
	SOCK5__.stop()
	

