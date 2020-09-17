#!/usr/bin/env python3.7
# coding: utf-8


from git import Repo
import yaml
from Tunnelier import Tunnelier
import argparse
import warnings
from functools import wraps
import os
import pdb
from getsec import *
import pyparsing as pp

YAML_INFO_TAG='/home/x112097/yaml/acisg_git_tag.yml'
GIT_REP='/home/x112097/GIT/ACI/'
TSK="/home/x112097/CONNEXION/pass.db"
DEFAUTL_USER="x112097"

def parseUrl(url__):

	Result=None
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	name=pp.Word(pp.alphanums+'.')
	http=pp.CaselessLiteral('http').setParseAction(lambda s,l,t : t[0].lower())
	https=pp.CaselessLiteral('https').setParseAction(lambda s,l,t : t[0].lower())
	ftp=pp.CaselessLiteral('ftp').setParseAction(lambda s,l,t : t[0].lower())
	ftps=pp.CaselessLiteral('ftps').setParseAction(lambda s,l,t : t[0].lower())
	path=pp.Combine(pp.Literal('/')+pp.Word(pp.alphanums+'_-/'))
	port=pp.Combine(pp.Suppress(pp.Literal(':'))+pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <65536 and int(tokens[0]) >= 0 ))
	url_http=http.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='80').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	url_https=https.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='443').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	url_ftp=https.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='21').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	url_ftps=https.setResultsName('protocol')+pp.Literal('://').suppress()+(ipAddress|name).setResultsName('ip')+pp.Optional(port,default='22').setResultsName('port')+pp.Optional(path,default=None).setResultsName('path')
	
	url=pp.MatchFirst([url_https,url_http,url_ftps,url_ftp])
	
	Result=url.parseString(url__).asDict()
	
	return Result
	
def mkdir(dir):
	if not os.path.exists(dir):
		os.makedirs(dir)
		
def add_login_pass_url(url,username=DEFAUTL_USER,pwd=""):
	tsk=secSbe(TSK)
	urlParsed=parseUrl(url)
	if not pwd:
		windows=tsk.win
				
	return urlParsed['protocol']+'://'+username+":"+windows+'@'+urlParsed['ip']+':'+urlParsed['port']+urlParsed['path']
	
def ignore_warnings(f):
    @wraps(f)
    def inner(*args, **kwargs):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore")
            response = f(*args, **kwargs)
        return response
    return inner

@ignore_warnings
def init_yaml(fichier_yaml):
	resultat={}
	
	with open(fichier_yaml, 'r') as contenu_yml:
		resultat = yaml.load(contenu_yml)
	
	return resultat
	
def test_tag(tag__,tags):
	assert tag__ in tags , "tags supported:"+" ".join(tags.keys())

	
def clone_git(url="",target="",**kwargs):
	tunnel=Tunnelier()
	new_url=tunnel.addUrl(url)
	final_url=add_login_pass_url(new_url)
	Repo.clone_from(final_url,target)
	tunnel.stop()
	
def fetch_git(url="",target="",**kwargs):
	repo=Repo(target)
	tunnel=Tunnelier()
	new_url=tunnel.addUrl(url)
	final_url=add_login_pass_url(new_url)
	#origin=repo.create_remote('origin',final_url)
	#origin.fetch()
	repo.remote().fetch()
	tunnel.stop()
	
def pull_git(url="",target="",**kwargs):
	repo=Repo(target)
	tunnel=Tunnelier()
	new_url=tunnel.addUrl(url)
	final_url=add_login_pass_url(new_url)
	#origin=repo.create_remote('origin',final_url)
	#origin.pull()
	repo.remote().pull()
	tunnel.stop()
	
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--tag",  action="store",help="Tag action",required=True)
	parser.add_argument("-s", "--site",  action="store",help="site or Fabric",required=False)
	parser.add_argument("--clone" ,action="store_true",help="Action git clone",required=False)
	parser.add_argument("--fetch" ,action="store_true",help="Action git fetch",required=False)
	parser.add_argument("--pull" ,action="store_true",help="Action git fetch",required=False)
	args = parser.parse_args()
	
	tags=init_yaml(YAML_INFO_TAG)
	
	test_tag(args.tag,tags['TAG'])
	
	dir_cur=GIT_REP+args.tag
	mkdir(dir_cur)
	
	if args.clone:
		clone_git(url=tags['TAG'][args.tag]['DIR'],target=dir_cur)
		
	if args.fetch:
		fetch_git(url=tags['TAG'][args.tag]['DIR'],target=dir_cur)
		
	if args.pull:
		pull_git(url=tags['TAG'][args.tag]['DIR'],target=dir_cur)
	
	#pdb.set_trace()
	
	print("Fin")


