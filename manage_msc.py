#!/usr/bin/env python3.7
# coding: utf-8


import sys
import argparse
import ipaddress
import smtplib
import pwd
import os
import getpass
from pathlib import Path
from logging import Logger
from logging.handlers import WatchedFileHandler
from logging import StreamHandler
import logging
import csv
import re
import atexit
import copy
import csv
import pwd
import yaml
import pdb

def logout_fabric(f,log):
	log.debug('Closing Fabric')
	f.logout()
	log.debug('Closing Tunnel')
	f.f.current_controller.tunnel.stop()
	
sys.path.insert(0,'/home/x112097/py/dmo')
import dmoPy3.aci as aci
import dmoPy3.aci.socgenbase as socgenbase
import dmoPy3.aci.default_objects as defobj

def main():
    parser=argparse.ArgumentParser(usage='%(prog)s -c config_file --fabric fabricName [options]' )
    parser.add_argument('-f',"--fabric",dest="fabric",default=None,action="store",help=u"Fabric Name")

    parser.add_argument('-u','--user',dest='user',default=None,action='store',help='User to be used to connect to MSC. If not specified: use your login account.')
    parser.add_argument('-p','--password',dest='password',default=None,action='store',help='User passsword')
    parser.add_argument('--list-sites',dest='list_sites',default=False,action='store_true', help='List Sites in fabric. ')
    parser.add_argument('--list-tenants',dest='list_tenants',default=False,action='store_true', help='List Tenants in fabric. ')

    parser.add_argument('--add',dest='add',default=False,action='store_true',help="Add a schema: currently, only supported with '--vrf' and '--magic'")
    parser.add_argument('--vrf',dest='vrf',default=[],action='append',help="With '--add' and '--magic', '--deploy': schema name will be derived from vrf name. Can be used multiple times. Or multiple vrfs can be specified if separated by comma")

    parser.add_argument('--logfile',dest="logfile",default=None,action="store",help=u"Where to log. optional")
    parser.add_argument('--disable-stdout',dest="disable_stdout",default=False,action="store_true",help=u"Disable stdout output.")
    parser.add_argument('--debug',dest="debug",default=False,action="store_true",help=u"Enable debug in the libraries.")

    parser.add_argument('--schema',dest='schema',action='append',default=[],help='Schema on which action will be done')
    #parser.add_argument('--template',dest='template',action='append',default=[],help='Templates to be deployed')
    parser.add_argument('--all-templates',dest='all_templates',action='store_true',default=True,help='All templates. Enabled by default. Cannot be unset for now.')
    
    parser.add_argument('--list-schemas',dest="list_schemas",default=False,action="store_true",help=u"List available schemas.")
    parser.add_argument('--show-schema',dest="show_schema",default=False,action="store_true",help=u"List templates in the schema and the sites where each template is deployed and if everything is OK.")
    parser.add_argument('--all-schemas',dest="all_schemas",default=False,action="store_true",help=u"Usable with '--show-schema'")
    parser.add_argument('--only-pending',dest="only_pending",default=False,action="store_true",help=u"Show only schema with pending changes. Great with '--all-schemas'")

    parser.add_argument('--show-consistency-summary',dest="show_consistency_summary",default=False,action="store_true",help=u"Show the consistency heat map.")
    parser.add_argument('--show-policy-states',dest="show_policy_states",default=False,action="store_true",help=u"Show the policy states of the schema.")


    parser.add_argument('--json-output',dest="json_output",default=False,action="store_true",help=u"Json output. No interpretation. With '--show-schema': complete json.")
    parser.add_argument('--yaml-output',dest="yaml_output",default=False,action="store_true",help=u"Yaml output. No interpretation. With '--show-schema': complete yaml.")

    
    options=parser.parse_args()
    hash_of_password={}
    if options.user is None:

if __name__=='__main__':
    main()

	