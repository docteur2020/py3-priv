#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import pdb
import yaml
import pprint
from connexion import *
from ipEnv import ifEntries
import cache as cc
import ParseVlanListe
from ParsingShow import ParseVlandb
import xlrd

L2_TRUNK_YML='/home/x112097/yaml/l2_trunk.yml'
PARSING_MODE_YML='/home/x112097/yaml/ParsingL2.yml'

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

def initValueInterface(s,l,t):	
	resultat={}
	
	slash=genere_mask_dict()
	ip_helper=[]
	
	for interface in t.keys():
		resultat[interface]={}
		ip_helper=[]
		for key__ in t[interface].keys():
			if key__=='no' and t[interface][key__]=='ip address':
				resultat[interface]['IP']=None
			elif  key__=='shutdown':
				resultat[interface]['status']='shutdown'
			elif  key__=='no' and t[interface][key__]=='shutdown':
				resultat[interface]['status']='active'
			elif  key__=='IP':
				res__=t[interface][key__].split()
				try:
					resultat[interface]['IP']=[res__[0]+"/"+slash[res__[1]]]
				except IndexError as e:
					resultat[interface]['IP']=res__
				except KeyError as e:
					pdb.set_trace()
					print(e)
					resultat[interface]['IP']='INDERTERMINE'
			elif key__=="dampening":
				other=t[interface]["dampening"].split()
				resultat[interface]['dampening']='enable'
				resultat[interface][other[0]]="".join(other[1:])
			elif  re.search('ip helper-address',key__):
				ip_helper.append(t[interface][key__])
			elif  re.search('no ip ',key__):
				resultat[interface]['ip '+t[interface][key__]]='disable'
			else:
				resultat[interface][key__]=t[interface][key__]
				

		if ip_helper:
			ip_helper.sort()
			resultat[interface]['ip helper-address']=ip_helper
			
		if 'status' not in resultat[interface].keys():
			resultat[interface]['status']='active'
				
		
	return resultat
	
def inser_inc(dict_id,tag):
	def parseAction(s,l,t):
		dict_id['0']=str(int(dict_id['0'])+1)
		return tag+dict_id['0']
		
	return parseAction
	
def init_inc(dict_id):
	def parseAction(s,l,t):

		dict_id={'0':'0'}
		return t
		
	return parseAction
	
class l2env(object):
	def __init__(self,env,tag,renew=False):
		self.tag="L2_VLAN_INFO_"+env+'_'+tag
		self.tag_db="L2_VLAN_DB_"+env+'_'+tag
		self.yaml_l2_file=L2_TRUNK_YML
		self.yaml_l2_parser=PARSING_MODE_YML
		

		
		with open(self.yaml_l2_file,'r') as file_yaml:
			data_l2_trunk=yaml.load(file_yaml,Loader=yaml.SafeLoader)
			
		with open(self.yaml_l2_parser,'r') as file_yaml:
			self.parsingInfo=yaml.load(file_yaml,Loader=yaml.SafeLoader)
			
		try:
			self.equipments=data_l2_trunk[env][tag]
			
		except KeyError as E:
			print("Verify YAML file",self.yaml_l2_file)
			raise(E)
			
		cacheL2=cc.Cache(self.tag)
		
		if cacheL2.isOK() and not renew:
			print('Cache Info Vlan is used for',self.tag) 
			self.interfaces=cacheL2.getValue()
		else:
			print('Cache l2 absent or not used',self.tag) 
			self.initVlanTrunk()
			cacheL2.save(self.interfaces)
			
		cacheDb=cc.Cache(self.tag_db)
		
		if cacheDb.isOK() and not renew:
			print('Cache Vlan db is used for',self.tag) 
			self.vlans=cacheDb.getValue()
		else:
			print('Cache Vlan Db absent or not used',self.tag) 
			self.initVlanDb()
			cacheDb.save(self.vlans)
		
		
		
		
			
	def get_type(self,equipment,interface):
		try:
			return self.equipments[equipment][interface]['type']
		except KeyError as E:
			print(E)
			pdb.set_trace()
		except TypeError as E:
			print(E)
			pdb.set_trace()
			return None
		
	@staticmethod
	def ParsingInterfaceOverlay(String__):
		Resultat={}
		id__={'0':'0'}
		id__noip={'0':'0'}
		Space=pp.Suppress(pp.OneOrMore(pp.White(' ')))
		Exclamations=pp.Suppress(pp.OneOrMore(pp.Literal('!')))
		Interface=pp.Combine(pp.LineStart().suppress()+pp.Literal('interface')+pp.OneOrMore(pp.CharsNotIn('\n')))
		HeadToIgnore=pp.SkipTo(Interface).suppress()
		Keyname_entry=Space+pp.MatchFirst([pp.Literal('switchport mode'),
											pp.Literal('ip helper-address').setParseAction(inser_inc(id__,'ip helper-address ')),
											pp.Literal('ip address').setParseAction(lambda t : t[0].replace('ip address','IP')),
											pp.Literal('ipv4 address').setParseAction(lambda t : t[0].replace('ip address','IP')),
											pp.Literal('ip vrf forwarding').setParseAction(lambda t : t[0].replace('ip vrf forwarding','vrf')),
											pp.Literal('vrf member').setParseAction(lambda t : t[0].replace('vrf member','vrf')),
											pp.Literal('switchport access vlan').setParseAction(lambda t : t[0].replace('switchport access vlan','access vlan')),
											pp.Literal('switchport trunk allowed vlan').setParseAction(lambda t : t[0].replace('switchport trunk allowed vlan','trunk vlan')),
											pp.Literal('switchport trunk native vlan').setParseAction(lambda t : t[0].replace('switchport trunk native vlan','native vlan')),
											pp.Literal('otv isis authentication-type').setParseAction(lambda t : t[0].replace('otv isis authentication-type','otv isis auth')),
											pp.Literal('otv isis authentication key-chain').setParseAction(lambda t : t[0].replace('otv isis authentication key-chain','otv auth key')),
											pp.Literal('otv extend-vlan').setParseAction(lambda t : t[0].replace('otv extend-vlan','otv vlan')),
											pp.Literal('otv adjacency-server unicast-only').setParseAction(lambda t : t[0].replace('otv adjacency-server unicast-only','otv adj srv')),
											pp.Literal('ip policy route-map'),
											pp.Literal('ip access-group'),
											pp.Literal('ip arp timeout'),
											pp.Literal('ip mtu'),
											pp.Literal('mtu'),
											pp.Literal('arp timeout').setParseAction(lambda t : t[0].replace('arp timeout','ip arp timeout')),
											pp.Literal('spanning-tree bpdufilter'),
											pp.Combine(pp.Literal('ip ospf ')+pp.Word(pp.alphanums+'-')),
											pp.Literal('no ip').setParseAction(inser_inc(id__,'no ip ')),
											pp.Literal('spanning-tree port type '),
											pp.Word(pp.alphanums+'-')])+Space
		Interface_key=pp.Combine(pp.LineStart().suppress()+pp.Literal("interface ")+pp.OneOrMore(pp.CharsNotIn('\n')))
		Value = pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))+pp.LineEnd().suppress()
		interfaceEntry = pp.dictOf(Keyname_entry, pp.Optional(Value,default=None))
		OneWordOnly=Space+pp.Word(pp.alphas).setParseAction(lambda t : { t[0]:'enable'})+pp.LineEnd()
		interfaceDef=pp.dictOf(Interface,pp.MatchFirst([OneWordOnly+pp.Optional(Exclamations),pp.Optional(interfaceEntry,default={})+pp.Optional(Exclamations)]))
		BlocsInterface=(HeadToIgnore+interfaceDef).setParseAction(initValueInterface)
		
		Resultat=BlocsInterface.parseString(String__).asList()
	
		key=list(Resultat[0].keys())[0].strip()
		value=[t for t in Resultat[0].values()]
		try:
			return { key: [  value[0]['status'] , 'overlay' , '0' , '0' ,value[0]['otv vlan'].strip() ] }
		except KeyError as E:	
			pdb.set_trace()
			print(E)
	
	def initVlanDb(self):
		self.vlans={}
		for equipment in self.equipments:
			commande_cur="sh vlan"
			con_get_vlan=connexion(equipement(equipment),None,None,None,'SSH',"TMP/"+equipment.lower()+"_shvlandb.log","TMP",commande_cur,timeout=600,verbose=False)
			vlan_cur=con_get_vlan.launch_withParser(ParseVlandb)
			if not vlan_cur:
				vlan_cur=ParseVlandb("TMP/"+equipment.lower()+"_shvlandb.log",mode='file')
			self.vlans[equipment]=vlan_cur
			
	def initVlanTrunk(self):
		self.interfaces={}
		for equipment in self.equipments:
			self.interfaces[equipment]={}
			for interface in self.equipments[equipment]:
				parser_cur=eval(self.parsingInfo[self.equipments[equipment][interface]['type']]['parser'])				
				commande_cur=self.parsingInfo[self.equipments[equipment][interface]['type']]['commande'].replace('<PORT>',interface)
				con_get_l2=connexion(equipement(equipment),None,None,None,'SSH',"TMP/"+equipment.lower()+"_shl2.log","TMP",commande_cur,timeout=300,verbose=False)
				vlan_cur=con_get_l2.launch_withParser(parser_cur)
				
				try:
					self.interfaces[equipment][interface]=list(vlan_cur.values())[0]
				except IndexError as E:
					pdb.set_trace()
					print(E)
				
		
	def __str__(self):
		return pprint.pformat(self.interfaces,width=200)
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('-e','--env',action="store",help='Environment',required=True)
	parser.add_argument('-t','--tag',action="store",help='tag that represents the flow')
	parser.add_argument('--renew',default=False,action="store_true",help='Force Cache renew')
	parser.add_argument('--vlan',action="store",help='Check Path for Vlan Liste')
	parser.add_argument('--xlsx',action="store",help='Excel File thats contains VLAN')
	parser.add_argument('--config',action="store",help='Directory that contains needed configuration')	

	args = parser.parse_args()
	
	if not args.xlsx and not args.tag:
		raise argparse.ArgumentError(None,'--xlsx  or --tag is required ')
		
	if args.xlsx and args.tag:
		raise argparse.ArgumentError(None,'--xlsx  and --tag is mutually  exclusive ')
		
	if args.xlsx and args.vlan:
		raise argparse.ArgumentError(None,'--xlsx  and --vlan is mutually  exclusive ')
	
	if not args.xlsx:
		L2ENV=l2env(args.env,args.tag,args.renew)
	
	#print(str(L2ENV))
	
	VlanMissing={}
	VlanMissingDb={}
	if args.vlan:
		print("Trunk verification")
		for equipment in L2ENV.interfaces:
			print("Check Trunk L2:",equipment)
			if equipment not in VlanMissing:
				VlanMissing[equipment]={}
			for interface in L2ENV.interfaces[equipment]:
				if interface not in VlanMissing[equipment]:
					VlanMissing[equipment][interface]=[]
				print(" interface:",interface)
				vlans_cur=L2ENV.interfaces[equipment][interface][-1]
				Liste_eq_if_cur=ParseVlanListe.liste_vlans(vlans_cur)
				Missing_cur=Liste_eq_if_cur.get_missing_vlan(ParseVlanListe.liste_vlans(args.vlan),verbose=True)
				if Missing_cur:
					VlanMissing[equipment][interface]+=[{'type':L2ENV.get_type(equipment,interface),'vlan_missing':Missing_cur}]
				print('\n\n')
		
		print("vlan Databse verification")
		for equipment in L2ENV.vlans:
			for vlan in ParseVlanListe.liste_vlans(args.vlan).explode():
				if equipment not in VlanMissingDb:
					VlanMissingDb[equipment]=[]
				test_cur=True
				if vlan not in L2ENV.vlans[equipment]:
					test_cur=False
				else:
					if L2ENV.vlans[equipment][vlan][1]!='active':
						test_cur=False
				
				if not test_cur:
					print("Vlan ",vlan," is missing on ",equipment)
					VlanMissingDb[equipment].append(vlan)
				
	if args.xlsx:
		(VlanByTag,otherInfo)=initXls(args.xlsx)
		L2ENV={}
		for tag in VlanByTag:
			print('TAG:',tag)
			L2ENV_CUR=l2env(args.env,tag,args.renew)
			vlans_to_check=','.join(VlanByTag[tag])
			L2ENV[tag]=L2ENV_CUR
			for equipment in L2ENV_CUR.interfaces:
				print("Check ",equipment)
				if equipment not in VlanMissing:
					VlanMissing[equipment]={}
				for interface in L2ENV_CUR.interfaces[equipment]:
					if interface not in VlanMissing[equipment]:
						 VlanMissing[equipment][interface]=[]
					print(" interface:",interface)
					vlans_cur=L2ENV_CUR.interfaces[equipment][interface][-1]
					Liste_eq_if_cur=ParseVlanListe.liste_vlans(vlans_cur)
					Missing_cur=Liste_eq_if_cur.get_missing_vlan(ParseVlanListe.liste_vlans(vlans_to_check),verbose=True)
					if Missing_cur:
						VlanMissing[equipment][interface]+=[{'type':L2ENV_CUR.get_type(equipment,interface),'vlan_missing':Missing_cur}]
					print('\n\n')
			for equipment in L2ENV_CUR.vlans:
				for vlan in VlanByTag[tag]:
					if equipment not in VlanMissingDb:
						VlanMissingDb[equipment]=[]
					test_cur=True
					if vlan not in L2ENV_CUR.vlans[equipment]:
						test_cur=False
					else:
						if L2ENV_CUR.vlans[equipment][vlan][1]!='active':
							test_cur=False
					
					if not test_cur:
						print("Vlan ",vlan," is missing on ",equipment)
						VlanMissingDb[equipment].append(vlan)



		pprint.pprint(VlanMissing)
		pprint.pprint(VlanMissingDb)
		
	if args.config:
		if not os.path.exists(args.config):
			os.makedirs(args.config)
			
		ConfigToAdd={}
		
		for equipment in VlanMissing:
			ConfigToAdd[equipment]=""
			
			
			for interface in VlanMissing[equipment]:
				infos_cur=VlanMissing[equipment][interface]
				for info_cur in infos_cur:
					if VlanMissing[equipment][interface]:
						if len(info_cur['vlan_missing']):
							if info_cur['type']=='trunk':
								ConfigToAdd[equipment]+="interface "+interface+"\n"
								ConfigToAdd[equipment]+=" switchport trunk allowed vlan add "+','.join(info_cur['vlan_missing'])+"\n"
							elif info_cur['type']=='overlay':
								ConfigToAdd[equipment]+="interface "+interface+"\n"
								ConfigToAdd[equipment]+=" otv extend-vlan add "+','.join(info_cur['vlan_missing'])+"\n"
			
		for equipment in VlanMissingDb:
			if VlanMissingDb[equipment]:
				for vlan in VlanMissingDb[equipment]:
					ConfigToAdd[equipment]+="vlan "+vlan+"\n"
		
		Resultconfig=ConfigToAdd.copy()
		for equipment in ConfigToAdd:
			if not ConfigToAdd[equipment]:
				del Resultconfig[equipment]
		pprint.pprint(Resultconfig,width=400)
		
		for equipment in Resultconfig:
			filename_cur=args.config+'/'+ equipment.upper()+'.CFG'
			with open(filename_cur,'w') as file_w:
				file_w.write(Resultconfig[equipment])
			
	
	