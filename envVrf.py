#!/usr/bin/env python3.7
# coding: utf-8

import argparse
from connexion import *
import yaml
from ParsingShow  import ParseVlanRun
import ruamel.yaml as ruYaml
from ruamel.yaml.compat import ordereddict
from ipEnv import ifEntries
import cache as cc
import pdb
import sys
import re
import xlrd
import os
from pprint import pprint as ppr
from dictdiffer import diff
import aci.Fabric
from  ParseVlanListe import *
from getHosts import *
from getsec import *

L3='/home/x112097/yaml/l3.yml'
MAPPING='/home/x112097/yaml/vlan_mapping.yml'
TAG_PREFIX_L3="L3_"
TAG_PREFIX_L2="L2_"
TAG_PREFIX_MAPPING="MAPPING_"
TAG_PREFIX_EPG="EPG_"
EXT_L2={'ODIN': { 'TIG':{'TIG-SC2':"95,234,450,2100-2199",'TIG-DC2':'299,315-324,327-328,331-333,340-345'} , 'SC2':{'TIG-SC2':"95,234,450,2100-2199"} , 'DC2': {'TIG-DC2':'299,315-324,327-328,331-333,340-345'} } }
FABRIC={'ODIN':'BDDF','PFHR':'LAB'}
SITES={'ODIN':{'DC_MAR':['DC2','DUB','DC5'],'DC_SEC':['SC2'],'DC_ALL':['DC2','DUB','DC5','SC2']},'PFHR':{'DC_PODA':['LAB_PODA'],'DC_PODB':['LAB_PODB'],'DC_ALL':['LAB_PODA','LAB_PODB']}}
PATCH='/home/x112097/yaml/patch.yml'
JINJA_DIR="/home/x112097/TEMPLATE/J2/ACI/"
TMP='/home/x112097/TMP'
OTV='/home/x112097/yaml/aci_otv.yml'
ACI_SITE={'BDDF':['DC2','DUB','DC5','SC2']}
DEFAULT_DIR_CONFIG='/home/x112097/CONFIG/ACI/'

def print_diff(list_diff):
	resultat=[]
	for entry in list_diff:
		resultat.append(entry)
	return resultat


def getConfigInterface(equipments__):

	Interfaces={}
	
	for equipment__ in equipments__:
		con_get_Running_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log","TMP","show run",timeout=300,verbose=False)
		Interfaces_cur=con_get_Running_cur.launch_withParser(ifEntries.ParseCiscoInterface)
		Interfaces[equipment__.upper()]=[]
		for parsingInterface in Interfaces_cur:
			Interfaces[equipment__.upper()].append(parsingInterface[0].asDict())

	return Interfaces
	
def getInterfaceOTV(site,vlan="",env=""):
	PATCH_OTV={}
	fabric_cur=FABRIC[env]
	with open(PATCH) as file_patch:
		PATCH_OTV=yaml.load(file_patch,Loader=yaml.SafeLoader)
		
	with open(OTV) as otv_yml:
		infoOTV=yaml.load(otv_yml,Loader=yaml.SafeLoader)
		
	site_otv=[]
	if vlan:
		try:
			if vlan in PATCH_OTV[env]['OTV']:
				site_otv=PATCH_OTV[env]['OTV'][vlan]
				
			elif site=='TIG' and env=="ODIN":
				site_otv=['DUB','DC5']
			
			else:	
				site_otv=[site]
				
		except KeyError as E:
			print(E)
			print("Verify environment in patch YAML:",PATCH)
			
		
	return { site__:infoOTV[fabric_cur][site__] for site__ in site_otv }

def suppressQuote(liste__):
		return str(liste__).replace("\'","")
	
def addVlanToExistingMapping(ExistingMapping,InterfaceOTV,env="ODIN",vlan="",vrf="",site="",ToBeConfigured={}):
	ap_cur=getAP(site,vrf,vlan=vlan,env=env)
	ifsOTV_cur=getInterfaceOTV(site,vlan=vlan,env=env)
	
	

	
	for site_otv in ifsOTV_cur.keys():
		mappingExistant=False
		int_otv=ifsOTV_cur[site_otv]['interface']
		node_otv='-'.join(ifsOTV_cur[site_otv]['node'])
		
		indice=0
		for binding in ExistingMapping[site_otv]:
			if binding['ap']==ap_cur and binding['ipg']==int_otv and  binding['node']==node_otv:
				if vlan not in binding['vlan_id']:
					ExistingMapping[site_otv][indice]['vlan_id'].append(vlan)
					if site_otv in ToBeConfigured:
						if ap_cur not in ToBeConfigured[site_otv]:
							ToBeConfigured[site_otv].append(ap_cur)
					else:
						ToBeConfigured[site_otv]=[ap_cur]
				else:
					print("Warning, vlan "+vlan+" already deployed on VPC ",site_otv)
				mappingExistant=True
				break;
			indice+=1
			
		if not mappingExistant:
			print("VRF "+vrf+" not present on VPC(",site_otv,')')
			if site_otv in ExistingMapping:
				ExistingMapping[site_otv].append({'ap': ap_cur, 'ipg': int_otv, 'node': node_otv, 'tenant': 'TN001', 'vlan_id': [vlan]})
			else:
				ExistingMapping[site_otv]=[{'ap': ap_cur, 'ipg': int_otv, 'node': node_otv, 'tenant': 'TN001', 'vlan_id': [vlan]}]
			if site_otv in ToBeConfigured:
				if ap_cur not in ToBeConfigured[site_otv]:
					ToBeConfigured[site_otv].append(ap_cur)
			else:
				ToBeConfigured[site_otv]=[ap_cur]
		
			
def parseMapping(String__):
	
	Mapping={}
	for line in String__.splitlines():
		if re.search('mapping',line):
			try:
				word=line.split()
				Mapping[word[3]]=word[4]
			except IndexError as e:
				pdb.set_trace()
				print(e)
				
	return Mapping
	
def getMappingInterface(equipment__, interface__):
	con_get_Running_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log","TMP","show run interface "+interface__,timeout=300,verbose=False)
	resultat= con_get_Running_cur.launch_withParser(parseMapping)
	return resultat

	
	

def getVlan(equipments__):

	Vlans={}
	
	for equipment__ in equipments__:
		con_get_Running_cur=connexion(equipement(equipment__),None,None,None,'SSH',"TMP/"+equipment__.lower()+"_shrun.log","TMP","show run",timeout=300,verbose=False)
		Vlans_cur=con_get_Running_cur.launch_withParser(ParseVlanRun)
		Vlans[equipment__.upper()]=Vlans_cur

	return Vlans
	
def initMapping(env):
	
	Mapping={}
	with open(MAPPING) as mapping_yml:
		infoMapping=yaml.load(mapping_yml,Loader=yaml.SafeLoader)
		
	try:
		infoMapSite=infoMapping[env]
	except KeyError as e:
		print(e)
		print("Environment Unknown, please set information in yaml file:", mapping_yml,file=sys.stderr)
		sys.exit(1)
	except TypeError as e:
		pdb.set_trace()
		print(e)


		
	for site in infoMapSite:
		try:
			Mapping[site]=getMappingInterface(list(infoMapSite[site].keys())[0],list(infoMapSite[site].values())[0])
		except IndexError:
			Mapping[site]={}
			
	return Mapping
	
def groupByVlanBinding(VlanBinding):
	
	resultat={}
	vlan_indexed={}
	for site in VlanBinding.keys():
		resultat[site]=[]
		vlan_indexed={}
		interface_cur=VlanBinding[site]['interface']
		node_cur=VlanBinding[site]['node']
		epgs_cur=VlanBinding[site]['epgs']
		for binding in epgs_cur:
			index=binding['tenant'][0]+':'+binding['ap'][0]
			if index in vlan_indexed.keys():
				vlan_indexed[index].append(binding['vlanid'][0])
			else:
				vlan_indexed[index]=[binding['vlanid'][0]]
		for tenant_ap in vlan_indexed.keys():
			tenant_ap_tab=tenant_ap.split(':')
			tenant=tenant_ap_tab[0]
			ap=tenant_ap_tab[1]
			vlan_indexed[tenant_ap].sort(key=int)
			resultat[site].append({'node':node_cur,'tenant':tenant,'ap':ap,'ipg':interface_cur,'vlan_id':vlan_indexed[tenant_ap]})
		

	return resultat
	
def testAPonSite(env,ap,site):
	test=False
		
	if env=="ODIN":
		if 'ALL' in ap:
			test=True
		elif site in ap:
			test=True
		elif site in ['DC2','TIG','DUB','DC5'] and '_MAR_' in ap:
			test=True
		elif site=='SC2' and ( 'SEC' in ap or 'ALL' in ap ) :
			test=True
	else:
		print("Env unknown")
		
	return test
	
def groupByVlanEPG(env,epgs):
	resultat={}
	
	for site in epgs:
		resultat[site]=[]
		for epg in epgs[site]:
			if  testAPonSite(env,epg[1],site):
				resultat[site].append(epg[-1])
		
	return resultat
		
def initOTVMapping(env):

	StaticEPG={}

	with open(OTV) as otv_yml:
		infoOTV=yaml.load(otv_yml,Loader=yaml.SafeLoader)

	fabric_cur=FABRIC[env]
	sites=ACI_SITE[fabric_cur]
	for site in sites:
		tag_cur=fabric_cur+'_'+site.upper()+'_STATIC_EPG'
		cache_cur=cc.Cache(tag_cur)
		StaticEPG[site]=cache_cur.getValue()
		
	Resultat_int={ site:{'interface':infoOTV[fabric_cur][site]['interface'],'node':'-'.join(infoOTV[fabric_cur][site]['node']),'epgs':StaticEPG[site][infoOTV[fabric_cur][site]['node'][0]][infoOTV[fabric_cur][site]['interface']]} for site in sites}
	
	resultat=groupByVlanBinding(Resultat_int)
		
	return resultat
		
	
def initExistingEPG(env,EPGS):
		
	resultat=groupByVlanEPG(env,EPGS)
	
	
	return resultat
	
def extractVrf(Interfaces,env='ODIN'):
	
	Vrfs={}
	
	PATCH_VRF={}
	
	with open(PATCH) as file_patch:
		PATCH_VRF=yaml.load(file_patch,Loader=yaml.SafeLoader)

	for site in Interfaces.keys():
		vlan_traite=[]
		Vrfs[site]={}
		for equipement in Interfaces[site]:
			for interface__ in Interfaces[site][equipement]:
				try:
					if re.search('Vlan',interface__['interface'][0]):
						if 'vrf' in interface__.keys():
							vlan_cur=interface__['interface'][0].replace('Vlan','')
							vrf_cur=interface__['vrf'][0]
							if vrf_cur != 'GRT':
								Vrfs[site][vlan_cur]=vrf_cur
								if vrf_cur in PATCH_VRF[env]['VRF']:
									Vrfs[site][vlan_cur]=PATCH_VRF[env]['VRF'][vrf_cur]
				except TypeError as typeerror:
					print(typeerror)
		
	return Vrfs
	
def extractDescription(Vlans):
	
	Descriptions={}
	
	for site in Vlans.keys():
		vlan_traite=[]
		Descriptions[site]={}
		for equipement in Vlans[site]:
			for vlan__ in Vlans[site][equipement]:
				try:
					if Vlans[site][equipement][vlan__]['name']:
						Descriptions[site][vlan__]=Vlans[site][equipement][vlan__]['name']
					else:
						#print(Vlans[site][equipement][vlan__]['name'])
						pass
				except TypeError as typeerror:
					print(typeerror)
				except KeyError as keyerror:
					pdb.set_trace()
					print(keyerror)
		
	return Descriptions
	
def initXls(xlsx__):
	VlanSite={}
	xl_workbook = xlrd.open_workbook(xlsx__)
	sheet_names = xl_workbook.sheet_names()
	
	OtherInfo={}
	
	for sheet__ in sheet_names:
		xl_sheet = xl_workbook.sheet_by_name(sheet__)
		VlanSite[sheet__]=[]
		for rownum in range(0,xl_sheet.nrows):
			VlanSite[sheet__].append(str(int(xl_sheet.row_values(rownum)[0])))
			try:
				name=xl_sheet.row_values(rownum)[1]
				if name:
					if 'DESC' not in OtherInfo:
						OtherInfo['DESC']={}
					if sheet__ not in OtherInfo['DESC']:
						OtherInfo['DESC'][sheet__]={}
						OtherInfo['DESC'][sheet__][str(int(xl_sheet.row_values(rownum)[0]))]=name
					else:
						OtherInfo['DESC'][sheet__][str(int(xl_sheet.row_values(rownum)[0]))]=name
				
			except IndexError:
				pass
			
			
	return (VlanSite,OtherInfo)
	
def getTemplate(site,vlan="",env='ODIN'):
	PATCH_TEMPLATE={}
	
	with open(PATCH) as file_patch:
		PATCH_TEMPLATE=yaml.load(file_patch,Loader=yaml.SafeLoader)
		
		
	if vlan:
		try:
			if vlan in PATCH_TEMPLATE[env]['TEMPLATE']:
				return PATCH_TEMPLATE[env]['TEMPLATE'][vlan]
		except KeyError as E:
			print(E)
			print("Verify environment in patch YAML:",PATCH)
	
	
	
	if env=='ODIN':
		if site=='DC2' or site=='TIG':
			return 'DC_MAR'
		elif site=='SC2':
			return 'DC_SEC'
			
	elif env=='PFHR':
		if site=='PODA':
			return 'DC_PODA'
		elif site=='PODB':
			return 'DC_PODB'
		
def getTranslatedVlan(site,vlan__,mapping):
	resultat=vlan__
	try:
		resultat=mapping[site][vlan__]
	except:
		pass
	
	return resultat
		
def getAP(site,vrf,vlan="",env='ODIN'):

	PATCH_AP={}
	
	with open(PATCH) as file_patch:
		PATCH_AP=yaml.load(file_patch,Loader=yaml.SafeLoader)
		
		
	if vlan:
		try:
			if vlan in PATCH_AP[env]['AP']:
				return vrf+'_'+PATCH_AP[env]['AP'][vlan]+'_'+'AP'
				
		except KeyError as E:
			print(E)
			print("Verify environment in patch YAML:",PATCH)
			
	if env=='ODIN':
		if site=='DC2' or site=='TIG':
			return vrf+'_MAR_AP'
		elif site=='SC2':
			return vrf+'_SEC_AP'
	elif env=='PFHR':
		if site=='PODA':
			return vrf+'_PODA_AP'
		elif site=='PODB':
			return vrf+'_PODB_AP'
		
def getVrf(site,vlan__,vrfs__):
	resultat=None
	try:
		resultat=vrfs__[site][str(vlan__)]
	except KeyError:
		resultat='NOTROUTED'
		#print(site,vlan__,'NOTROUTED')
		
	if not resultat:
		pdb.set_trace()
		print('Error')
		
	return resultat
	
def getDescription(site,vlan__,desc__,exception):
	resultat=None
	try:
		resultat=desc__[site][vlan__]
	except KeyError:
		resultat='TOBEDEFINED'
	
	try:
		resultat=exception['DESC'][site][vlan__]
	except KeyError:
		pass
	if not resultat:
		pdb.set_trace()
		print('Error')	
		
	return resultat
	
def initYamlConfig(VlanSite,vrf__,desc__,mapping__,otherInfo):
	templates_epgs_bds={}
	templates_epgs_contracts={}
	sites_epgs_domains={}
	
	configYaml={}
	
	vrf_liste=[]
	
	for site in VlanSite.keys():
		for vlan__ in VlanSite[site]:
			try:
				vrf_cur=getVrf(site,vlan__,vrf__)
				if vrf_cur not in templates_epgs_bds.keys():
					templates_epgs_bds[vrf_cur]=[]
				if vrf_cur not in templates_epgs_contracts.keys():
					templates_epgs_contracts[vrf_cur]=[]
				if vrf_cur not in sites_epgs_domains.keys():
					sites_epgs_domains[vrf_cur]=[]	
					
				if vrf_cur not in vrf_liste:
					vrf_liste.append(vrf_cur)
					
				templates_epgs_bds[vrf_cur].append({ 'vlan_id': int(getTranslatedVlan(site,vlan__,mapping__)), 'template': getTemplate(site,vlan=vlan__), 'ap': getAP(site,vrf_cur,vlan=vlan__), 'L2STRETCH': "yes", 'preferred_group': "yes", 'BD_unknown_unicast': "flood", 'display_name': getDescription(site,vlan__,desc__,otherInfo) })
				templates_epgs_contracts[vrf_cur].append({ 'vlan_id': int(getTranslatedVlan(site,vlan__,mapping__)) , 'template': getTemplate(site,vlan=vlan__) , 'ap': getAP(site,vrf_cur,vlan=vlan__), 'contracts': [ { 'schema': "", 'template': getTemplate(site,vlan=vlan__), 'name': 'PermitAny_'+vrf_cur+'_VRF', 'type': 'consumer' }, { 'schema': "BDDF_GLOBAL_CONTRACTS", 'template': 'Template1', 'name': 'PermitAny_TSM', 'type': 'consumer' } ]})
				sites_epgs_domains[vrf_cur].append({ 'vlan_id': int(getTranslatedVlan(site,vlan__,mapping__)), 'site': site, 'site_template': getTemplate(site,vlan=vlan__), 'ap': getAP(site,vrf_cur,vlan=vlan__) , 'domains': [ { 'profile': 'PDOM_COMMON', 'type': 'physicalDomain' } ]})
			except KeyError as e:
				pdb.set_trace()
				print(e)
				
	for vrf___ in vrf_liste:
		configYaml[vrf___]={'templates_epgs_bds':templates_epgs_bds[vrf___],'templates_epgs_contracts':templates_epgs_contracts[vrf___],'sites_epgs_domains':sites_epgs_domains[vrf___]}
			
	return configYaml
	
def getYamlFile(env__,vrf__,directory):
	return directory+'/'+FABRIC[env__]+'_'+vrf__+'.yml'
	
def addConfigYaml(yaml_file,config,save=""):
	cur_yaml = ruYaml.YAML()
	cur_yaml.indent(mapping=2,sequence=3, offset=3)
	cur_yaml.indent( offset=3)
	cur_yaml.preserves_quotes=True
	cur_yaml.width = 4096
	cur_yaml.default_flow_style = True

	try:
		with open( yaml_file) as str_yaml:
			data = cur_yaml.load(str_yaml)
			for tag in config.keys():
				try:
					#data[tag]+=config[tag]
					for line in config[tag]:
						data[tag].append(line)
						#if tag=='templates_epgs_contracts':
						#	pdb.set_trace()
				except KeyError as e:
					print(e)
					print("tag not present:",tag)
					print("Verify Yaml file",yaml_file)
			cur_yaml.dump(data, sys.stdout)
			
			if save:
				dir__=save
				file__=os.path.basename(schema_yaml[vrf__])
				
				if not os.path.exists(dir__):
					os.makedirs(dir__)
					
				with open(dir__+'/'+file__,'w') as file__w:
					cur_yaml.dump(data, file__w )
	except 	FileNotFoundError as e:
		print(e)
		print("Schema vrf is Needed",yaml_file)
		pdb.set_trace()
		data=None
		
	return data
		
def initParamVlan(vlan,site,Vlan2Vrf,Vlan2Desc,Mapping,env="ODIN",info={}):
	'''  - { vlan_id: {{vlan.id}}, template: {{vlan.template}}, ap: "{{vlan.ap}}", L2STRETCH: "yes", preferred_group: "yes", BD_unknown_unicast: "flood", display_name: "{{vlan.description}}" }'''
	vlan__={}
	
	vrf_cur=getVrf(site,vlan,Vlan2Vrf)
	vlan__['id']=int(getTranslatedVlan(site,vlan,Mapping))
	vlan__['template']=getTemplate(site,vlan=vlan,env=env)
	vlan__['ap']=getAP(site,vrf_cur,vlan=vlan,env=env)
	vlan__['description']=getDescription(site,vlan,Vlan2Desc,info)
	vlan__['vrf']=vrf_cur
	vlan__['site']=site
	try:
		vlan__['site_template']=SITES[env][getTemplate(site,vlan=vlan,env=env)]
	except KeyError as e:
		pdb.set_trace()
		print(e)
	
	return vlan__
	
def initVrfs(Vlan2Vrf,VlanSite):
	vrfs__={}
	for site__ in VlanSite.keys():
		for vlan__ in  Vlan2Vrf[site__]:
			vrf_cur=Vlan2Vrf[site__][vlan__]
			if vrf_cur in vrfs__.keys():
				vrfs__[vrf_cur].append((site__,vlan__))
			else:
				vrfs__[vrf_cur]=[(site__,vlan__)]
				
	return vrfs__
	
def addConfigToYaml(config__,file__,cible,env='ODIN',mode='copy'):
	
	info_tag={}
	for tag in config__.keys():
		info_tag[tag]=False
	
	if mode=='copy':
		if not os.path.exists(cible):
			os.makedirs(cible)
	
	if mode=='copy':
		try:	
			with open(file__,'r') as file_config:
				lines=file_config.read().splitlines(True)
	
		except FileNotFoundError:
			print('schema file not present:',file__)
			
			vrf__=os.path.basename(file__).replace(FABRIC[env]+'_','').replace('.yml','').replace('.yaml','')
			addSchema(vrf__,TMP+'/CONFIG/'+os.path.basename(file__),env)
			with open(TMP+'/'+os.path.basename(file__),'r') as file_config:
				lines=file_config.read().splitlines(True)
			
		ExceptWrite=False
		with open(cible+'/'+os.path.basename(file__),'w') as file_cible:
			for line in lines:
				for tag in config__.keys():
					if re.search(tag,line):
						info_tag[tag]=True
						file_cible.write(line.replace('#'+tag,tag))
						ExceptWrite=True
				for tag in config__.keys():
					if info_tag[tag] and re.search('^$',line):
						file_cible.write(config__[tag])
						info_tag[tag]=False
				if not ExceptWrite:
					file_cible.write(line)
				else:
					ExceptWrite=False
	elif mode=='modify':
		print("The initial yaml File will be directly modified:",file__)
		try:
			pdb.set_trace()
			ExceptWrite=False
			with open(file__,'a+') as file_config:
				while True:
					try:
						line=file_config.readline()
					except EOFError:
						print('END OF FILE')
						break
					for tag in config__.keys():
						if re.search(tag,line):
							info_tag[tag]=True
							file_config.write(line.replace('#'+tag,tag))
							ExceptWrite=True
					for tag in config__.keys():
						if info_tag[tag] and re.search('^$',line):
							file_config.write(config__[tag])
							info_tag[tag]=False
					if not ExceptWrite:
						pass
					else:
						ExceptWrite=False

	
		except FileNotFoundError:
			print('schema file not present:',file__)
			
			vrf__=os.path.basename(file__).replace(FABRIC[env]+'_','').replace('.yml','').replace('.yaml','')
			addSchema(vrf__,file__,env)
			with open(TMP+'/'+os.path.basename(file__),'r') as file_config:
				lines=file_config.read().splitlines()
			

			ExceptWrite=False
			with open(file__,'a+') as file_config:
				while True:
					try:
						line=file_config.readline()
						if not line:
							break
					except EOFError:
						print('END OF FILE')
						break
					for tag in config__.keys():
						if re.search(tag,line):
							info_tag[tag]=True
							file_config.write(line.replace('#'+tag,tag))
							ExceptWrite=True
					for tag in config__.keys():
						if info_tag[tag] and re.search('^$',line):
							file_config.write(config__[tag])
							info_tag[tag]=False
					if not ExceptWrite:
						pass
					else:
						ExceptWrite=False
	
	else:
		print('Mode no supported:',mode,file=sys.stderr)
		sys.exit(1)

def addSchema(vrf__,filename__,env__):
	loader = jinja2.FileSystemLoader(JINJA_DIR+"MSO")
	env_j2 = jinja2.Environment( loader=loader)
	template=env_j2.get_template(os.path.basename('schema_'+env__+'.j2'))
	resultat=template.render({"vrf":vrf__}).rstrip()
	
	with open(filename__,'w') as file_w:
		file_w.write(resultat)
	

def getExistingVlan(schemas):
	vlans__=[]
	for schema_file in schemas:
		try:
			with open(schema_file,'r') as sch_file:
				info_yaml=yaml.load(sch_file,Loader=yaml.SafeLoader)
				try:
					for info_epgs in info_yaml['templates_epgs_bds']:
						id_cur=info_epgs['vlan_id']
						template_cur=info_epgs['template']
						vlans__.append(template_cur+':'+str(id_cur))
				except KeyError as e:
					pass
		except FileNotFoundError as e:
			pass
			
		
	return vlans__
	
def printVlan(vlans__,vrf__,desc__):
	print('VLANS TO CONFIGURE:')
	for site__ in vlans__.keys():
		for vlan__ in vlans__[site__]:
			try:
				print('site:'+site__,'id:'+vlan__,'vrf:'+getVrf(site__,vlan__,vrf__),'descr:'+desc__[site__][vlan__])
			except TypeError as e:
				pdb.set_trace()
				print(e)
			except KeyError as e:
				print('site:'+site__,'id:'+vlan__,'vrf:'+getVrf(site__,vlan__,vrf__),'descr:TBD')
				
		
def FilterOTVMapping(NewConfig,AP_to_configured):	
	FilteredConfig={}
	
	for site in AP_to_configured:
		FilteredConfig[site]=[]
		for binding in NewConfig[site]:
			try:
				if binding['ap'] in AP_to_configured[site]:
					FilteredConfig[site].append(binding)
			except KeyError as E:
				pdb.set_trace()
				print(E)


	
	return FilteredConfig
	
def saveConfigOTV(config,directory):

	if not os.path.exists(directory):
		os.makedirs(directory)

	loader = jinja2.FileSystemLoader(JINJA_DIR+"APIC")
	env_j2 = jinja2.Environment( loader=loader)
	env_j2.filters['suppressQuote']=suppressQuote
	
	
	try:
		template=env_j2.get_template('static_otv.j2')
	except jinja2.exceptions.TemplateNotFound:
		pdb.set_trace()
		print("Error loadind template")
		
	for site in config:
		filename=directory+'/ACI_RET_'+site+'_FABRIC.TXT'
		config_cur=template.render({"bindings":config[site]}).rstrip()
		
		with open(filename,'w') as file_w:
			file_w.write(config_cur)

def saveConfigSchema(env,config,directory):

	
	if not os.path.exists(directory):
		os.makedirs(directory)
		
	for vrf in config:
		filename=directory+'/'+FABRIC[env]+'_'+vrf+'.TXT'
		with open(filename,'w') as file_w:
			for tag in config[vrf]:
				file_w.write(tag+':\n')
				file_w.write(config[vrf][tag]+'\n\n')
	
if __name__ == '__main__':
	"Fonction principale"	
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-e", "--env",action="store",help="Environment",required=True)
	parser.add_argument("-s", "--site",action="store",help="Site",required=False)
	parser.add_argument("-y", "--yaml",action="store",default=L3,help="Yaml File with L3 equipment Informations",required=False)
	parser.add_argument("-r", "--resultat",action="store",help="Directory the contains new yaml",required=False)
	parser.add_argument("--renew-l3",dest="renew_l3",action="store_true",help="get current config l3 and not try to get Info from a cache",required=False)
	parser.add_argument("--renew-l2",dest="renew_l2",action="store_true",help="get current config l2 and not try to get Info from a cache",required=False)
	parser.add_argument("--renew-epg",dest="renew_epg",action="store_true",help="get current epg and not try to get Info from a cache",required=False)
	parser.add_argument("--renew-mapping",dest="renew_mapping",action="store_true",help="get current mapping and not try to get Info from a cache",required=False)
	parser.add_argument("--renew",action="store_true",help="get current config l2 l3 mapping and not try to get Info from a cache",required=False)
	parser.add_argument("--xlsx",action="store",help="Fichier Excel Contenant les Vlans",required=False)
	parser.add_argument("--config-yaml",dest='config_yaml',action="store",help="Directory that contains Schema yaml file",required=False)
	parser.add_argument("--get-vrf",dest='get_vrf',action="store",help="Print vrf",required=False)
	parser.add_argument("--jinja",action="store_true",help="Mode Jinja instead dump yaml",required=False)
	parser.add_argument("--modify",action="store_true",help="directly modify the existing directory",required=False)
	parser.add_argument("--otv",action="store_true",help="print otv configuration",required=False)
	parser.add_argument("--tag",action="store",default="CUR",help="TAG config",required=False)
	
	args = parser.parse_args()
	
	if args.config_yaml and not args.xlsx:
		raise argparse.ArgumentError(None,'--xlsx is manadatory with --config-yaml ')
		
	if args.resultat and not args.config_yaml and not args.xlsx:
		raise argparse.ArgumentError(None,'--xlsx  and --config-yaml is manadatory with --resultat ')
		
		
	if args.jinja and not args.config_yaml:
		raise argparse.ArgumentError(None,'--args.config_yaml is manadatory with --args.jinja ')
		
	if args.resultat and not args.config_yaml and not args.xlsx:
		raise argparse.ArgumentError(None,'--xlsx  and --config-yaml is manadatory with --resultat ')

	if args.modify and args.resultat :
		raise argparse.ArgumentError(None,'--modify and --resultat or -r are mutually exclusive ')
		
		
	if args.modify and not args.config_yaml and not args.xlsx:
		raise argparse.ArgumentError(None,'--xlsx  and --config-yaml is manadatory with --modify ')
		
	with open(args.yaml, 'r' ) as info_yml:
		Info=yaml.load(info_yml,Loader=yaml.SafeLoader)
		
	try:
		
		env=Info[args.env]
	except KeyError as e:
		print("Environment Unknown, please set information in yaml file:",args.yaml,file=sys.stderr)
		sys.exit(1)
		
	Interfaces={}
	Vlans={}
	
	infoL3Cache=cc.Cache(TAG_PREFIX_L3+args.env)
	infoL2Cache=cc.Cache(TAG_PREFIX_L2+args.env)
	infoMapCache=cc.Cache(TAG_PREFIX_MAPPING+args.env)
	infoEpgCache=cc.Cache(TAG_PREFIX_EPG+args.env)
	if infoL3Cache.isOK() and not args.renew_l3 and not args.renew:
		Interfaces=infoL3Cache.getValue()
	else:
		print('Cache l3 renew...')
		for site in env.keys():
			liste_host=[]
			for host__ in env[site]:
				liste_host.append(host__)
			Interfaces[site]=getConfigInterface(liste_host)
		infoL3Cache.save(Interfaces)
			
	if infoL2Cache.isOK() and not args.renew_l2 and not args.renew:
		Vlans=infoL2Cache.getValue()
	else:
		print('Cache l2 renew...')
		for site in env.keys():
			liste_host=[]
			for host__ in env[site]:
				liste_host.append(host__)
			Vlans[site]=getVlan(liste_host)
		infoL2Cache.save(Vlans)
	
	if infoEpgCache.isOK() and not args.renew_epg and not args.renew:
		Epgs=infoEpgCache.getValue()
	else:
		print('Cache Epgs renew...')
		fabric=aci.Fabric.Fabric(FABRIC[args.env])
		Epgs=fabric.getEpgs()
		infoEpgCache.save(Epgs)
		
	if infoMapCache.isOK() and not args.renew_mapping and not args.renew:
		Mapping=infoMapCache.getValue()
	else:
		print('Cache mapping renew...')
		Mapping=initMapping(args.env)
		infoMapCache.save(Mapping)
		
		
	Vlan2Vrf=extractVrf(Interfaces)
	Vlan2Desc=extractDescription(Vlans)
	
	if args.jinja:
		if args.xlsx:
			ConfigSchema={}
			(VlanSite,OtherInfo)=initXls(args.xlsx)
			tags=['templates_epgs_bds','templates_epgs_contracts','sites_epgs_domains']
			templates={}

			loader = jinja2.FileSystemLoader(JINJA_DIR+'MSO')
			env_j2 = jinja2.Environment( loader=loader)
			
			
			for tag__ in tags:
				try:
					templates[tag__]=env_j2.get_template(os.path.basename(tag__+'.j2'))
				except jinja2.exceptions.TemplateNotFound:
					pdb.set_trace()
					print("Error loadind template")
				
			vrfs_site=initVrfs(Vlan2Vrf,VlanSite)
			
			schema_yaml={}		
			for vrf__ in vrfs_site.keys():
				schema_yaml[vrf__]= getYamlFile(args.env,vrf__,args.config_yaml)
			
			
			printVlan(VlanSite,Vlan2Vrf,Vlan2Desc)
			
			list_sch=[ s for s in schema_yaml.values() ] 
			#existingvlans=getExistingVlan(list_sch)
			
			existingvlans=initExistingEPG(args.env,Epgs)
			
			vrf_traite=[]
			paramVlans={}
			
			AllexistingVlan=[]
			
			testNoL2ext=True
			for site__ in VlanSite:
				for vlan__ in VlanSite[site__]:		
					for interco in EXT_L2[args.env][site__]:
						if vlan__ in liste_vlans(EXT_L2[args.env][site__][interco]):
							print('Verify vlan',vlan__,'it can be in l2 extension',interco)
							testNoL2ext=False
							
			if testNoL2ext:
				print("Check vlan in L2DCI:OK")
				
			for site__ in existingvlans:
				AllexistingVlan+=existingvlans[site__]
			for site__ in VlanSite:
				for vlan__ in VlanSite[site__]:

					try:
						vrf__=getVrf(site__,vlan__,Vlan2Vrf)
						if getTranslatedVlan(site__,vlan__,Mapping) not in AllexistingVlan:
							if vrf__ not in vrf_traite:
								vrf_traite.append(vrf__)
								paramVlans[vrf__]=[]
								if vrf__ not in schema_yaml.keys():
									schema_yaml[vrf__]= getYamlFile(args.env,vrf__,args.config_yaml)
							paramVlans[vrf__].append(initParamVlan(vlan__,site__,Vlan2Vrf,Vlan2Desc,Mapping,env=args.env,info=OtherInfo))
						else:
							print("Vlan already deployed:",site__,vlan__,vrf__,'NAT:'+getTranslatedVlan(site__,vlan__,Mapping))
					except TypeError as e:
						pdb.set_trace()
						print(e)
						print(stop)
						
					
					
			for vrf__ in vrf_traite:
				ConfigSchema[vrf__]={}
				for tag__ in tags:
					try:
						ConfigSchema[vrf__][tag__]=templates[tag__].render({"vlans":paramVlans[vrf__]}).replace('\n','',1).rstrip()
					except KeyError as e:
						pdb.set_trace()
						print(e)
						

			if args.resultat:
				for vrf__ in vrf_traite:
					try:
						addConfigToYaml(ConfigSchema[vrf__],schema_yaml[vrf__],args.resultat,env=args.env)
					except KeyError as e:
						pdb.set_trace()
						print(e)
						
			if args.modify:
				for vrf__ in vrf_traite:
					try:
						addConfigToYaml(ConfigSchema[vrf__],schema_yaml[vrf__],None,env=args.env,mode='modify')
					except KeyError as e:
						pdb.set_trace()
						print(e)	
			
			if args.otv:
				CurOTVMapping=initOTVMapping(args.env)
				print("OTV current static binding configuration:")
				ppr(CurOTVMapping,width=500)
				NewOTVMapping=CurOTVMapping.copy()
				
				siteAPtoConfigured={}
				for site__ in VlanSite:
					for vlan__ in VlanSite[site__]:

						try:
							vrf__=getVrf(site__,vlan__,Vlan2Vrf)
							interfaceOTV=getInterfaceOTV(site__,vlan=vlan__,env=args.env)
							addVlanToExistingMapping(NewOTVMapping,interfaceOTV,env=args.env,vlan=getTranslatedVlan(site__,vlan__,Mapping),vrf=vrf__,site=site__,ToBeConfigured=siteAPtoConfigured)
						except TypeError as e:
							pdb.set_trace()
							print(e)
							print(stop)
						
				print("OTV New static binding configuration:")
				ppr(NewOTVMapping,width=800)
				
				filteredConfig=FilterOTVMapping(NewOTVMapping,siteAPtoConfigured)
				
				print("OTV New static binding configuration (needed change):")
				ppr(filteredConfig,width=800)
				
				print("Saving OTV static binding configuration to ",DEFAULT_DIR_CONFIG+args.tag,"...")
				saveConfigOTV(filteredConfig,DEFAULT_DIR_CONFIG+args.tag)
	
				print("Saving Schema configuration to ",DEFAULT_DIR_CONFIG+args.tag,"...")
				saveConfigSchema(args.env,ConfigSchema,DEFAULT_DIR_CONFIG+args.tag)	
			
	else:
		if args.xlsx:
			(VlanSite,OtherInfo)=initXls(args.xlsx)
			if args.config_yaml:
				ConfigYaml=initYamlConfig(VlanSite,Vlan2Vrf,Vlan2Desc,Mapping,{})
				
				schema_yaml={}
				for vrf__ in ConfigYaml.keys():
					schema_yaml[vrf__]= getYamlFile(args.env,vrf__,args.config_yaml)
					
				if args.resultat:
					save=args.resultat
				else:
					save=""
					
				for vrf__ in schema_yaml.keys():
					data_cur=addConfigYaml(schema_yaml[vrf__],ConfigYaml[vrf__],save=save)
					
				
				pdb.set_trace()
	
	print("test")