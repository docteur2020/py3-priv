#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals


import pyparsing as pp
from ipaddress import ip_address as ipaddr
from ipcalc import Network , IP
import argparse
import re
import pdb
import csv
import glob
import pickle
import re
from extractMacFromXls import hostnames
import string
from getArpFirewall import *
import dns.resolver
import jinja2
import yaml
from time import gmtime, strftime , localtime
from ParseVlanListe import liste_vlans,vlan

PATH_YAML='/home/x112097/yaml/parseResult'

def saveResult(result,saveName):
		suffix=strftime("_%Y%m%d_%Hh%Mm%Ss.yml", localtime())
		filename=PATH_YAML+'/'+saveName+suffix
		with open(filename,'w') as yml_w:
			 yaml.dump(result,yml_w ,default_flow_style=False)

def getReverseDns(IP):
	name_cur=None
	try:
		name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),'192.16.207.80').answer[0].__str__().split()[-1] 
	except IndexError:
		try:
			name_cur=dns.query.udp(dns.message.make_query(dns.reversename.from_address(IP), dns.rdatatype.PTR, use_edns=0),'184.12.21.17').answer[0].__str__().split()[-1]
		except IndexError:
			pass
	except AttributeError as e:
		pdb.set_trace()
		print(e)
		
	return name_cur
	
def genere_mask_dict():
	resultat={}
	for i in range(0,33):
		resultat[Network("0.0.0.0/"+str(i)).netmask().__str__()]=str(i)
	return resultat

entete__=['EQUIPEMENT','INTERFACE','DESCRIPTION','MAC','IP','PORT-CHANNEL','STATUS=[DESC,STATUS,VLAN,DUPLEX,SPEED]','SWITCHPORT=[STATUS,MODE,ACCESS VLAN,NATIVE VLAN,TRUNK VLAN]']

def getClassfulIP(ip__):
	resultat="INDETERMINE"
	try:
		if ipaddr(ip__) <= ipaddr('127.255.255.255'):
			resultat='A'
		elif ipaddr(ip__) >= ipaddr('128.0.0.0') and ipaddr(ip__) <= ipaddr('191.255.255.255'):
			resultat='B'
		elif ipaddr(ip__) >= ipaddr('192.0.0.0') and ipaddr(ip__) <= ipaddr('223.255.255.255'):
			resultat='C'
		elif ipaddr(ip__) >= ipaddr('224.0.0.0') and ipaddr(ip__) <= ipaddr('239.255.255.255'):
			resultat='D'
		elif ipaddr(ip__) >= ipaddr('240.0.0.0') and ipaddr(ip__) <= ipaddr('255.255.255.255'):
			resultat='E'
			
	except ValueError as E:
		print(E)
		
	return resultat
	
def getDefaultMask(ip__):
	resultat=32
	Dict_class={'A':'8','B':'16','C':'24','D':'32','E':'32'}
	if ip__=='0.0.0.0':
		resultat='0'
	else:
		Class__=getClassfulIP(ip__)
		try:
			resultat=Dict_class[Class__]
		except:
			pass
	return resultat

class DC(object):
	"Classe template de configuration"
	def __init__(self,MAC__={},DESC__={},ARP__={},STATUS__={},PORTCHANNEL__={},SWITCHPORT__={}):
		
		self.macs=MAC__
		self.descriptions=DESC__
		self.arps=ARP__
		self.status=STATUS__
		self.portchannels=PORTCHANNEL__
		self.switchports=SWITCHPORT__
		self.macByVlan={}
		self.arpByVlan={}
		self.initMacByVlans()
		self.initArpByVlans()
		
	def __str__(self):
		return str(self.macs)+'\n'+str(self.descriptions)+'\n'+str(self.status)+'\n'+str(self.portchannels)+str(self.switchports)
		
	def save(self,filename):

		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def initMacByVlans(self):
		
		for equipment in self.macs:
			for interface in self.macs[equipment]:
				entry_mac=self.macs[equipment][interface]
				if entry_mac and entry_mac!='None':
					description=entry_mac[1]
					liste_mac=entry_mac[0]
					if isinstance(liste_mac,list):
						for mac_info in liste_mac:
							vlan=mac_info[0]
							mac=mac_info[1]
							if mac in self.macByVlan:
								if vlan in self.macByVlan[mac]:
									self.macByVlan[mac][vlan].append([equipment,interface,description])
								else:
									self.macByVlan[mac][vlan]=[[equipment,interface,description]]
							else:
								self.macByVlan[mac]={vlan:[[equipment,interface,description]]}
								
	def initArpByVlans(self):
		
		for mac in self.arps:
			for entry in self.arps[mac]:
				if not re.search('Vlan',entry[2]):
					continue
				vlan_cur=entry[2].replace('Vlan','')
				if mac in self.arpByVlan:
					if vlan_cur in self.arpByVlan[mac]:
						self.arpByVlan[mac][vlan_cur].append(entry)
					else:
						self.arpByVlan[mac][vlan_cur]=[entry]
						
				else:
					 self.arpByVlan[mac]={vlan_cur:[entry]}

	def load(self,filename):
		
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
			
		try:
			self.macs=dc.macs
			self.descriptions=dc.descriptions
			self.status=dc.status
			self.arps=dc.arps
			self.portchannels=dc.portchannels
			self.switchports=dc.switchports
			try:
				self.macByVlan=dc.macByVlan
			except AttributeError:
				self.macByVlan={}
				self.initMacByVlans()
				
			try:
				self.arpByVlan=dc.arpByVlan
			except AttributeError:
				self.arpByVlann={}
				self.initArpByVlans()
		except:
			print('ERROR')
			
	def getInterfaceFromPo(self,equipement,interface_po):
		id_po=interface_po.replace('Po','').replace('po','')
		resultat=[]
		for entry in self.portchannels[equipement]:
			if id_po==entry[0]:
				for inter__ in entry[3]:
					resultat.append(inter__[0])
				break;
					
				
		return resultat
			
	def extractInterface(self,equipement__,interface__):
		resultat=None
		equipement=equipement__.lower()
		interface=interface__.replace('\n','')
		mac_po=None
		Switchport_cur=str(getSwitchport(interface,equipement,self.switchports))
		try:
			mac_cur=str(self.macs[equipement][interface][0])
			#pdb.set_trace()
			description=str(self.descriptions[equipement][interface])
			Po_cur=getPortChannel(interface,equipement,self.portchannels)
			Desc_Po=None
			try:
				Desc_Po=self.descriptions[equipement][Po_cur]
			except KeyError:
				Desc_Po=None
			try:
				Po_comp=getPortChannelComplete(interface,equipement,self.portchannels)
			except:
				Po_comp=None
			Status_Cur=str(self.status[equipement][interface])
			
			
			if mac_cur == 'None' and Po_cur != None:
				mac_cur=str(self.macs[equipement][str(Po_cur)][0])
				#pdb.set_trace()
				mac_po=True
			try:
				#pdb.set_trace()
				
				if not mac_po:
					Arp_cur=getArp(self.arps,self.macs[equipement][interface])
				else:
					Arp_cur=getArp(self.arps,self.macs[equipement][str(Po_cur)])
					
			except TypeError:
				#pdb.set_trace()
				pass
		except KeyError:		
		
			try:
				description=str(self.descriptions[equipement][interface])
			except KeyError:
				pdb.set_trace()	
			try:
				Status_Cur=str(self.status[equipement][interface])
			except KeyError:
				pdb.set_trace()	
			try:
				Po_cur=getPortChannel(interface,equipement,self.portchannels)	
			except:
				Po_cur=None
				#pdb.set_trace()	
			try:
				Po_comp=getPortChannelComplete(interface,equipement,self.portchannels)
			except:
				Po_comp=None
				
			try:
				Desc_Po=self.descriptions[equipement][Po_cur]
			except KeyError:
				Desc_Po=None
				
			Arp_cur=None
			print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+";Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)			
		
		
		resultat=[equipement,interface,description,mac_cur,Arp_cur,str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)]
		
		return resultat
		
		
						
	def extractInterfaces(self,interface_csv):
		with open(interface_csv,'r') as file_info_port:
			resultat_csv=[]
			resultat_csv.append(entete__)
			for ligne in file_info_port:
				ligne_col=[ x for x in  re.split(',|;| ',ligne)  if x ]
				equipement=ligne_col[0].lower()
				interface=ligne_col[1].replace('\n','')
				mac_po=False
				try:
					mac_cur=str(self.macs[equipement][interface][0])
					#pdb.set_trace()
					description=str(self.descriptions[equipement][interface])
					Po_cur=getPortChannel(interface,equipement,self.portchannels)
					Desc_Po=None
					try:
						Desc_Po=self.descriptions[equipement][Po_cur]
					except KeyError:
						Desc_Po=None
					Po_comp=getPortChannelComplete(interface,equipement,self.portchannels)
					Status_Cur=str(self.status[equipement][interface])
					Switchport_cur=str(getSwitchport(interface,equipement,self.switchports))
					
					if mac_cur == 'None' and Po_cur != None:
						mac_cur=str(self.macs[equipement][str(Po_cur)][0])
						#pdb.set_trace()
						mac_po=True
					try:
						#pdb.set_trace()
						
						if not mac_po:
							Arp_cur=getArp(self.arps,self.macs[equipement][interface])
						else:
							Arp_cur=getArp(self.arps,self.macs[equipement][str(Po_cur)])
							
						print(equipement+" "+interface+":"+mac_cur+" L3:"+str(Arp_cur)+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
						resultat_csv.append([equipement,interface,description,mac_cur,str(Arp_cur),str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)])
					except TypeError:
						#pdb.set_trace()
						pass
						print(equipement+" "+interface+":"+mac_cur+" L3:None"+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
						resultat_csv.append([equipement,interface,description,mac_cur,'None',str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)])		
				except KeyError as e:		
					print(e)
					pdb.set_trace()
					try:
						description=str(self.descriptions[equipement][interface])
					except KeyError:
						pdb.set_trace()	
					try:
						Status_Cur=str(self.status[equipement][interface])
					except KeyError:
						pdb.set_trace()
					try:
						Po_cur=getPortChannel(interface,equipement,self.portchannels)	
					except:
						pdb.set_trace()
					try:
						print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
					except UnboundLocalError as e:
						print(e)
						pdb.set_trace()
					resultat_csv.append([equipement,interface,description,['None'],'None',str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)])					
		
		return resultat_csv
		
	def extractInterfaces_from_list(self,liste_interface):
		resultat_csv=[]
		for port__ in liste_interface:
			equipement=port__[0].lower()
			interface=port__[1]
			mac_po=False
			try:
				mac_cur=str(self.macs[equipement][interface][0])
				#pdb.set_trace()
				description=str(self.descriptions[equipement][interface])
				Po_cur=getPortChannel(interface,equipement,self.portchannels)
				Desc_Po=None
				try:
					Desc_Po=self.descriptions[equipement][Po_cur]
				except KeyError:
					Desc_Po=None
				Po_comp=getPortChannelComplete(interface,equipement,self.portchannels)
				Status_Cur=str(self.status[equipement][interface])
				Switchport_cur=str(getSwitchport(interface,equipement,self.switchports))
				
				if mac_cur == 'None' and Po_cur != None:
					mac_cur=str(self.macs[equipement][str(Po_cur)][0])
					#pdb.set_trace()
					mac_po=True
				try:
					#pdb.set_trace()
					
					if not mac_po:
						Arp_cur=getArp(self.arps,self.macs[equipement][interface])
					else:
						Arp_cur=getArp(self.arps,self.macs[equipement][str(Po_cur)])
						
					print(equipement+" "+interface+":"+mac_cur+" L3:"+str(Arp_cur)+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
					resultat_csv.append([equipement,interface,description,mac_cur,str(Arp_cur),str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)])
				except TypeError:
					#pdb.set_trace()
					pass
					print(equipement+" "+interface+":"+mac_cur+" L3:None"+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
					resultat_csv.append([equipement,interface,description,mac_cur,'None',str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)])		
			except KeyError as e:		
				print(e)
				pdb.set_trace()
				try:
					description=str(self.descriptions[equipement][interface])
				except KeyError:
					pdb.set_trace()	
				try:
					Status_Cur=str(self.status[equipement][interface])
				except KeyError:
					pdb.set_trace()
				try:
					Po_cur=getPortChannel(interface,equipement,self.portchannels)	
				except:
					pdb.set_trace()
				try:
					print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
				except UnboundLocalError as e:
					print(e)
					pdb.set_trace()
				resultat_csv.append([equipement,interface,description,['None'],'None',str(Po_comp),Status_Cur,Switchport_cur,str(Desc_Po)])					
		
		return resultat_csv

	def extract_port_vlans (self,vlan__):
		result=[]
		vlans_lst=liste_vlans(vlan__)
		
		for vlan_obj in vlans_lst:
			vlans_obj=vlan(int(vlan_obj))
			#pdb.set_trace()
			#print("MACS:")
			#print(self.macs)
			#pdb.set_trace()
			for equipment__ in self.switchports.keys():
				#pdb.set_trace()
				for port__ in self.switchports[equipment__].keys():
					mac__=[]
					try:
						status__=self.status[equipment__][getShortPort(port__)]
					except KeyError:
						continue
						pass
					
					try:
						switchport__=self.switchports[equipment__][port__]
					except KeyError:
						pdb.set_trace()
						pass
					try:
						description__=self.descriptions[equipment__][getShortPort(port__)]
					except KeyError:
						pdb.set_trace()
						pass
						
					try:
						vlans__=None
						if status__[1]=="connected":
							#pdb.set_trace()
							if switchport__[1]=="access" or switchport__[1]=="static access":
								vlans__=switchport__[2]
								#pdb.set_trace()
							elif switchport__[1]=="trunk":
								vlans__=switchport__[4]
								#pdb.set_trace()
					except IndexError:
						pdb.set_trace()
						pass		
						
					if vlans__ :
						vlans__cur_obj=liste_vlans(vlans__)
						if vlans_obj in vlans__cur_obj:
							if self.macs[equipment__][getShortPort(port__)][0]!=None and type(self.macs[equipment__][getShortPort(port__)][0])==list:
								for mac_cur in self.macs[equipment__][getShortPort(port__)][0]:
									#print("MAC CUR LIST:"+equipment__+" "+port__)
									#print(mac_cur_list)
									#print("FIN__MAC CUR LIST:\n\n")
									#pdb.set_trace()
									if mac_cur != None:
										#pdb.set_trace()
										try:
											if vlans_obj in liste_vlans(mac_cur[0]):
												mac__.append(mac_cur)
										except:
											print('ERROR')
											pdb.set_trace()
		
	
							if mac__ :
								if [equipment__,port__,description__,switchport__[1],vlans__ ,switchport__,status__[1],mac__] not in result:
									result.append([equipment__,port__,description__,switchport__[1],vlans__ ,switchport__,status__[1],mac__])
							else:
								if [equipment__,port__,description__,switchport__[1],vlans__ ,switchport__,status__[1],"None"] not in result:
									result.append([equipment__,port__,description__,switchport__[1],vlans__ ,switchport__,status__[1],"None"])
							
		#pdb.set_trace()
	
		return result	

	def extract_ip(self,ip__):
		result=[]

		for mac__ in self.arps.keys():
			entries=self.arps[mac__]
			try:
				for entry in entries:
					if ip__==entry[3]:
						result.append([mac__]+entry)
					
			
			except IndexError:
				print('Erreur Index:'+str(entry))
		#pdb.set_trace()
	
		return result		
		
	def extract_all_ip(self):
		result={}

		fw_json=getLastDumpArpFW()
		for equipement__ in self.macs.keys():
			for interface__ in self.macs[equipement__].keys():
				macs_cur=self.macs[equipement__][interface__][0]
				if macs_cur:
					for mac_cur in macs_cur:
						if mac_cur[1] in self.arps.keys():
							ip_info_1=self.arps[mac_cur[1]]
						else:
							ip_info_1=None
						ip_info_2=get_arp_entry(fw_json,mac_cur[1])
						if ip_info_1 and ip_info_2:
							ip_info=ip_info_1+[[ip_info_2['firewall'],'GRT','Vlan'+mac_cur[0],ip_info_2['ip']]]
						elif ip_info_1:
							ip_info=ip_info_1
						elif ip_info_2:
							ip_info=[[ip_info_2['firewall'],'GRT','Vlan'+mac_cur[0],ip_info_2['ip']]]
						else:
							ip_info=None
						if mac_cur[1] not in result.keys():
							if ip_info:
								result[mac_cur[1]]={'vlan':mac_cur[0],'IP':ip_info}
					

	
		return result	

	def extract_mac (self,mac_param,vlan=""):
		result=[]
		
		mac__=hostnames.mac_to_cisco(mac_param)
		
		if mac__=='NULL':
			mac__=mac_param
		
		if not vlan:
			for equipment__ in self.macs.keys():
				#pdb.set_trace()
				for port__ in self.macs[equipment__].keys():
					if self.macs[equipment__][port__][0]:
						for mac_cur in self.macs[equipment__][port__][0]:
							if mac_cur==None:
								pdb.set_trace()
							if mac__ == mac_cur[1]:
								try:
									description__=self.descriptions[equipment__][getShortPort(port__)]
								except KeyError:
									pdb.set_trace()
									pass
								try:
									switchport__=self.switchports[equipment__][port__]
								except KeyError:
									try:
										switchport__=self.switchports[equipment__][getLongPort(port__)]
									except KeyError:
										switchport__="UNKNOWN"
										pass
								if not vlan:
									result.append([equipment__,port__,mac__,description__,mac_cur[0],switchport__])
								else:
									if mac_cur[0]==vlan:
										result.append([equipment__,port__,mac__,description__,mac_cur[0],switchport__])
		else:
			try:
				for entry in self.macByVlan[mac__][vlan]:
					try:
						switchport__=self.switchports[entry[0]][getLongPort(entry[1])]
					except KeyError:
						switchport__="UNKNOWN"
						pass
					
					result.append([entry[0],entry[1],mac__,entry[2],vlan,switchport__])
			except KeyError as E:
				result=[]
				print(E)
				#pdb.set_trace()
							
							
		return result

	def extract_macs(self,macs__,vlan=""):
		result=[]
		
		if not vlan:
			if re.search(',',macs__):
				liste_mac=macs__.split(',')
				
				for mac__ in liste_mac:
					#print(mac__)
					result=result+self.extract_mac(mac__)
					
			else:
				result=self.extract_mac(macs__)
		else:
			result=self.extract_mac(macs__,vlan=vlan)
			#print('ici:',macs__,vlan,result)

			
		return result
		
	def getArpDC(self,mac__,vlan=""):
		result=None
		
		if not vlan:
			if mac__ in self.arps:
				result=self.arps[mac__]
		else:
			if mac__ in self.arpByVlan:
				if vlan in self.arpByVlan[mac__]:
					result=self.arpByVlan[mac__][vlan]
			
		return result
		
	def getInfoMac(self,mac__,vlan=""):
	
		info__=self.extract_mac(mac__,vlan=vlan)
		ips__=self.getArpDC(mac__,vlan=vlan)
		dns__= {}
		
		if ips__:
			for ip__ in ips__:
				try:
					dns__[ip__[3]]=getReverseDns(ip__[3])
				except IndexError as E:
					pdb.set_trace()
					print(E)


				
		return [mac__]+[ips__]+[dns__]
		

def ParseVrf(String__):

	Resultat=None
	
	Show=pp.Suppress((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.OneOrMore(pp.Word(pp.alphanums)))+pp.Literal('\n')
	FirstLine_Nexus=pp.Suppress(pp.Literal('VRF-Name')+pp.Literal('VRF-ID')+ pp.Literal('State')+pp.Literal('Reason'))
	FirstLine_Cisco=pp.Suppress(pp.Literal('Name')+pp.Literal('Default')+ pp.Literal('RD')+pp.Literal('Interfaces'))
	FirstLine=FirstLine_Cisco | FirstLine_Nexus
	VRF_Nexus=pp.Word(pp.alphanums+"-_")+pp.Suppress(pp.Word(pp.nums)+pp.Literal("Up")+pp.Literal('--'))
	VRF_Cisco=pp.Word(pp.alphanums+"-_")+pp.Suppress(pp.Word(pp.nums)+pp.Literal(":")+pp.Word(pp.nums)+pp.Word(pp.printables))
	VRF=VRF_Nexus|VRF_Cisco
	Interface_Only=pp.Suppress(pp.printables)
	LastLine=pp.Suppress(pp.Word(pp.printables+'#'))
	Line=Show|FirstLine|VRF|LastLine|Interface_Only
	Lines=pp.OneOrMore(Line)
	

	Resultat=Lines.parseString(String__).asList()

	return Resultat
	
def parseShIntFex(String__):
	Resultat={}
	id__={'0':'0'}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress(pp.Literal("Fabric")+pp.nestedExpr(opener='Fabric',closer='Serial'))
	Limite=pp.Suppress(pp.Literal('------')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Interface=pp.Combine(pp.Literal('Eth')+pp.Word(pp.nums+'/'))
	Uplink=pp.Word('01234',exact=1)
	FexID=pp.Word(pp.nums,exact=3)|(pp.Literal('---').setParseAction(replace_id(id__)))
	FexState=pp.CaselessLiteral("Configured")|pp.CaselessLiteral("Active")
	FexModel=pp.Combine(pp.Literal("N2K")+pp.Word(string.ascii_uppercase+"-"+pp.nums))
	SerialNumber=pp.Word(string.ascii_uppercase+pp.nums,min=9)
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	ToSuppress=Show|hostname
	EntryFexActive=pp.Group(FexID+Interface+FexState+Uplink+pp.Optional(FexModel,default=None)+pp.Optional(SerialNumber,default=None))
	EntryFexConfigured=pp.Group(FexID+Interface+pp.CaselessLiteral("Configured")+Uplink)
	EntryFex=pp.MatchFirst([EntryFexActive,EntryFexConfigured])
	Entries=Show+Legend+Limite+pp.OneOrMore(EntryFex)
	
	ResultatList=Entries.parseString(String__).asList()
	
	for entry in ResultatList:
		fexid_cur= entry[0]
		if fexid_cur not in Resultat.keys():
			Resultat[fexid_cur]=[entry[1:]]
		else:
			Resultat[fexid_cur].append(entry[1:])
	
	return Resultat
	
def parseShIntFexFile(File__):
	Resultat={}
	id__={'0':'0'}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress(pp.Literal("Fabric")+pp.nestedExpr(opener='Fabric',closer='Serial'))
	Limite=pp.Suppress(pp.Literal('------')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Interface=pp.Combine(pp.Literal('Eth')+pp.Word(pp.nums+'/'))
	Uplink=pp.Word('01234',exact=1)
	FexID=pp.Word(pp.nums,exact=3)|(pp.Literal('---').setParseAction(replace_id(id__)))
	FexState=pp.CaselessLiteral("Configured")|pp.CaselessLiteral("Active")
	FexModel=pp.Combine(pp.Literal("N2K")+pp.Word(string.ascii_uppercase+"-"+pp.nums))
	SerialNumber=pp.Word(string.ascii_uppercase+pp.nums,min=9)
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	ToSuppress=Show|hostname
	EntryFexActive=pp.Group(FexID+Interface+FexState+Uplink+pp.Optional(FexModel,default=None)+pp.Optional(SerialNumber,default=None))
	EntryFexConfigured=pp.Group(FexID+Interface+pp.CaselessLiteral("Configured")+Uplink)
	EntryFex=pp.MatchFirst([EntryFexActive,EntryFexConfigured])
	Entries=Show+Legend+Limite+pp.OneOrMore(EntryFex)
	
	ResultatList=Entries.parseFile(File__).asList()
	
	for entry in ResultatList:
		fexid_cur= entry[0]
		if fexid_cur not in Resultat.keys():
			Resultat[fexid_cur]=[entry[1:]]
		else:
			Resultat[fexid_cur].append(entry[1:])
			
	return Resultat
	
def ParseShNextPo(String__):

	Resultat=None
	Show=pp.Suppress((pp.CaselessLiteral('shNextPo')))
	Legend1=pp.Suppress(pp.Literal('Next')+pp.Literal('Available')+pp.Literal('Port-channel')+pp.Literal('IDs'))
	Legend2=pp.Suppress(pp.Literal('Desc.')+pp.Literal('Next')+pp.Literal('ID'))
	Interligne=pp.Suppress((pp.Word('=',min=10)))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Desc=(pp.CaselessLiteral('Non VPC Po to Servers')|pp.CaselessLiteral('VPC Po to Servers')|pp.CaselessLiteral('Po on FEX')|pp.CaselessLiteral('Non VPC Po to Network Infra.')|pp.CaselessLiteral('Non VPC Po to other Infra eq. (FW,...)')|pp.CaselessLiteral('Po to FEX')|pp.CaselessLiteral('VPC Po to Network Infra.')|pp.CaselessLiteral('VPC Po to other Infra. (FW,...)')      ).setParseAction(lambda t : t[0].replace(' ','_'))
	ToSuppress=Show|Legend1|Legend2|Interligne|hostname
	nextPoID=pp.Word(pp.nums)
	Entry=pp.OneOrMore(ToSuppress)+pp.dictOf(Desc,nextPoID)+pp.ZeroOrMore(ToSuppress)
	
	Resultat=Entry.parseString(String__).asDict()
	
	return Resultat
	
def ParseShNextPoFile(File__):

	Resultat=None
	Show=pp.Suppress((pp.CaselessLiteral('shNextPo')))
	Legend1=pp.Suppress(pp.Literal('Next')+pp.Literal('Available')+pp.Literal('Port-channel')+pp.Literal('IDs'))
	Legend2=pp.Suppress(pp.Literal('Desc.')+pp.Literal('Next')+pp.Literal('ID'))
	Interligne=pp.Suppress((pp.Word('=',min=10)))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Desc=(pp.CaselessLiteral('Non VPC Po to Servers')|pp.CaselessLiteral('VPC Po to Servers')|pp.CaselessLiteral('Po on FEX')).setParseAction(lambda t : t[0].replace(' ','_'))
	ToSuppress=Show|Legend1|Legend2|Interligne|hostname
	nextPoID=pp.Word(pp.nums)
	Entry=pp.OneOrMore(ToSuppress)+pp.dictOf(Desc,nextPoID)+pp.ZeroOrMore(ToSuppress)
	
	Resultat=Entry.parseFile(File__).asDict()
	
	return Resultat
	
def replace_id(dict_id):
	def parseAction(s,l,t):
		resultat=t[0]
		dict_id['0']=str(int(dict_id['0'])+1)
		
		return "NOFEXID"+dict_id['0']
		
	return parseAction
	
def ParseShFexString(String):

	
	Resultat=None
	id__={'0':'0'}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend1=pp.MatchFirst([pp.Suppress(pp.CaselessLiteral('FEX')*5),pp.Suppress(pp.CaselessLiteral('FEX')*4)])+pp.OneOrMore(pp.CharsNotIn('\n')).suppress()
	Legend2=pp.Suppress(pp.OneOrMore(pp.CaselessLiteral('Number')|pp.CaselessLiteral('Description')|pp.CaselessLiteral('State')|pp.CaselessLiteral('Model')|pp.CaselessLiteral('Serial')))
	Legend3=pp.Suppress(pp.Word('-'))
	Legend=Legend1+Legend2+Legend3
	FexID=pp.Word(pp.nums)|(pp.Literal('---').setParseAction(replace_id(id__)))
	Description=pp.Word(pp.alphanums+"-_/")
	FexState=pp.CaselessLiteral("Online")|pp.CaselessLiteral("Offline")|pp.CaselessLiteral("Discovered")
	FexModel=pp.Word(string.ascii_uppercase+"-"+pp.nums)
	SerialNumber=pp.Word(string.ascii_uppercase+pp.nums)
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	ToSuppress=Show|hostname
	InfoFex=pp.Group(Description+FexState+FexModel+SerialNumber)
	Entries=Show+Legend+pp.dictOf(FexID,InfoFex)+pp.ZeroOrMore(ToSuppress)
	
	Resultat=Entries.parseString(String).asDict()
	
	return Resultat
	
def ParseShFex(File__):

	Resultat=None
	id__={'0':'0'}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend1=pp.MatchFirst([pp.Suppress(pp.CaselessLiteral('FEX')*5),pp.Suppress(pp.CaselessLiteral('FEX')*4)])+pp.OneOrMore(pp.CharsNotIn('\n')).suppress()
	Legend2=pp.Suppress(pp.OneOrMore(pp.CaselessLiteral('Number')|pp.CaselessLiteral('Description')|pp.CaselessLiteral('State')|pp.CaselessLiteral('Model')|pp.CaselessLiteral('Serial')))
	Legend3=pp.Suppress(pp.Word('-'))
	Legend=Legend1+Legend2+Legend3
	FexID=pp.Word(pp.nums)|(pp.Literal('---').setParseAction(replace_id(id__)))
	Description=pp.Word(pp.alphanums+"-_/")
	FexState=pp.CaselessLiteral("Online")|pp.CaselessLiteral("Offline")|pp.CaselessLiteral("Discovered")
	FexModel=pp.Word(string.ascii_uppercase+"-"+pp.nums)
	SerialNumber=pp.Word(string.ascii_uppercase+pp.nums)
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	ToSuppress=Show|hostname
	InfoFex=pp.Group(Description+FexState+FexModel+SerialNumber)
	Entries=Show+Legend+pp.dictOf(FexID,InfoFex)+pp.ZeroOrMore(ToSuppress)
	
	Resultat=Entries.parseFile(File__).asDict()
	
	return Resultat
	
def ParseShNextPoFile(File__):

	Resultat=None
	Show=pp.Suppress((pp.CaselessLiteral('shNextPo')))
	Legend1=pp.Suppress(pp.Literal('Next')+pp.Literal('Available')+pp.Literal('Port-channel')+pp.Literal('IDs'))
	Legend2=pp.Suppress(pp.Literal('Desc.')+pp.Literal('Next')+pp.Literal('ID'))
	Interligne=pp.Suppress((pp.Word('=',min=10)))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Desc=(pp.CaselessLiteral('Non VPC Po to Servers')|pp.CaselessLiteral('VPC Po to Servers')|pp.CaselessLiteral('Po on FEX')|pp.CaselessLiteral('Non VPC Po to Network Infra.')|pp.CaselessLiteral('Non VPC Po to other Infra eq. (FW,...)')|pp.CaselessLiteral('Po to FEX')|pp.CaselessLiteral('VPC Po to Network Infra.')|pp.CaselessLiteral('VPC Po to other Infra. (FW,...)')      ).setParseAction(lambda t : t[0].replace(' ','_'))
	
	ToSuppress=Show|Legend1|Legend2|Interligne|hostname
	nextPoID=pp.Word(pp.nums)
	Entry=pp.OneOrMore(ToSuppress)+pp.dictOf(Desc,nextPoID)+pp.ZeroOrMore(ToSuppress)
	
	Resultat=Entry.parseFile(File__).asDict()
	
	return Resultat
	
def ParseVrfFile(File__):

	Resultat=None
	
	Show=pp.Suppress((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.OneOrMore(pp.Word(pp.alphanums)))+pp.Literal('\n')
	FirstLine_Nexus=pp.Suppress(pp.Literal('VRF-Name')+pp.Literal('VRF-ID')+ pp.Literal('State')+pp.Literal('Reason'))
	FirstLine_Cisco=pp.Suppress(pp.Literal('Name')+pp.Literal('Default')+ pp.Literal('RD')+pp.Literal('Interfaces'))
	FirstLine=FirstLine_Cisco | FirstLine_Nexus
	VRF_Nexus=pp.Word(pp.alphanums+"-_")+pp.Suppress(pp.Word(pp.nums)+pp.Word("Up")+pp.Word('--'))
	VRF_Cisco=pp.Word(pp.alphanums+"-_")+pp.Suppress(pp.Word(pp.nums)+pp.Literal(":")+pp.Word(pp.nums)+pp.Word(pp.printables))
	VRF=VRF_Nexus|VRF_Cisco
	Interface_Only=pp.Suppress(pp.printables)
	LastLine=pp.Suppress(pp.Word(pp.printables+'#'))
	Line=Show|FirstLine|VRF|LastLine|Interface_Only
	Lines=pp.OneOrMore(Line)
	

	Resultat=Lines.parseFile(File__).asList()

	return Resultat
	
def ParseArpCiscoFile(File__):

	Resultat=None
	
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	ShowArpGrt=pp.ZeroOrMore(hostname)+((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.CaselessLiteral('ip')+pp.CaselessLiteral('arp')).setParseAction(pp.replaceWith('GRT'))
	ShowArpVrf=pp.ZeroOrMore(hostname)+ pp.Suppress((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.CaselessLiteral('ip')+pp.CaselessLiteral('arp')+pp.CaselessLiteral('vrf'))+pp.Word(pp.alphanums+"-_")
	VRF=pp.MatchFirst([ShowArpVrf,ShowArpGrt])
	Legend=pp.Suppress(pp.Literal('Protocol')+pp.Literal('Address')+pp.Literal('Age')+pp.Literal('(min)')+pp.Literal('Hardware')+pp.Literal('Addr')+pp.Literal('Type')+pp.Literal('Interface'))
	LegendNexus=pp.MatchFirst([pp.Suppress(pp.nestedExpr(opener='Flags:',closer='Interface\n') ),pp.Suppress(pp.nestedExpr(opener='Flags:',closer='Flags\n') )])
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	Incomplete=pp.CaselessLiteral('incomplete').setParseAction(pp.replaceWith('INCOMPLETE'))
	hexint = pp.Word(pp.hexnums,exact=4)
	macAddress = pp.Combine(hexint + ('.'+hexint)*2)|pp.CaselessLiteral('incomplete')
	Interface=pp.Word(pp.alphanums+('\/.-'))
	Flags=pp.Suppress(pp.Word('+*#D'))
	EntryArpNonEmpty=pp.Group(pp.Literal('Internet').suppress()+ipAddress+pp.Word(pp.nums+'-').suppress()+macAddress+pp.Word('ARPA').suppress()+Interface+pp.LineEnd().suppress())
	EntryArpEmpty=pp.Group(pp.Literal('Internet').suppress()+ipAddress+pp.Word(pp.nums+'-')+Incomplete+pp.Word('ARPA').setParseAction(pp.replaceWith('N\A'))+pp.LineEnd().suppress())
	time1=pp.Combine(pp.Word(pp.nums,exact=2) + (':' + pp.Word(pp.nums,exact=2) )*2)
	time2=pp.Word(pp.nums+".",exact=8)
	time=pp.Suppress(time1|time2)
	EntryArpNexus=pp.Group((ipAddress|Incomplete)+(time|pp.Literal('-')).suppress()+macAddress+Interface+pp.Optional(Flags))
	
	EntryArp=EntryArpNonEmpty|EntryArpEmpty

	EntriesArp=pp.Group(pp.OneOrMore(EntryArp))
	EntriesArpNexus=pp.Group(pp.ZeroOrMore(EntryArpNexus))
	
	#BlocArpVrf=pp.dictOf(VRF, (pp.Optional(Legend)+EntriesArp) | (pp.Optional(LegendNexus)+EntriesArpNexus ) )
	BlocArpVrfNexus =pp.dictOf(VRF, (pp.Optional(LegendNexus)+EntriesArpNexus ) )+pp.ZeroOrMore(hostname)
	BlocArpVrf =pp.dictOf(VRF, (pp.Optional(Legend+EntriesArp,default=[None]) ) )+pp.ZeroOrMore(hostname)
	
	try:	
		Resultat=BlocArpVrf.parseFile(File__,parseAll=True).asDict()
	except pp.ParseException as e1:
		try:
			Resultat=BlocArpVrfNexus.parseFile(File__,parseAll=True).asDict()
		except pp.ParseException as e2:
			print("Erreur parsing Cisco:"+File__)
			print(e1)
			print("Erreur parsing Nexus:"+File__)
			print(e2)
			raise(e2) 
	
	
		
	return Resultat
		
def ParseBgpNeighborFile(File__):

	Resultat=None
	Day_XR=pp.Literal('Mon')|pp.Literal('Tue')|pp.Literal('Wed')|pp.Literal('Thu')|pp.Literal('Fri')|pp.Literal('Sat')|pp.Literal('Sun')
	Month_XR=pp.Literal('Jan')|pp.Literal('Feb')|pp.Literal('Mar')|pp.Literal('Apr')|pp.Literal('May')|pp.Literal('Jun')|pp.Literal('Jul')|pp.Literal('Aug')|pp.Literal('Sep')|pp.Literal('Oct')|pp.Literal('Nov')|pp.Literal('Dec')
	Date_XR=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=31 and int(tokens[0]) >= 1 )
	Hour_XR=pp.Word(pp.nums,exact=2)+(pp.Literal(':')+pp.Word(pp.nums,exact=2))*2+pp.Literal('.')+pp.Word(pp.nums)
	Timestamp_XR=pp.Suppress(Day_XR+Month_XR+Date_XR+Hour_XR+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	ShowBGPGrt=pp.ZeroOrMore(hostname)+((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.Optional(pp.CaselessLiteral('ip'))+(pp.CaselessLiteral('bgp'))).setParseAction(pp.replaceWith('GRT'))+pp.Suppress(pp.CaselessLiteral('sum')+pp.OneOrMore(pp.CharsNotIn('\n')))
	ShowBGPVrf=pp.ZeroOrMore(hostname)+ pp.Suppress((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.Optional(pp.CaselessLiteral('ip'))+pp.CaselessLiteral('bgp')+pp.MatchFirst([pp.CaselessLiteral('vpnv4 vrf'),pp.CaselessLiteral('vrf')]))+pp.Word(pp.alphanums+"-_")+pp.Suppress(pp.CaselessLiteral('sum')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF_XR=pp.Optional(Show+Timestamp_XR)+pp.Suppress(pp.Literal('VRF: '))+pp.OneOrMore(pp.CharsNotIn('\n'))
	VRF=pp.MatchFirst([VRF_XR,ShowBGPVrf,ShowBGPGrt]).setParseAction(lambda tokens: str(tokens[0]).strip())
	LegendIOS=pp.Suppress(pp.nestedExpr(opener='BGP router identifier',closer='PfxRcd') )
	LegendNexus=pp.Suppress(pp.nestedExpr(opener='BGP summary information for',closer='PfxRcd') )
	LigneTiret=pp.Suppress(pp.LineStart()+pp.Word('-')+pp.LineEnd())
	LegendXR=LigneTiret+pp.Suppress(pp.nestedExpr(opener='BGP VRF ',closer='PfxRcd') )
	Legend=pp.MatchFirst([LegendXR,LegendNexus,LegendIOS])
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	Version=pp.Suppress(pp.Word('012345',exact=1))
	AS=pp.Word(pp.nums)
	Others=pp.Suppress(pp.Word(pp.nums)*5)
	jma=pp.Word(pp.nums)+pp.Word('ywmdh',exact=1)
	heure=pp.Word(pp.nums,min=1,max=2)+(':'+pp.Word(pp.nums,min=1,max=2) ) *2
	duree=(jma*2)|(jma*3)
	Never=pp.CaselessLiteral('never')
	time=pp.Suppress(duree|heure|Never)
	Status=pp.MatchFirst([pp.Literal("0!"),pp.Word(pp.nums),pp.OneOrMore(pp.CharsNotIn('\n'))])
	Unknown=(pp.CaselessLiteral('Unknown vrf') + pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(pp.replaceWith(None))
	NoBGP=pp.nestedExpr(opener='BGP summary information for',closer='Unicast').setParseAction(pp.replaceWith(None))
	Speaker=pp.CaselessLiteral('Speaker')+(pp.Word(pp.nums)*6)
	NoBGPXR=(LigneTiret+pp.nestedExpr(opener='BGP VRF ',closer='StandbyVer') + Speaker).setParseAction(pp.replaceWith(None))
	NoBGPXR2=(LigneTiret+pp.nestedExpr(opener='BGP VRF ',closer='command for details.') ).setParseAction(pp.replaceWith(None))
	Neighbor=pp.Group(ipAddress+Version+AS+Others+time+Status)
	BlocVrf=pp.dictOf(VRF, pp.Optional( pp.MatchFirst([Legend+pp.Group(pp.OneOrMore(Neighbor)),pp.Group(Unknown),NoBGP,NoBGPXR2,NoBGPXR]),default=None))+pp.Optional(hostname)
	Resultat=BlocVrf.parseFile(File__,parseAll=True).asDict()
	
	#pdb.set_trace()
	return Resultat
	
def ParseBgpNeighbor(String__):

	Resultat=None
	Day_XR=pp.Literal('Mon')|pp.Literal('Tue')|pp.Literal('Wed')|pp.Literal('Thu')|pp.Literal('Fri')|pp.Literal('Sat')|pp.Literal('Sun')
	Month_XR=pp.Literal('Jan')|pp.Literal('Feb')|pp.Literal('Mar')|pp.Literal('Apr')|pp.Literal('May')|pp.Literal('Jun')|pp.Literal('Jul')|pp.Literal('Aug')|pp.Literal('Sep')|pp.Literal('Oct')|pp.Literal('Nov')|pp.Literal('Dec')
	Date_XR=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=31 and int(tokens[0]) >= 1 )
	Hour_XR=pp.Word(pp.nums,exact=2)+(pp.Literal(':')+pp.Word(pp.nums,exact=2))*2+pp.Literal('.')+pp.Word(pp.nums)
	Timestamp_XR=pp.Suppress(Day_XR+Month_XR+Date_XR+Hour_XR+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	ShowBGPGrt=pp.ZeroOrMore(hostname)+((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.Optional(pp.CaselessLiteral('ip'))+(pp.CaselessLiteral('bgp'))).setParseAction(pp.replaceWith('GRT'))+pp.Suppress(pp.CaselessLiteral('sum')+pp.OneOrMore(pp.CharsNotIn('\n')))
	ShowBGPVrf=pp.ZeroOrMore(hostname)+ pp.Suppress((pp.CaselessLiteral('sh ')|pp.CaselessLiteral('show '))+pp.Optional(pp.CaselessLiteral('ip'))+pp.CaselessLiteral('bgp')+pp.MatchFirst([pp.CaselessLiteral('vpnv4 vrf'),pp.CaselessLiteral('vrf')]))+pp.Word(pp.alphanums+"-_")+pp.Suppress(pp.CaselessLiteral('sum')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF_XR=pp.Optional(Show+Timestamp_XR)+pp.Suppress(pp.Literal('VRF: '))+pp.OneOrMore(pp.CharsNotIn('\n'))
	VRF=pp.MatchFirst([VRF_XR,ShowBGPVrf,ShowBGPGrt]).setParseAction(lambda tokens: str(tokens[0]).strip())
	LegendIOS=pp.Suppress(pp.nestedExpr(opener='BGP router identifier',closer='PfxRcd') )
	LegendNexus=pp.Suppress(pp.nestedExpr(opener='BGP summary information for',closer='PfxRcd') )
	LigneTiret=pp.Suppress(pp.LineStart()+pp.Word('-')+pp.LineEnd())
	LegendXR=LigneTiret+pp.Suppress(pp.nestedExpr(opener='BGP VRF ',closer='PfxRcd') )
	Legend=pp.MatchFirst([LegendXR,LegendNexus,LegendIOS])
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	Version=pp.Suppress(pp.Word('012345',exact=1))
	AS=pp.Word(pp.nums)
	Others=pp.Suppress(pp.Word(pp.nums)*5)
	jma=pp.Word(pp.nums)+pp.Word('ywmdh',exact=1)
	heure=pp.Word(pp.nums,min=1,max=2)+(':'+pp.Word(pp.nums,min=1,max=2) ) *2
	duree=(jma*2)|(jma*3)
	Never=pp.CaselessLiteral('never')
	time=pp.Suppress(duree|heure|Never)
	Status=pp.MatchFirst([pp.Literal("0!"),pp.Word(pp.nums),pp.OneOrMore(pp.CharsNotIn('\n'))])
	Unknown=(pp.CaselessLiteral('Unknown vrf') + pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(pp.replaceWith(None))
	NoBGP=pp.nestedExpr(opener='BGP summary information for',closer='Unicast').setParseAction(pp.replaceWith(None))
	Speaker=pp.CaselessLiteral('Speaker')+(pp.Word(pp.nums)*6)
	NoBGPXR=(LigneTiret+pp.nestedExpr(opener='BGP VRF ',closer='StandbyVer') + Speaker).setParseAction(pp.replaceWith(None))
	NoBGPXR2=(LigneTiret+pp.nestedExpr(opener='BGP VRF ',closer='command for details.') ).setParseAction(pp.replaceWith(None))
	Neighbor=pp.Group(ipAddress+Version+AS+Others+time+Status)
	BlocVrf=pp.dictOf(VRF, pp.Optional( pp.MatchFirst([Legend+pp.Group(pp.OneOrMore(Neighbor)),pp.Group(Unknown),NoBGP,NoBGPXR2,NoBGPXR]),default=None))+pp.Optional(hostname)
	
	try:
		Resultat=BlocVrf.parseString(String__,parseAll=True).asDict()
	except pp.ParseException as e:
		print(e)
		print('String:'+String__)
		raise(e)
	return Resultat
	
def ParseMacCisco(String__):

	Resultat=[]
	End=pp.stringEnd|pp.LineEnd().suppress()|pp.Literal(' ').suppress()|pp.Literal('\n').suppress()|pp.Literal('\r').suppress()|pp.Literal('\r\n').suppress()
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	ID=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=65535 and int(tokens[0]) >= 0 )
	PortFP=pp.Combine(ID+((pp.Literal('.')+ID)*2))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	prompt=pp.Suppress(pp.OneOrMore(pp.Word(pp.alphanums+'-_'))+pp.Literal('#'))
	ShowAnd=pp.Suppress (pp.nestedExpr(opener='sh',closer='--\n') )
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='Legend:',closer='--\n')) 
	Legend_old=pp.Suppress (pp.nestedExpr(opener='Vlan',closer='--\n') )
	FirstLineCisco=pp.Suppress(pp.Literal('VLAN')+pp.ZeroOrMore(pp.Word(pp.printables)))
	FirstLineNexus=pp.Suppress(pp.Literal('vlan')+pp.Literal('mac')+pp.Literal('address')+pp.ZeroOrMore(pp.Word(pp.printables)))
	FirstLine=FirstLineCisco|FirstLineNexus
	Limite=pp.Suppress(pp.Literal('------')+pp.OneOrMore(pp.Word('-+'))+pp.Literal('\n'))
	Ports=pp.Suppress( (pp.CaselessLiteral('static')|pp.CaselessLiteral('dynamic')|pp.CaselessLiteral('igmp') ) + (pp.Word(pp.nums)|pp.Literal('-')|pp.Literal('~~~'))+pp.Optional(2*pp.Literal('F')))+(pp.OneOrMore(Interface|PortFP))
	hexint = pp.Word(pp.hexnums,exact=4)
	macAddress = pp.Combine(hexint + ('.'+hexint)*2)
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 1 ))
	Entry_CPU=pp.Suppress(pp.Literal('All')+macAddress+pp.Literal('STATIC')+pp.Literal('CPU'))
	EntryNexus=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+Ports)
	EntryCisco=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +(pp.Literal('Yes')|pp.Literal('No')).suppress()+(pp.Literal('-')|pp.Word(pp.nums)).suppress()+pp.OneOrMore(pp.delimitedList(Interface,delim=',')))
	EntryCiscoOld=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() + ( (pp.Literal('ip')+pp.Optional(',ipx')+pp.Optional(',assigned')+pp.Optional(',other') ) |pp.Literal('other')|pp.Literal('assigned')|pp.Literal('system')).suppress()+Interface)
	EntryCiscoOther=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +Interface)
	EmptyPort=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +(pp.Literal('Yes')|pp.Literal('No')).suppress()+(pp.Literal('-')|pp.Word(pp.nums)).setParseAction(pp.replaceWith('None')))
	SpecialEntry=pp.Group(pp.Literal('*  ---').setParseAction(pp.replaceWith('None'))+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +(pp.Literal('Yes')|pp.Literal('No')).suppress()+(pp.Literal('-')|pp.Word(pp.nums)).suppress()+pp.OneOrMore(pp.delimitedList(Interface,delim=',')))
	L3Entry=pp.Suppress(Interface+macAddress+(pp.Keyword('dynamic') |pp.Keyword('static')).suppress() + ( (pp.Literal('ip')+pp.Optional(',ipx')+pp.Optional(',assigned')+pp.Optional(',other') ) |pp.Literal('other')|pp.Literal('assigned')|pp.Literal('system')).suppress()+pp.OneOrMore(pp.delimitedList(Interface,delim=',')))
	Debut=pp.MatchFirst([ShowAnd+Legend_old,Show+Legend])
	Line=Debut|FirstLine|Limite|EntryNexus|EntryCisco|EntryCiscoOld|Entry_CPU|EmptyPort|SpecialEntry|L3Entry|prompt
	Lines=pp.OneOrMore(Line)
	
	Entry=EntryNexus|EntryCisco|EntryCiscoOld|Entry_CPU|EmptyPort|EntryCiscoOther|SpecialEntry|L3Entry
	
	#Resultat=Lines.parseFile(File__)
	
	

	for parsingEntry in Entry.scanString(String__):
		temp_list=parsingEntry[0].asList()
		try:
			if temp_list[0]:
				Resultat.append(temp_list[0])
				#pdb.set_trace()
		except IndexError:
			pass
				
	#pdb.set_trace()
	
	return Resultat
	
def ParseRunInterface(String__):
	
	Resultat={}
	
	Space=pp.OneOrMore(pp.White(' '))
	Interface=pp.Combine(pp.LineStart().suppress()+pp.Literal('interface')+Space+pp.OneOrMore(pp.CharsNotIn('\n ')))
	EntryInterface=pp.Combine(Space+pp.OneOrMore(pp.CharsNotIn('\n')))
	EntriesInterface=pp.Group(pp.OneOrMore(EntryInterface))
	BlocsInterface=pp.Group(Interface+pp.Optional(EntriesInterface,default=None))
	

	for parsingEntry in BlocsInterface.scanString(String__):
		try:
			if parsingEntry[0].asList()[0][1]:
				Resultat[ parsingEntry[0].asList()[0][0].replace('\r','')]=parsingEntry[0].asList()[0][1]
			else:
				Resultat[ parsingEntry[0].asList()[0][0].replace('\r','')]=parsingEntry[0].asList()[0][1]
		except KeyError as E:
			print(E)
			raise(E)

	return Resultat

def ParseVlanRun(String__):
	
	Resultat={}
	
	temp_list=[]
	
	Space=pp.Suppress(pp.OneOrMore(pp.White(' ')))
	VlanListe=pp.Word(pp.nums+',-')
	VlanLine=(pp.Combine(pp.LineStart().suppress()+pp.Literal('vlan').suppress()+Space+VlanListe+pp.LineEnd().suppress())).setResultsName('vlan')
	Name=(pp.Combine(Space+pp.Literal('name').suppress()+Space+pp.OneOrMore(pp.CharsNotIn('\n')))).setResultsName('name')
	Mode=(pp.Combine(Space+pp.Literal('mode').suppress()+Space+pp.OneOrMore(pp.CharsNotIn('\n')))).setResultsName('mode')
	EntryVlan=Name|Mode
	BlocVlan=VlanLine+pp.OneOrMore(EntryVlan)
	
		
	for parsingVlanEntry in BlocVlan.scanString(String__.replace('\r','')):
		temp_list.append(parsingVlanEntry[0].asDict())
		
		
	for vlan__ in temp_list:
		try:
			name=vlan__['name']
		except KeyError:
			name=None
		
		try:
			mode=vlan__['mode']
		except KeyError:
			mode="CLASSICAL"
		
		vlan_liste=vlan__['vlan']
		
		if re.search('-|,',vlan_liste):
			for vlan____ in liste_vlans(vlan_liste).explode():
				Resultat[vlan____]={'mode': mode , 'name': name}
		else:
			Resultat[vlan_liste]={'mode': mode , 'name': name}

	return Resultat
	
	
def ParseIntCounterError(File__):
	Space=pp.Suppress(pp.OneOrMore(pp.White(' ')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch') | pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ]) | pp.Literal('Loopback') | pp.Literal('Vlan') | pp.Literal('Tunnel') |pp.Literal('Null') |pp.Literal('mgmt')) + pp.Word(pp.nums+('\/.')) )
	Error=pp.Word(pp.alphas+'-_')
	Errors=pp.Suppress(pp.Literal('Port'))+pp.OneOrMore(Space+pp.CharsNotIn(' \n'+pp.nums))
	Interligne=pp.Suppress(pp.Word('-',min=10))
	Value=pp.MatchFirst([pp.Word(pp.nums),pp.Literal('--')+pp.LineEnd().suppress(),pp.Literal('-- ').setParseAction(pp.replaceWith('--'))])
	Values=pp.Group(pp.OneOrMore(Value))
	Entries=pp.dictOf(Interface,Values)
	Bloc=pp.Group(pp.Optional(Interligne)+Errors+pp.Optional(Interligne)+Entries)
	Blocs=pp.OneOrMore(Bloc)
	All=pp.Optional(Show)+Blocs
	
	
	
	resultat_list=All.parseFile(File__).asList()
	
	indice={}
	resultat={}
	for bloc in resultat_list:
		i=0
		for info in bloc:
			if isinstance(info,list):
				interface_cur=info[0]
				if interface_cur not in resultat.keys():
					resultat[interface_cur]={}
					
				other_i=0
				for valeur in info[1]:
					try:
						resultat[interface_cur][indice[other_i]]=valeur
						other_i+=1
					except IndexError as e:
						print(e)
						pdb.set_trace()
					except KeyError as e:
						print(e)
						pdb.set_trace()
			else:
				try:
					indice[i]=info
					i+=1
				except IndexError as e:
					pdb.set_trace()
					print(e)
					
	
	
	return resultat
	
def ParseIntCounterErrorStr(Str__):
	Space=pp.Suppress(pp.OneOrMore(pp.White(' ')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch') | pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ]) | pp.Literal('Loopback') | pp.Literal('Vlan') | pp.Literal('Tunnel') |pp.Literal('Null')  |pp.Literal('mgmt') ) + pp.Word(pp.nums+('\/.')) )
	Error=pp.Word(pp.alphas+'-_')
	Errors=pp.Suppress(pp.Literal('Port'))+pp.OneOrMore(Space+pp.CharsNotIn(' \n'+pp.nums))
	Interligne=pp.Suppress(pp.Word('-',min=10))
	Value=pp.MatchFirst([pp.Word(pp.nums),pp.Literal('-- ').setParseAction(pp.replaceWith('--')),pp.Literal('--')])
	Values=pp.Group(pp.OneOrMore(Value))+pp.LineEnd().suppress()
	Entries=pp.dictOf(Interface,Values)
	Bloc=pp.Group(pp.Optional(Interligne)+Errors+pp.Optional(Interligne)+Entries)
	Blocs=pp.OneOrMore(Bloc)
	All=pp.Optional(Show)+Blocs
	
	
	
	resultat_list=All.parseString(Str__).asList()
	
	#pdb.set_trace()
	
	indice={}
	resultat={}
	for bloc in resultat_list:
		i=0
		for info in bloc:
			if isinstance(info,list):
				interface_cur=info[0]
				if interface_cur not in resultat.keys():
					resultat[interface_cur]={}
					
				other_i=0
				for valeur in info[1]:
					try:
						resultat[interface_cur][indice[other_i]]=valeur
						other_i+=1
					except IndexError as e:
						print(e)
						pdb.set_trace()
					except KeyError as e:
						print(e)
						pdb.set_trace()
			else:
				try:
					indice[i]=info
					i+=1
				except IndexError as e:
					print(e)
					pdb.set_trace()
	
	
	return resultat
	
def ParseVlanRunFile(File__):
	
	Resultat={}
	
	temp_list=[]
	
	Space=pp.Suppress(pp.OneOrMore(pp.White(' ')))
	VlanListe=pp.Word(pp.nums+',-')
	VlanLine=(pp.Combine(pp.LineStart().suppress()+pp.Literal('vlan').suppress()+Space+VlanListe+pp.LineEnd().suppress())).setResultsName('vlan')
	Name=(pp.Combine(Space+pp.Literal('name').suppress()+Space+pp.OneOrMore(pp.CharsNotIn('\n')))).setResultsName('name')
	Mode=(pp.Combine(Space+pp.Literal('mode').suppress()+Space+pp.OneOrMore(pp.CharsNotIn('\n')))).setResultsName('mode')
	EntryVlan=Name|Mode
	BlocVlan=VlanLine+pp.OneOrMore(EntryVlan)
	
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingVlanEntry in BlocVlan.scanString(file_str):
			temp_list.append(parsingVlanEntry[0].asDict())
			
		#print(temp_list)
		
			
		for vlan__ in temp_list:
			try:
				name=vlan__['name']
			except KeyError:
				name=None
			
			try:
				mode=vlan__['mode']
			except KeyError:
				mode="CLASSICAL"
			
			vlan_liste=vlan__['vlan']
			
			if re.search('-|,',vlan_liste):
				for vlan____ in liste_vlans(vlan_liste).explode():
					Resultat[vlan____]={'mode': mode , 'name': name}
			else:
				Resultat[vlan_liste]={'mode': mode , 'name': name}

	return Resultat

def ParseRunInterfaceFile(File__):
	Resultat={}
	
	Space=pp.OneOrMore(pp.White(' '))
	Interface=pp.Combine(pp.LineStart().suppress()+pp.Literal('interface')+Space+pp.OneOrMore(pp.CharsNotIn('\n ')))
	EntryInterface=pp.Combine(Space+pp.OneOrMore(pp.CharsNotIn('\n')))
	EntriesInterface=pp.Group(pp.OneOrMore(EntryInterface))
	BlocsInterface=pp.Group(Interface+pp.Optional(EntriesInterface,default=None))
	
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingEntry in BlocsInterface.scanString(file_str):
			try:
				if parsingEntry[0].asList()[0][1]:
					Resultat[ parsingEntry[0].asList()[0][0].replace('\r','')]=parsingEntry[0].asList()[0][1]
				else:
					Resultat[ parsingEntry[0].asList()[0][0].replace('\r','')]=parsingEntry[0].asList()[0][1]
			except KeyError as E:
				print(E)
				raise(E)

	return Resultat
	
def ParseRunInterfaceDeeperFile(File__):
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
	
	Resultat=BlocsInterface.parseFile(File__,parseAll=True)

	return Resultat
	
def ParseRunAccessList(FileOrStr,mode='file'):
	Resultat=[]
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	ipAddress2=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	NumStandard=pp.Word(pp.nums).addCondition(lambda tokens:(int(tokens[0]) <=99 and int(tokens[0]) >= 1 )  or (  int(tokens[0]) <=1999 and int(tokens[0]) >= 1300    ) )
	NumExtended=pp.Word(pp.nums).addCondition(lambda tokens:(int(tokens[0]) <=199 and int(tokens[0]) >= 100 )  or (  int(tokens[0]) <=2699 and int(tokens[0]) >= 2000    ) )

	action=pp.Literal('permit')|pp.Literal('deny')|pp.Literal('remark')
	protocol=pp.Literal('ip')
	host=pp.Group( (pp.Literal('host')+ipAddress).setParseAction(lambda t : [ t[1],t[0].replace('host','0.0.0.0') ] ) )
	Any=pp.Group( pp.Literal('any').setParseAction(lambda t : ['0.0.0.0','255.255.255.255']) )
	network=pp.Group(ipAddress*2)
	oneIP=pp.Group(ipAddress2.setParseAction(lambda t : [ t[0],'0.0.0.0' ] ))
	SrcOrDst=pp.MatchFirst([Any,network,host,oneIP])
	Log=pp.Suppress(pp.MatchFirst([pp.Literal('log-input'),pp.Literal('log')]))

	aceNumStandard=pp.Literal('access-list')+NumStandard+action+SrcOrDst+pp.Optional(Log)
	aceNumExtended=pp.Literal('access-list')+NumExtended+action+protocol+SrcOrDst+SrcOrDst+pp.Optional(Log)
	aclNumRemark=pp.Literal('access-list')+pp.Word(pp.nums)+pp.Literal('remark')+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))
	
	ace=pp.Group(aceNumStandard|aceNumExtended|aclNumRemark)
	
	Space=pp.Suppress(pp.OneOrMore(pp.White(' ')))
	Exclamations=pp.Suppress(pp.OneOrMore(pp.Literal('!')))

	HeadToIgnore=pp.SkipTo(ace).suppress()
	Acls=pp.OneOrMore(ace)
	
	BlocsAcl=HeadToIgnore+Acls
	
	if mode=='file':
		Resultat=BlocsAcl.parseFile(FileOrStr).asList()
	elif mode =='str':
		Resultat=BlocsAcl.parseString(FileOrStr).asList()
		
	if Resultat:
		
		Resultat_Dict={}
		for entry in Resultat:
			if entry[1] not in Resultat_Dict:
				Resultat_Dict[entry[1]]=[entry]
			else:
				Resultat_Dict[entry[1]].append(entry)
		return Resultat_Dict
	else:
		return {}


	
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
	
def ParseMacCiscoFile(File__):
	Resultat=[]
	End=pp.stringEnd|pp.LineEnd().suppress()|pp.Literal(' ').suppress()|pp.Literal('\n').suppress()|pp.Literal('\r').suppress()|pp.Literal('\r\n').suppress()
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	ID=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=65535 and int(tokens[0]) >= 0 )
	PortFP=pp.Combine(ID+((pp.Literal('.')+ID)*2))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	prompt=pp.Suppress(pp.OneOrMore(pp.Word(pp.alphanums+'-_'))+pp.Literal('#'))
	ShowAnd=pp.Suppress (pp.nestedExpr(opener='sh',closer='--\n') )
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='Legend:',closer='--\n')) 
	Legend_old=pp.Suppress (pp.nestedExpr(opener='Vlan',closer='--\n') )
	FirstLineCisco=pp.Suppress(pp.Literal('VLAN')+pp.ZeroOrMore(pp.Word(pp.printables)))
	FirstLineNexus=pp.Suppress(pp.Literal('vlan')+pp.Literal('mac')+pp.Literal('address')+pp.ZeroOrMore(pp.Word(pp.printables)))
	FirstLine=FirstLineCisco|FirstLineNexus
	Limite=pp.Suppress(pp.Literal('------')+pp.OneOrMore(pp.Word('-+'))+pp.Literal('\n'))
	Ports=pp.Suppress( (pp.CaselessLiteral('static')|pp.CaselessLiteral('dynamic')|pp.CaselessLiteral('igmp') ) + (pp.Word(pp.nums)|pp.Literal('-')|pp.Literal('~~~'))+pp.Optional(2*pp.Literal('F')))+(pp.OneOrMore(Interface|PortFP))
	hexint = pp.Word(pp.hexnums,exact=4)
	macAddress = pp.Combine(hexint + ('.'+hexint)*2)
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 1 ))
	Entry_CPU=pp.Suppress(pp.Literal('All')+macAddress+pp.Literal('STATIC')+pp.Literal('CPU'))
	EntryNexus=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+Ports)
	EntryCisco=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +(pp.Literal('Yes')|pp.Literal('No')).suppress()+(pp.Literal('-')|pp.Word(pp.nums)).suppress()+pp.OneOrMore(pp.delimitedList(Interface,delim=',')))
	EntryCiscoOld=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() + ( (pp.Literal('ip')+pp.Optional(',ipx')+pp.Optional(',assigned')+pp.Optional(',other') ) |pp.Literal('other')|pp.Literal('assigned')|pp.Literal('system')).suppress()+Interface)
	EntryCiscoOther=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +Interface)
	EmptyPort=pp.Group(pp.Suppress(pp.ZeroOrMore((pp.Literal('*')| pp.Literal('-') | pp.Literal('+'))))+Vlan+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +(pp.Literal('Yes')|pp.Literal('No')).suppress()+(pp.Literal('-')|pp.Word(pp.nums)).setParseAction(pp.replaceWith('None')))
	SpecialEntry=pp.Group(pp.Literal('*  ---').setParseAction(pp.replaceWith('None'))+macAddress+(pp.CaselessLiteral('dynamic') |pp.CaselessLiteral('static')).suppress() +(pp.Literal('Yes')|pp.Literal('No')).suppress()+(pp.Literal('-')|pp.Word(pp.nums)).suppress()+pp.OneOrMore(pp.delimitedList(Interface,delim=',')))
	L3Entry=pp.Suppress(Interface+macAddress+(pp.Keyword('dynamic') |pp.Keyword('static')).suppress() + ( (pp.Literal('ip')+pp.Optional(',ipx')+pp.Optional(',assigned')+pp.Optional(',other') ) |pp.Literal('other')|pp.Literal('assigned')|pp.Literal('system')).suppress()+pp.OneOrMore(pp.delimitedList(Interface,delim=',')))
	Debut=pp.MatchFirst([ShowAnd+Legend_old,Show+Legend])
	Line=Debut|FirstLine|Limite|EntryNexus|EntryCisco|EntryCiscoOld|Entry_CPU|EmptyPort|SpecialEntry|L3Entry|prompt
	Lines=pp.OneOrMore(Line)
	
	Entry=EntryNexus|EntryCisco|EntryCiscoOld|Entry_CPU|EmptyPort|EntryCiscoOther|SpecialEntry|L3Entry
	
	#Resultat=Lines.parseFile(File__)
	
	
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingEntry in Entry.scanString(file_str):
			temp_list=parsingEntry[0].asList()
			try:
				if temp_list[0]:
					Resultat.append(temp_list[0])
					#pdb.set_trace()
			except IndexError:
				pass
				
	#pdb.set_trace()
	
	return Resultat
	
def ParseSwitchPort(File__):

	resultat=None
	hostname=pp.Word(pp.alphanums+'-_')+pp.Literal('#')
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	DefaultMode=pp.Suppress(pp.Literal('Default switchport mode:') +pp.OneOrMore(pp.CharsNotIn('\n')))
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 0 ))
	InterfaceBiz=pp.Suppress(pp.Literal("vdc")+pp.Word(pp.nums)+pp.Literal("vlan")+pp.Word(pp.nums)+pp.Literal('Name:'))
	Name=pp.MatchFirst([InterfaceBiz,pp.Suppress(pp.Literal('Name:'))])
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ])  ) + pp.Word(pp.nums+('\/.')) )
	LigneInterface=(Name+pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(lambda tokens: str(tokens[0]).strip())
	Mode=pp.Literal('trunk')|pp.MatchFirst([pp.Literal('static access'),pp.Literal('access')])|pp.Literal('dynamic auto')|pp.Literal('dynamic desirable')|pp.Literal('down')|pp.Literal('unassigned')|pp.Literal('fex-fabric')|pp.Literal('fex-fabric')|pp.CaselessLiteral('FabricPath') |pp.Combine((pp.CaselessLiteral('private-vlan')+pp.OneOrMore(pp.CharsNotIn('\n'))))
	Comp=pp.Suppress( pp.MatchFirst( [pp.Literal('((')+pp.OneOrMore(pp.Word(pp.alphanums+'-_/:'))+pp.Literal('))'), pp.Literal('(')+pp.OneOrMore(pp.Word(pp.alphanums+'-_/:'))+pp.Literal(')'),pp.Literal('(')+pp.OneOrMore(pp.CharsNotIn('\n'))]))
	Switchport=pp.Literal('Switchport:').suppress()+pp.Literal('Enabled')|pp.Literal('Not enabled')
	SwitchPortMonitor=pp.Suppress(pp.Literal('Switchport Monitor:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	SwitchPortIsolated=pp.Suppress(pp.Literal('Switchport Isolated :')+pp.OneOrMore(pp.CharsNotIn('\n')))
	AdminEncap=pp.Suppress(pp.Literal('Administrative Trunking Encapsulation:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpeEncap=pp.Suppress(pp.Literal('Operational Trunking Encapsulation:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	AdminMode=pp.Suppress(pp.Literal('Administrative Mode:')+Mode)
	TaggingNative=pp.Suppress(pp.Literal('Administrative Native VLAN tagging:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Opedot1qEther=pp.Suppress(pp.Literal('Operational Dot1q')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpeTaggingNative=pp.Suppress(pp.Literal('Operational Native VLAN tagging:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpeMode=pp.Literal('Operational Mode:').suppress()+Mode+pp.Suppress(pp.Optional(Comp))
	Nego=pp.Suppress(pp.Literal('Negotiation of Trunking:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	NativeVlanAccess=pp.Suppress(pp.Literal('Access Mode VLAN:'))+((Vlan+pp.Optional(Comp))|pp.Literal('unassigned'))
	NativeVlanTrunk=pp.Suppress(pp.Literal('Trunking Native Mode VLAN:'))+Vlan+pp.Suppress(pp.Optional(Comp))
	ListeVlans=pp.Combine(pp.CaselessLiteral('none')|pp.CaselessLiteral('ALL')|(Vlan+pp.ZeroOrMore( (pp.Word('-,\n').setParseAction(lambda t : t[0].replace('\n',''))+pp.Optional(pp.White().suppress())+Vlan))))
	VlansTrunk=pp.Suppress(pp.Literal('Trunking VLANs Enabled:')|pp.Literal('Trunking VLANs Allowed:'))+ListeVlans
	Voice=pp.Suppress(pp.Literal('Voice VLAN:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Private=pp.Suppress(pp.Literal('Administrative')+pp.Literal('private-vlan')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpePrivate=pp.Literal('Operational private-vlan:')+Vlan+pp.OneOrMore(pp.CharsNotIn('\n'))
	Pruning=pp.Suppress(pp.Literal('Pruning')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Unknown=pp.Suppress(pp.Literal('Unknown')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Trust=pp.Suppress(pp.Literal('Extended Trust State')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Protected=pp.Suppress(pp.Literal('Protected')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Capture=pp.Suppress(pp.Literal('Capture')+pp.OneOrMore(pp.CharsNotIn('\n')))
	AppTrust=pp.Suppress(pp.Literal('Appliance')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OperationalPrivate=pp.Suppress(pp.MatchFirst([OpePrivate,pp.Literal('Operational private-vlan')+pp.OneOrMore(pp.CharsNotIn('\n'))]))
	FP=pp.Suppress(pp.Literal('FabricPath')+pp.OneOrMore(pp.CharsNotIn('\n')))
	InfoBlock__=Switchport|SwitchPortMonitor|SwitchPortIsolated|AdminMode|AdminEncap|OpeMode|TaggingNative|OpeTaggingNative|Opedot1qEther|OpeEncap|Nego|NativeVlanAccess|AppTrust|NativeVlanTrunk|VlansTrunk|Voice|Private|Pruning|Unknown|Trust|Capture|Protected|OperationalPrivate|FP
	InfoBlock=pp.MatchFirst([InfoBlock__,pp.Suppress(pp.Literal('Switchport ')+pp.OneOrMore(pp.CharsNotIn('\n'))),pp.Suppress(pp.Literal('Virtual Ethernet')+pp.OneOrMore(pp.CharsNotIn('\n')))])
	InfoBlocks=pp.OneOrMore(InfoBlock)
	
	Entry=pp.Optional(Show)+pp.Optional(DefaultMode)+pp.dictOf(LigneInterface, InfoBlocks )+pp.Suppress(pp.Optional(hostname))
	try:
		resultat=Entry.parseFile(File__,parseAll=True).asDict()
	except pp.ParseException as e:
		print(e)
		print('File:'+File__)
		raise(e)
	
	return resultat
	
def ParseSwitchPortString(Str__):

	resultat=None
	hostname=pp.Word(pp.alphanums+'-_')+pp.Literal('#')
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 0 ))
	InterfaceBiz=pp.Suppress(pp.Literal("vdc")+pp.Word(pp.nums)+pp.Literal("vlan")+pp.Word(pp.nums)+pp.Literal('Name:'))
	Name=pp.MatchFirst([InterfaceBiz,pp.Suppress(pp.Literal('Name:'))])
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ])  ) + pp.Word(pp.nums+('\/.')) )
	LigneInterface=(Name+pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(lambda tokens: str(tokens[0]).strip())
	Mode=pp.Literal('trunk')|pp.MatchFirst([pp.Literal('static access'),pp.Literal('access')])|pp.Literal('dynamic auto')|pp.Literal('dynamic desirable')|pp.Literal('down')|pp.Literal('unassigned')|pp.Literal('fex-fabric')|pp.Literal('fex-fabric')|pp.CaselessLiteral('FabricPath') |pp.Combine((pp.Literal('private-vlan')+pp.OneOrMore(pp.CharsNotIn('\n'))))
	Comp=pp.Suppress( pp.MatchFirst( [pp.Literal('((')+pp.OneOrMore(pp.Word(pp.alphanums+'-_/:'))+pp.Literal('))'), pp.Literal('(')+pp.OneOrMore(pp.Word(pp.alphanums+'-_/:'))+pp.Literal(')'),pp.Literal('(')+pp.OneOrMore(pp.CharsNotIn('\n'))]))
	Switchport=pp.Literal('Switchport:').suppress()+pp.Literal('Enabled')|pp.Literal('Not enabled')
	SwitchPortMonitor=pp.Suppress(pp.Literal('Switchport Monitor:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	SwitchPortIsolated=pp.Suppress(pp.Literal('Switchport Isolated :')+pp.OneOrMore(pp.CharsNotIn('\n')))
	AdminEncap=pp.Suppress(pp.Literal('Administrative Trunking Encapsulation:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpeEncap=pp.Suppress(pp.Literal('Operational Trunking Encapsulation:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	AdminMode=pp.Suppress(pp.Literal('Administrative Mode:')+Mode)
	TaggingNative=pp.Suppress(pp.Literal('Administrative Native VLAN tagging:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Opedot1qEther=pp.Suppress(pp.Literal('Operational Dot1q')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpeTaggingNative=pp.Suppress(pp.Literal('Operational Native VLAN tagging:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpeMode=pp.Literal('Operational Mode:').suppress()+Mode+pp.Suppress(pp.Optional(Comp))
	Nego=pp.Suppress(pp.Literal('Negotiation of Trunking:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	NativeVlanAccess=pp.Suppress(pp.Literal('Access Mode VLAN:'))+((Vlan+pp.Optional(Comp))|pp.Literal('unassigned'))
	NativeVlanTrunk=pp.Suppress(pp.Literal('Trunking Native Mode VLAN:'))+Vlan+pp.Suppress(pp.Optional(Comp))
	ListeVlans=pp.Combine(pp.CaselessLiteral('none')|pp.CaselessLiteral('ALL')|(Vlan+pp.ZeroOrMore( (pp.Word('-,\n').setParseAction(lambda t : t[0].replace('\n',''))+pp.Optional(pp.White().suppress())+Vlan))))
	VlansTrunk=pp.Suppress(pp.Literal('Trunking VLANs Enabled:')|pp.Literal('Trunking VLANs Allowed:'))+ListeVlans
	Voice=pp.Suppress(pp.Literal('Voice VLAN:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Private=pp.Suppress(pp.Literal('Administrative')+pp.Literal('private-vlan')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OpePrivate=pp.Literal('Operational private-vlan:')+Vlan+pp.OneOrMore(pp.CharsNotIn('\n'))
	Pruning=pp.Suppress(pp.Literal('Pruning')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Unknown=pp.Suppress(pp.Literal('Unknown')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Trust=pp.Suppress(pp.Literal('Extended Trust State')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Protected=pp.Suppress(pp.Literal('Protected')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Capture=pp.Suppress(pp.Literal('Capture')+pp.OneOrMore(pp.CharsNotIn('\n')))
	AppTrust=pp.Suppress(pp.Literal('Appliance')+pp.OneOrMore(pp.CharsNotIn('\n')))
	OperationalPrivate=pp.Suppress(pp.MatchFirst([OpePrivate,pp.Literal('Operational private-vlan')+pp.OneOrMore(pp.CharsNotIn('\n'))]))
	FP=pp.Suppress(pp.Literal('FabricPath')+pp.OneOrMore(pp.CharsNotIn('\n')))
	InfoBlock__=Switchport|SwitchPortMonitor|SwitchPortIsolated|AdminMode|AdminEncap|OpeMode|TaggingNative|OpeTaggingNative|Opedot1qEther|OpeEncap|Nego|NativeVlanAccess|AppTrust|NativeVlanTrunk|VlansTrunk|Voice|Private|Pruning|Unknown|Trust|Capture|Protected|OperationalPrivate|FP
	InfoBlock=pp.MatchFirst([InfoBlock__,pp.Suppress(pp.Literal('Switchport ')+pp.OneOrMore(pp.CharsNotIn('\n'))),pp.Suppress(pp.Literal('Virtual Ethernet')+pp.OneOrMore(pp.CharsNotIn('\n')))])
	InfoBlocks=pp.OneOrMore(InfoBlock)
	
	Entry=pp.Optional(Show)+pp.dictOf(LigneInterface, InfoBlocks )+pp.Suppress(pp.Optional(hostname))
	try:
		resultat=Entry.parseString(Str__,parseAll=True).asDict()
	except pp.ParseException as e:
		print(e)
		print('Str:'+Str__)
		raise(e)
	
	return resultat
	
def ParseIpRouteCisco(File__,modestr=False):
	Resultat=None
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch') | pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ]) | pp.Literal('Loopback') | pp.Literal('Vlan') | pp.Literal('Tunnel') |pp.Literal('Null') ) + pp.Word(pp.nums+('\/.')) )
	VRF=pp.Keyword('Routing').suppress()+pp.Keyword('Table:').suppress()+pp.Word(pp.alphanums+"-_")
	Legend1= pp.nestedExpr(opener='Codes:',closer='downloaded static route')
	Legend2= pp.nestedExpr(opener='Codes:',closer='next hop override')
	Legend3= pp.nestedExpr(opener='Codes:',closer='overrides from PfR')
	Legend0= pp.nestedExpr(opener='Codes:',closer='override') 
	Legend=pp.MatchFirst([Legend3,Legend2,Legend1,Legend0]).suppress()
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Optional(pp.Literal('/')+slash))
	Space_=pp.Word(' ',min=3,max=6)
	Default=(pp.Group(pp.Literal('Gateway of last resort is').setParseAction(pp.replaceWith('DEFAULT'))+ipAddress+pp.OneOrMore(pp.CharsNotIn('\n')).suppress()))|pp.Literal('Gateway of last resort is not set').setParseAction(pp.replaceWith(['DEFAULT','None']))
	Connected=pp.Literal('C')
	Local=pp.Literal('L')
	Static=pp.Literal('S')
	Rip=pp.Literal('R')
	Bgp=pp.MatchFirst([pp.Literal('B*'),pp.Literal('B')])
	EIGRP=pp.MatchFirst([pp.Literal('D EX'),pp.Literal('D')])
	Ospf=pp.MatchFirst([pp.Literal('O E1'),pp.Literal('O E2'),pp.Literal('O IA'),pp.Literal('O*E1'),pp.Literal('O*E2'),pp.Literal('O*IA'),pp.Literal('O')])
	Protocol=(Connected|Static|Rip|Bgp|Ospf|EIGRP)+pp.Optional(pp.Word('*+',exact=1)).suppress()
	cost=pp.Suppress(pp.Combine(pp.Literal('[')+pp.Word(pp.nums)+pp.Literal('/')+pp.Word(pp.nums)+pp.Literal(']')))
	heure=pp.Word(pp.nums,min=1,max=2)+(':'+pp.Word(pp.nums,min=1,max=2) ) *2
	VRFNextHop=pp.Suppress(pp.Literal('(')+pp.Word(pp.alphanums+"-_")+pp.Literal(')'))
	jma=pp.Word(pp.nums)+pp.Word('ywmdh',exact=1)
	duree=(jma*2)|(jma*3)
	time=duree|heure
	Virgule=pp.Suppress(pp.Literal(','))
	NextHop=cost+pp.Suppress(pp.Literal('via'))+ipAddress+pp.Optional(VRFNextHop)+pp.Suppress(pp.Optional(pp.Literal(',')+time))+pp.Suppress(pp.Optional(pp.Literal(',')+Interface))
	Entry=pp.Group(Protocol+Prefix+pp.Group(pp.OneOrMore(NextHop)))
	EntryConnected=pp.Group((Connected|Local|Static)+Prefix+pp.Literal('is directly connected,').suppress()+Interface)
	EntryConnectedBGP=Bgp+Prefix+pp.Literal('is directly connected').suppress()+pp.Optional(VRFNextHop)+Virgule+pp.Suppress(time)+Virgule+Interface
	EntryWoSlash=pp.Group(Protocol+ipAddress+pp.Group(pp.OneOrMore(NextHop)))
	EntryConnectedBGPWoSlash=pp.Group(Bgp+ipAddress+pp.Literal('is directly connected').suppress()+pp.Optional(VRFNextHop)+Virgule+pp.Suppress(time)+Virgule+Interface)
	EntrySummary=pp.Group(Protocol+Prefix+pp.Suppress(pp.Literal('is a summary'))+pp.Suppress(pp.Optional(pp.Literal(',')+time))+Virgule+Interface)
	EntryConnectedWoSlash=pp.Group((Connected|Local|Static)+ipAddress+pp.Literal('is directly connected,').suppress()+Interface)
	EntriesSubnetted=pp.Group(pp.Group(ipAddress+pp.Literal('/')+slash+pp.Suppress(pp.Literal('is subnetted,')+pp.OneOrMore(pp.CharsNotIn('\n'))))+pp.Group(pp.OneOrMore(EntryWoSlash|EntryConnectedWoSlash|EntryConnectedBGPWoSlash))).setParseAction(parseEntriesSubnetted)
	InfoSubnet=pp.Suppress(Prefix+pp.Literal('is variably subnetted,')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Entries=pp.OneOrMore(EntriesSubnetted|Default|Entry|InfoSubnet|EntryConnected|EntryConnectedBGP|EntrySummary)
	BlocVrf=pp.dictOf(pp.Optional(Show)+pp.Optional(VRF,default="GRT")+Legend,pp.Group(Entries))+pp.Optional(hostname)
	
	if not modestr:
		Resultat=BlocVrf.parseFile(File__,parseAll=True)
	else:
		Resultat=BlocVrf.parseString(File__,parseAll=True)
	
	return Resultat

def reOrderNH(string,location,token):
	Resultat=[]
	
	
	Prefix=token[0][0]
	Liste_NH=token[0][1]
	
	#print("PREFIX:"+str(Prefix))
	#print("NHs:"+str(Liste_NH))
	
	DictNH={}
	
	try:
	
		for NH in Liste_NH:
		
			#pdb.set_trace()
			
			Gateway=NH[0]
			Protocol=NH[1]
		
			try:
				DictNH[Protocol].append(Gateway)
			except KeyError:
				DictNH[Protocol]=[Gateway]
	except:
		pdb.set_trace()
		
	for Proto in DictNH.keys():
		Resultat.append([Proto,Prefix,DictNH[Proto]])
		
	#print("RESULTAT:"+str(Resultat))
		
	#pdb.set_trace()
		
	return Resultat
				
def parseEntriesSubnetted(string,location,token):
	Resultat=[]
	
	#pdb.set_trace()
	try:
		slash=token[0][0][2]
		ListeEntry=token[0][1].asList()
	except KeyError:
		pdb.set_trace()
	
	for Entry in ListeEntry:
		Resultat.append([Entry[0],Entry[1]+"/"+slash,Entry[2]])
		#print(Entry[0]+" "+Entry[1]+"/"+slash+" "+str(Entry[2]))
	
	return Resultat		

def ParseIpRouteNexus(File__,modestr=False):
	Resultat=None
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch') | pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('Ethernet') ]) | pp.Literal('Loopback') | pp.Literal('Vlan') | pp.Literal('Null') | pp.Literal('mgmt')  ) + pp.Word(pp.nums+('\/.')) )
	VRF=pp.Optional('No').suppress()+pp.Literal('IP Route Table for VRF \"').suppress()+pp.Word(pp.alphanums+"-_")+pp.Literal('\"').suppress()
	Legend=pp.Suppress (pp.nestedExpr(opener='\'*\' denotes',closer='VRF <string>') )
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Optional(pp.Literal('/')+slash))
	Via=pp.Suppress(pp.MatchFirst([pp.Literal('*via'),pp.Literal('via')]))
	Tag=pp.Suppress(pp.Literal('tag')+pp.Word(pp.nums))
	Virgule=pp.Suppress(pp.Literal(','))
	Connected=pp.Literal('direct').setParseAction(pp.replaceWith('C'))
	Local=pp.Literal('local').setParseAction(pp.replaceWith('L'))
	Hsrp=pp.Literal('hsrp')
	Vrrp=pp.Literal('vrrp_engine')
	Static=pp.Literal('static').setParseAction(pp.replaceWith('S'))
	Rip=(pp.Keyword('rip')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')+pp.Literal('rip')).setParseAction(pp.replaceWith('R'))
	Bgp=(pp.Keyword('bgp')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')+(pp.Literal('internal')|pp.Literal('external'))).setParseAction(pp.replaceWith('B'))
	EIGRP=(pp.Keyword('eigrp')+VRF+pp.Literal(',')).setParseAction(pp.replaceWith('D'))
	Ospf_E1=(pp.Keyword('ospf')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')+pp.Literal('type-1')).setParseAction(pp.replaceWith('O E1'))
	Ospf_E2=(pp.Keyword('ospf')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')+pp.Literal('type-2')).setParseAction(pp.replaceWith('O E2'))
	Ospf_Intra=(pp.Keyword('ospf')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')+pp.Literal('intra')).setParseAction(pp.replaceWith('O IA'))
	Ospf_Inter=(pp.Keyword('ospf')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')+pp.Literal('inter')).setParseAction(pp.replaceWith('O'))
	Ospf_only=(pp.Keyword('ospf')+pp.Word(pp.alphanums+"-_")+pp.Literal(',')).setParseAction(pp.replaceWith('O'))
	Ospf=pp.MatchFirst([Ospf_E1|Ospf_E2|Ospf_Intra|Ospf_Inter,Ospf_only])
	Discard=pp.Literal('discard')
	Protocol=(Connected|Static|Local|Hsrp|Rip|Bgp|Ospf|EIGRP|Vrrp)
	cost=pp.Suppress(pp.Combine(pp.Literal('[')+pp.Word(pp.nums)+pp.Literal('/')+pp.Word(pp.nums)+pp.Literal(']')))
	heure=pp.Word(pp.nums,min=1,max=2)+(':'+pp.Word(pp.nums,min=1,max=2) ) *2
	jma=pp.Word(pp.nums)+pp.Word('ywmdh',exact=1)
	duree=(jma*2)|(jma*3)
	time=pp.Suppress(duree|heure|pp.Word(pp.nums+'.'))
	NextHopDiscard=pp.Group(Via+pp.Combine(pp.Literal('Null')+pp.Word(pp.nums+('\/.')))+Virgule+(pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(pp.replaceWith('discard')))
	NextHopStatic=pp.Group(Via+Prefix+Virgule+Interface+Virgule+cost+Virgule+time+Protocol+pp.Optional(Tag))
	NextHopConnected=pp.Group(Via+Interface+Virgule+cost+Virgule+time+Virgule+Protocol+pp.Optional(Tag)+pp.Optional(',').suppress()+pp.Optional(Discard))
	NextHopDynamic=pp.Group(Via+Prefix+Virgule+pp.Optional(Interface+pp.Literal(',')).suppress()+cost+Virgule+time+Virgule+Protocol+pp.Optional(',').suppress()+pp.Optional(Tag)+pp.Optional(',').suppress()+pp.Optional(Discard))
	NextHop=pp.MatchFirst([NextHopStatic,NextHopDynamic,NextHopConnected,NextHopDiscard])
	#Entry=pp.Group(Prefix+Virgule+pp.Suppress(pp.Literal('ubest/mbest')+pp.OneOrMore(pp.CharsNotIn('\n')))+pp.Group(pp.OneOrMore(NextHop)))
	Entry=pp.Group(Prefix+Virgule+pp.Suppress(pp.Literal('ubest/mbest')+pp.OneOrMore(pp.CharsNotIn('\n')))+pp.LineEnd().suppress()+pp.Group(pp.OneOrMore(NextHop))).setParseAction(reOrderNH)
	Entries=pp.ZeroOrMore(Entry)
	BlocVrf=pp.dictOf(pp.Optional(hostname)+Show+VRF+pp.Optional(Legend),pp.Optional(pp.Group(Entries),default=[]))+pp.Optional(hostname)
	
	if not modestr:
		Resultat=BlocVrf.parseFile(File__,parseAll=True)
	else:
		Resultat=BlocVrf.parseString(File__,parseAll=True)
	
	return Resultat	
	
def ParseIpRouteXR(File__,modestr=False):

	Resultat=None
	Day=pp.Literal('Mon')|pp.Literal('Tue')|pp.Literal('Wed')|pp.Literal('Thu')|pp.Literal('Fri')|pp.Literal('Sat')|pp.Literal('Sun')
	Month=pp.Literal('Jan')|pp.Literal('Feb')|pp.Literal('Mar')|pp.Literal('Apr')|pp.Literal('May')|pp.Literal('Jun')|pp.Literal('Jul')|pp.Literal('Aug')|pp.Literal('Sep')|pp.Literal('Oct')|pp.Literal('Nov')|pp.Literal('Dec')
	Date=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=31 and int(tokens[0]) >= 1 )
	Hour=pp.Word(pp.nums,exact=2)+(pp.Literal(':')+pp.Word(pp.nums,exact=2))*2+pp.Literal('.')+pp.Word(pp.nums)
	Timestamp=pp.Suppress(Day+Month+Date+Hour+pp.OneOrMore(pp.CharsNotIn('\n')))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Optional(pp.Literal('/')+slash))
	Via=pp.Suppress(pp.MatchFirst([pp.Literal('*via'),pp.Literal('via')]))
	Tag=pp.Suppress(pp.Literal('tag')+pp.Word(pp.nums))
	Virgule=pp.Suppress(pp.Literal(','))
	Hardware=((pp.Literal('MgmtEth')|pp.Literal('RSP')|pp.Literal('CPU')|pp.Literal('EINT'))+pp.Word(pp.nums,exact=1))|pp.Word(pp.nums,exact=1)
	Hardwares=pp.Combine(Hardware+pp.Optional(pp.OneOrMore(pp.Literal('/')+pp.OneOrMore(Hardware))))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n'))+Timestamp)
	Interface=pp.Combine((pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('Bundle-Ether')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch') | pp.Literal('Router')|pp.Literal('Stby-Switch')| pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('TenGigE'),pp.Literal('HundredGigE'),pp.Literal('Ethernet') ]) | pp.MatchFirst([pp.Literal('nV-Loopback'),pp.Literal('Loopback')]) | pp.Literal('Vlan')  | pp.Literal('Null')| pp.Literal('BVI')) + pp.Word(pp.nums+('\/.')) )
	Legend=pp.Suppress (pp.nestedExpr(opener='Codes:',closer='Backup path') )
	Default=(pp.Group(pp.Literal('Gateway of last resort is').setParseAction(pp.replaceWith('DEFAULT'))+ipAddress+pp.OneOrMore(pp.CharsNotIn('\n')).suppress()))|pp.Literal('Gateway of last resort is not set').setParseAction(pp.replaceWith(['DEFAULT','None']))
	VRF=pp.Literal('VRF: ').suppress()+pp.Word(pp.alphanums+"-_*")
	Connected=pp.Literal('C')
	Local=pp.Literal('L')
	Static=pp.Literal('S')
	Rip=pp.Literal('R')
	heure=pp.Word(pp.nums,min=1,max=2)+(':'+pp.Word(pp.nums,min=1,max=2) ) *2
	jma=pp.Word(pp.nums)+pp.Word('ywmdh',exact=1)
	duree=(jma*2)|(jma*3)
	time=pp.Suppress(duree|heure)
	Bgp=pp.MatchFirst([pp.Literal('B*'),pp.Literal('B')])
	EIGRP=pp.MatchFirst([pp.Literal('D EX'),pp.Literal('D')])
	Ospf=pp.MatchFirst([pp.Literal('O E1'),pp.Literal('O E2'),pp.Literal('O IA'),pp.Literal('O*E1'),pp.Literal('O*E2'),pp.Literal('O*IA'),pp.Literal('O')])
	Protocol=(Local|Connected|Static|Rip|Bgp|Ospf|EIGRP)+pp.Optional(pp.Word('*+',exact=1)).suppress()
	cost=pp.Suppress(pp.Combine(pp.Literal('[')+pp.Word(pp.nums)+pp.Literal('/')+pp.Word(pp.nums)+pp.Literal(']')))
	NextHopVRF=pp.Literal('(nexthop in vrf ')+pp.Word(pp.alphanums+"-_*")+pp.Literal(')')
	NextHop=cost+pp.Suppress(pp.Literal('via'))+ipAddress+pp.Suppress(pp.Optional(NextHopVRF))+pp.Suppress(pp.Literal(',')+time)+pp.Suppress(pp.Optional(Virgule+Interface))
	Entry=pp.Group(Protocol+Prefix+pp.Group(pp.OneOrMore(NextHop)+pp.Optional(Virgule+(Interface|Hardwares))))
	EntryConnected=pp.Group(Protocol+Prefix+pp.Group(pp.OneOrMore(pp.Literal('is directly connected,').suppress()+time+Virgule+(Interface|Hardwares)+pp.Suppress(pp.Optional(NextHopVRF)))))
	EntryConnectedVia=pp.Group(Protocol+Prefix+pp.Group(pp.OneOrMore(pp.Literal('is directly connected,').suppress()+time+Virgule+(Interface|Hardwares)+pp.Suppress(pp.Optional(NextHopVRF)))))
	NoRoute=pp.Suppress(pp.Literal('% No matching routes found'))
	Entries=pp.ZeroOrMore(Entry|EntryConnected|Default)
	BlocVrf=pp.dictOf(pp.Optional(Show)+pp.Optional(VRF,default="GRT")+(Legend|NoRoute),pp.Group(Entries))+pp.Optional(hostname)
	
	if not modestr:
		Resultat=BlocVrf.parseFile(File__,parseAll=True)
	else:
		Resultat=BlocVrf.parseString(File__,parseAll=True)
	
	return Resultat
	
def ParseBgpTableXR(File__):
	
	Resultat=None
	Day=pp.Literal('Mon')|pp.Literal('Tue')|pp.Literal('Wed')|pp.Literal('Thu')|pp.Literal('Fri')|pp.Literal('Sat')|pp.Literal('Sun')
	Month=pp.Literal('Jan')|pp.Literal('Feb')|pp.Literal('Mar')|pp.Literal('Apr')|pp.Literal('May')|pp.Literal('Jun')|pp.Literal('Jul')|pp.Literal('Aug')|pp.Literal('Sep')|pp.Literal('Oct')|pp.Literal('Nov')|pp.Literal('Dec')
	Date=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=31 and int(tokens[0]) >= 1 )
	Hour=pp.Word(pp.nums,exact=2)+(pp.Literal(':')+pp.Word(pp.nums,exact=2))*2+pp.Literal('.')+pp.Word(pp.nums)
	Timestamp=pp.Suppress(Day+Month+Date+Hour+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n'))+Timestamp)
	Virgule=pp.Suppress(pp.Literal(','))
	VRF__1=pp.Literal('BGP VRF ').suppress()+pp.Word(pp.alphanums+"-_*")+Virgule+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF__2=pp.Literal('VRF: ').suppress()+pp.OneOrMore(pp.CharsNotIn('\n'))+pp.Suppress(pp.Literal('--')+pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF=pp.MatchFirst([VRF__1,VRF__2])
	BGP_rd=pp.Suppress(pp.Literal('BGP Route Distinguisher:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='VRF ID:',closer='Weight Path') )
	RD=pp.Suppress(pp.Literal('Route Distinguisher:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Process=pp.Suppress(pp.Literal('Processed')+pp.OneOrMore(pp.CharsNotIn('\n')))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=pp.Suppress(pp.Word(pp.nums)+pp.OneOrMore(pp.CharsNotIn('\n')))
	NextHop=pp.Group(ipAddress+OtherAttributes)
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes)
	FirstInfo=Code+Prefix+NextHop
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(VRF,default="GRT")+pp.Optional(BGP_rd+Legend+RD),pp.Optional(pp.Group(Entries)+Process,default=None ))+pp.ZeroOrMore(hostname)
	Resultat=BlocVrf.parseFile(File__,parseAll=True)
	
	return Resultat
	
def ParseBgpTableXRStr(Str__):
	
	Resultat=None
	Day=pp.Literal('Mon')|pp.Literal('Tue')|pp.Literal('Wed')|pp.Literal('Thu')|pp.Literal('Fri')|pp.Literal('Sat')|pp.Literal('Sun')
	Month=pp.Literal('Jan')|pp.Literal('Feb')|pp.Literal('Mar')|pp.Literal('Apr')|pp.Literal('May')|pp.Literal('Jun')|pp.Literal('Jul')|pp.Literal('Aug')|pp.Literal('Sep')|pp.Literal('Oct')|pp.Literal('Nov')|pp.Literal('Dec')
	Date=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=31 and int(tokens[0]) >= 1 )
	Hour=pp.Word(pp.nums,exact=2)+(pp.Literal(':')+pp.Word(pp.nums,exact=2))*2+pp.Literal('.')+pp.Word(pp.nums)
	Timestamp=pp.Suppress(Day+Month+Date+Hour+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n'))+Timestamp)
	Virgule=pp.Suppress(pp.Literal(','))
	VRF__1=pp.Literal('BGP VRF ').suppress()+pp.Word(pp.alphanums+"-_*")+Virgule+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF__2=pp.Literal('VRF: ').suppress()+pp.OneOrMore(pp.CharsNotIn('\n'))+pp.Suppress(pp.Literal('--')+pp.OneOrMore(pp.CharsNotIn('\n')))
	VRF=pp.MatchFirst([VRF__1,VRF__2])
	BGP_rd=pp.Suppress(pp.Literal('BGP Route Distinguisher:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='VRF ID:',closer='Weight Path') )
	RD=pp.Suppress(pp.Literal('Route Distinguisher:')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Process=pp.Suppress(pp.Literal('Processed')+pp.OneOrMore(pp.CharsNotIn('\n')))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=pp.Suppress(pp.Word(pp.nums)+pp.OneOrMore(pp.CharsNotIn('\n')))
	NextHop=pp.Group(ipAddress+OtherAttributes)
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes)
	FirstInfo=Code+Prefix+NextHop
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(VRF,default="GRT")+pp.Optional(BGP_rd+Legend+RD),pp.Optional(pp.Group(Entries)+Process,default=None ))+pp.ZeroOrMore(hostname)
	Resultat=BlocVrf.parseString(Str__,parseAll=True)
	
	return Resultat
def ParseBgpTableIOS(File__):
	
	Resultat=None
	End=pp.Suppress(pp.LineEnd())
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='BGP table version',closer='Weight Path') )
	RD=pp.Suppress(pp.Literal('Route Distinguisher:')+pp.Word(pp.nums)+pp.Literal(':')+pp.Word(pp.nums))
	VRF=RD+pp.Suppress(pp.Literal('(default for vrf '))+pp.Word(pp.alphanums+"-_*")+pp.Suppress(pp.Literal(')'))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix__slash=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Prefix__wo__slash=pp.Combine(octet + ('.'+octet)*3).setParseAction(lambda s,l,t : t[0]+'/'+getDefaultMask(t[0]) )
	Prefix=pp.MatchFirst([Prefix__slash,Prefix__wo__slash])
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=pp.Suppress(pp.Word(pp.nums)+pp.White()+pp.OneOrMore(pp.CharsNotIn('\n')))
	NextHop=pp.Group(ipAddress+OtherAttributes)+End
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes+End)
	FirstInfo=Code+Prefix+NextHop
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(Legend+VRF,default="GRT"),pp.MatchFirst([pp.Group(Entries),hostname])+pp.Optional(pp.OneOrMore(hostname)))
	Resultat=BlocVrf.parseFile(File__,parseAll=True)
	
	return Resultat
	
def ParseBgpTableNxOS(File__):
	
	Resultat=None
	End=pp.Suppress(pp.LineEnd())
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_:/')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='BGP table version',closer='Weight Path') )
	VRF=pp.Suppress(pp.Literal('BGP routing table information for VRF'))+pp.Word(pp.alphanums+"-_*,").setParseAction(lambda t : t[0].replace(',',''))+pp.Suppress(pp.OneOrMore(pp.CharsNotIn('\n')))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	Prefix__slash=pp.Combine(ipAddress+pp.Literal('/')+slash)
	Prefix__wo__slash=pp.Combine(octet + ('.'+octet)*3).setParseAction(lambda s,l,t : t[0]+'/'+getDefaultMask(t[0]) )
	Prefix=pp.MatchFirst([Prefix__slash,Prefix__wo__slash])
	Status=pp.Word('sdh*irSN',exact=1)
	Best=pp.Literal('>')
	Origin=pp.Word('ie?|&r',exact=1)
	Code=pp.MatchFirst([pp.Combine(Status+Best+Origin),pp.Combine(Status+pp.Literal(' ')+Origin),pp.Combine(Status+Best),pp.Combine(Status)])
	OtherAttributes=pp.Suppress(pp.Word(pp.nums)+pp.White()+pp.OneOrMore(pp.CharsNotIn('\n')))
	NextHop=pp.Group(ipAddress+OtherAttributes)+End
	OtherNextHop=pp.Group(Code+ipAddress+OtherAttributes+End)
	FirstInfo=Code+Prefix+NextHop
	Entry=pp.Group(FirstInfo+pp.Optional(pp.Group(pp.OneOrMore(OtherNextHop)))).setParseAction(AddAttributesFirstRoute)
	Entries=pp.ZeroOrMore(pp.Group(Entry))
	BlocVrf=pp.dictOf(Show+pp.Optional(VRF+Legend,default="GRT"),pp.MatchFirst([pp.Group(Entries),hostname])+pp.Optional(pp.OneOrMore(hostname)))
	Resultat=BlocVrf.parseFile(File__,parseAll=True)
	
	return Resultat
	
def test(s,l,t):
	pdb.set_trace()
	return t[0]+'/'+getDefaultMask(t[0])
	
def ParseBgpTable(File__):
	resultat=None
	
	try:
		resultat = ParseBgpTableIOS(File__).asDict()
	except pp.ParseException as e1:
		try:
			resultat=ParseBgpTableXR(File__).asDict()
		except pp.ParseException as e2:
			try:
				resultat=ParseBgpTableNxOS(File__).asDict()
			except pp.ParseException as e3:
				print('Erreur de parsing\n')
				print('Fichier:'+File__)
				print(e1)
				print(e2)
				print(e3)
				
				
	return resultat
	
	
	
def ParseBgpTableString(String__):
				
	return String__
	
def AddAttributesFirstRoute(string,location,token):
	resultat=[]
	
	
	Code_NH1=token[0][0]
	Prefix=token[0][1]
	FirstNH=token[0][2]

	try:
		OtherNH=token[0][3]
		resultat=[ Prefix,[ [Code_NH1,FirstNH[0]]] + OtherNH.asList()]
	except IndexError:
		resultat=[ Prefix,[ [Code_NH1,FirstNH[0]]]]
	
	print(resultat)
	return resultat	
	
	
def ParseIpRoute(File__,modestr=False):

	resultat=None
	
	try:
		resultat = ParseIpRouteNexus(File__,modestr).asDict()
	except pp.ParseException as e1:
		try:
			resultat=ParseIpRouteCisco(File__,modestr).asDict()
		except pp.ParseException as e2:
			try:
				resultat= ParseIpRouteXR(File__,modestr).asDict()
			except pp.ParseException as e3 :
				print('Erreur de parsing\n')
				print('Fichier:'+File__)
				print(e1)
				print(e2)
				print(e3)
				
	return resultat
	

def ParseIpRouteStr(String__):
	return ParseIpRoute(String__,modestr=True)
	
def ParseIpRouteString(String__):
	return ParseIpRoute(String__,modestr=True)

def ParseDescriptionCiscoFile(File__):

	Resultat={}
	Interface=pp.Combine((pp.Literal('Vl')|pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Tu')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.A'))) | pp.Literal('Switch')|pp.Literal('Router')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	prompt=pp.Suppress(pp.OneOrMore(pp.Word(pp.alphanums+'-_'))+pp.Literal('#'))
	Show=pp.Suppress (pp.nestedExpr(opener='sh',closer='Description\n') )
	Admin_down=pp.Keyword('admin')+pp.Keyword('down')+pp.Keyword('down') 
	Up=pp.Keyword('up')+pp.Keyword('up') 
	Down=pp.Keyword('down')+pp.Keyword('down')
	Updown=pp.Keyword('up')+pp.Keyword('down')
	Deleted=pp.Keyword('deleted')+pp.Keyword('down')
	Status=pp.MatchFirst([Admin_down,Up,Down,Updown,Deleted])
	Description=pp.Suppress(Status)+pp.Combine(pp.OneOrMore(pp.CharsNotIn('\n')))
	NoDescription=(pp.Suppress( Status )).setParseAction(pp.replaceWith('None'))+pp.LineEnd().suppress()
	# Entry=Show|prompt|pp.Group(pp.LineStart()+Interface+Description+pp.LineEnd().suppress())|pp.Group(pp.LineStart()+Interface+NoDescription+pp.LineEnd().suppress())
	# Entries=pp.OneOrMore(Entry)
	# Resultat=Entries.parseFile(File__)
	
	# Entry=Show|prompt|pp.dictOf(pp.LineStart()+Interface, ( ( Description+pp.LineEnd().suppress() )| ( NoDescription+pp.LineEnd().suppress() ) ))
	
	Entry=pp.dictOf(pp.Optional(Show).suppress()+pp.LineStart()+Interface, pp.MatchFirst( [NoDescription,Description]) ) + pp.Optional(prompt)
	
	Resultat=Entry.parseFile(File__,parseAll=True)
	

	return Resultat.asDict()
	
def ParseDescriptionNexusFile(File__):

	Resultat={}
	Interface=pp.Combine((pp.Literal('Vl')|pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Tu')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	InterfacePo=pp.Combine(pp.Literal('Po')+pp.Word(pp.nums))
	prompt=pp.Suppress(pp.OneOrMore(pp.Word(pp.alphanums+'-_'))+pp.Literal('#'))
	Show=pp.Suppress (pp.nestedExpr(opener='sh',closer='Description\n') )
	LineDash=pp.Suppress(pp.Word('-',min=10)+pp.LineEnd())
	Speed=pp.Keyword('10G')|pp.Keyword('40G')|pp.Keyword('1000')
	DescriptionNexusPo=pp.Combine(pp.Word(pp.alphanums+'()_/\:;,.-[]{}<>*#"')+pp.ZeroOrMore(pp.Literal(" ")+pp.Word(pp.alphanums+'()/\:;,.-_[]{}<>*#"')))
	NoDescriptionNexusPo=(pp.Keyword('--')).setParseAction(pp.replaceWith('None'))
	DescriptionNexus=pp.Suppress( pp.Keyword('eth') + Speed)+pp.OneOrMore(pp.CharsNotIn('\n'))
	NoDescriptionNexus=pp.Suppress( pp.Keyword('eth') + Speed) +(pp.Keyword('--')).setParseAction(pp.replaceWith('None'))
	# Entry=Show|prompt|pp.Group(pp.LineStart()+Interface+Description+pp.LineEnd().suppress())|pp.Group(pp.LineStart()+Interface+NoDescription+pp.LineEnd().suppress())
	# Entries=pp.OneOrMore(Entry)
	# Resultat=Entries.parseFile(File__)
	
	# Entry=Show|prompt|pp.dictOf(pp.LineStart()+Interface, ( ( Description+pp.LineEnd().suppress() )| ( NoDescription+pp.LineEnd().suppress() ) ))
	Comment=(pp.Keyword('Port')+pp.Keyword('Type')+pp.Keyword('Speed')+pp.Keyword('Description'))|(pp.Keyword('Port')+pp.Keyword('Description'))
	BlocToIgnore=LineDash+Comment.suppress()+LineDash
	EntryNexusInt=Interface+pp.MatchFirst([NoDescriptionNexus,DescriptionNexus])
	EntryPo=InterfacePo+pp.MatchFirst([NoDescriptionNexusPo,DescriptionNexusPo])
	EntryNexus=EntryNexusInt|EntryPo
	
	temp_list_entries=[]
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingEntry in EntryNexus.scanString(file_str):
			temp_list_entries.append(parsingEntry[0].asList())
				

	return dict(temp_list_entries)	

def ParseDescriptionCiscoOrNexusFile(File__):
	Resultat={}
	
	try:
		Resultat=ParseDescriptionCiscoFile(File__)
	except  pp.ParseException as e1:
		print(e1)
		try:
			Resultat=ParseDescriptionNexusFile(File__)
		except  pp.ParseException as e2:
			print(File__)
			print(e1)
			print(e2)
			pdb.set_trace()
			
	return Resultat
	
def ParseDescriptionCiscoOrNexus(String__):
	return String__
	
def ParsePortChannelCiscoFile(File__):

	Show=(pp.nestedExpr(opener='sh',closer='\n') )
	prompt=pp.LineStart()+(pp.OneOrMore(pp.Word(pp.alphanums+'-_'))+pp.Literal('#'))
	Legend=(pp.nestedExpr(opener='Flags:',closer='---\n') )
	LegendSuiteNexus= (pp.nestedExpr(opener='Group',closer='---\n') ) 
	PoID=pp.Word(pp.nums)
	Flag=pp.Word('DPIHsrSRUM',exact=1)
	Flags=pp.OneOrMore(Flag)
	Protocol=pp.Literal('LACP')|pp.Literal('NONE').setParseAction(pp.replaceWith('None'))|pp.Literal('NONE')|pp.CaselessLiteral('pagp')|pp.Literal('-').setParseAction(pp.replaceWith('None'))
	Interface=pp.Group(pp.Word(pp.alphanums+('\/.-'))+pp.Literal('(').suppress()+Flags+pp.Literal(')').suppress())
	IntPo=pp.Combine(pp.Literal('Po')+pp.Word(pp.nums)+pp.Literal('(')+Flags+pp.Literal(')'))
	Type=pp.Suppress(pp.Literal('Eth'))
	EntryWithInterface=PoID+IntPo+pp.Optional(Type)+Protocol+pp.Group(pp.OneOrMore(Interface))
	EntryWithoutInterface=PoID+IntPo+pp.Literal('-').setParseAction(pp.replaceWith('None'))+pp.Suppress(pp.LineEnd()).setParseAction(lambda t: t.append('None'))
	Entry=EntryWithInterface|EntryWithoutInterface
	
	temp_list_entries=[]
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingEntry in Entry.scanString(file_str):
			temp_list_entries.append(parsingEntry[0].asList())
	
	
	return temp_list_entries
	
def ParsePortChannelCisco(Str__):

	Show=(pp.nestedExpr(opener='sh',closer='\n') )
	prompt=pp.LineStart()+(pp.OneOrMore(pp.Word(pp.alphanums+'-_'))+pp.Literal('#'))
	Legend=(pp.nestedExpr(opener='Flags:',closer='---\n') )
	LegendSuiteNexus= (pp.nestedExpr(opener='Group',closer='---\n') ) 
	PoID=pp.Word(pp.nums)
	Flag=pp.Word('DPIHsrSRUM',exact=1)
	Flags=pp.OneOrMore(Flag)
	Protocol=pp.Literal('LACP')|pp.Literal('NONE').setParseAction(pp.replaceWith('None'))|pp.Literal('NONE')|pp.CaselessLiteral('pagp')|pp.Literal('-').setParseAction(pp.replaceWith('None'))
	Interface=pp.Group(pp.Word(pp.alphanums+('\/.-'))+pp.Literal('(').suppress()+Flags+pp.Literal(')').suppress())
	IntPo=pp.Combine(pp.Literal('Po')+pp.Word(pp.nums)+pp.Literal('(')+Flags+pp.Literal(')'))
	Type=pp.Suppress(pp.Literal('Eth'))
	EntryWithInterface=PoID+IntPo+pp.Optional(Type)+Protocol+pp.Group(pp.OneOrMore(Interface))
	EntryWithoutInterface=PoID+IntPo+pp.Literal('-').setParseAction(pp.replaceWith('None'))+pp.Suppress(pp.LineEnd()).setParseAction(lambda t: t.append('None'))
	Entry=EntryWithInterface|EntryWithoutInterface

	temp_list_entries=[]
	for parsingEntry in Entry.scanString(Str__):
		temp_list_entries.append(parsingEntry[0].asList())
		
	return temp_list_entries
	
def ParseCdpNeighborDetail(File__):

	Resultat={}
	Limitation=pp.Suppress(pp.lineStart+pp.Literal('----------')+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	DeviceID=(pp.Literal('Device ID').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'-_().')).setParseAction(lambda s,l,t : re.split('\.|\(',t[0])[0].upper()).setResultsName('Neighbor')
	Interface=(pp.Literal('Interface').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'/')).setResultsName('Interface')
	Virgule=pp.Literal(',').suppress()
	InterfaceNeigh=(Virgule+pp.Literal('Port ID (outgoing port)').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'/')).setResultsName('Interface Neighbor')
	
	EntryCDP=Limitation+DeviceID+pp.SkipTo(Interface).suppress()+Interface+InterfaceNeigh
	
	with open(File__,'r') as fich__:	
		file_str=fich__.read()
	
	temp_list=[]
	for parsingCDPEntry in EntryCDP.scanString(file_str):
		temp_list.append(parsingCDPEntry[0].asDict())
		
	#print(temp_list)
		
	for cdp__ in temp_list:
		Resultat[cdp__['Interface'][0]]={'Neighbor': cdp__['Neighbor'] , 'Interface Neighbor': cdp__['Interface Neighbor'][0]}
	
		
	return Resultat
	
def ParseLldpNeighborDetail(File__):

	Resultat={}
	
	EmptyLine=pp.Suppress(pp.LineEnd())
	ChassisId=pp.Group(pp.Literal('Chassis id')+pp.Literal(':').suppress()+pp.OneOrMore(pp.CharsNotIn('\n')))
	UsedInfo=pp.Group((pp.OneOrMore(pp.CharsNotIn(':\n'))+pp.Literal(':').suppress()+pp.OneOrMore(pp.CharsNotIn('\n'))).addCondition(lambda tokens: tokens[0] != 'Chassis id'))
	UnusedInfo=pp.Suppress(pp.OneOrMore(pp.CharsNotIn(':\n')))
	Info=pp.LineStart()+pp.MatchFirst([UsedInfo,UnusedInfo])
	
	EntryLLDP=pp.OneOrMore(ChassisId)+pp.OneOrMore(Info)
	
	with open(File__,'r') as fich__:	
		file_str=fich__.read()
	
	temp_list=[]
	for parsingLLDPEntry in EntryLLDP.scanString(file_str):
		temp_dict={}
		list_cur=parsingLLDPEntry[0].asList()
		for info in list_cur:
			temp_dict[info[0].strip()]=info[1].strip()
		
		temp_list.append(temp_dict)
		
	#print(temp_list)
		
	for lldp__ in temp_list:
		try:
			Resultat[lldp__['Local Port id']]={'Neighbor': lldp__['System Name'] , 'Interface Neighbor': lldp__['Port id'], 'Model': lldp__['System Description'] , 'Management IP': lldp__['Management Address']}
		except KeyError as e:
				Resultat[lldp__['Local Port id']]={'Neighbor': lldp__['System Name'] , 'Interface Neighbor': None, 'Model': lldp__['System Description'] , 'Management IP': lldp__['Management Address']}


	
		
	return Resultat
	
def ParseLldpNeighborDetailString(Str__):

	Resultat={}
	
	EmptyLine=pp.Suppress(pp.LineEnd())
	ChassisId=pp.Group(pp.Literal('Chassis id')+pp.Literal(':').suppress()+pp.OneOrMore(pp.CharsNotIn('\n')))
	UsedInfo=pp.Group((pp.OneOrMore(pp.CharsNotIn(':\n'))+pp.Literal(':').suppress()+pp.OneOrMore(pp.CharsNotIn('\n'))).addCondition(lambda tokens: tokens[0] != 'Chassis id'))
	UnusedInfo=pp.Suppress(pp.OneOrMore(pp.CharsNotIn(':\n')))
	Info=pp.LineStart()+pp.MatchFirst([UsedInfo,UnusedInfo])
	
	EntryLLDP=pp.OneOrMore(ChassisId)+pp.OneOrMore(Info)
	
	temp_list=[]
	for parsingLLDPEntry in EntryLLDP.scanString(Str__):
		temp_dict={}
		list_cur=parsingLLDPEntry[0].asList()
		for info in list_cur:
			temp_dict[info[0].strip()]=info[1].strip()
		
		temp_list.append(temp_dict)
		
	#print(temp_list)
		
	for lldp__ in temp_list:
		try:
			Resultat[lldp__['Local Port id']]={'Neighbor': lldp__['System Name'] , 'Interface Neighbor': lldp__['Port id'], 'Model': lldp__['System Description'] , 'Management IP': lldp__['Management Address']}
		except KeyError as e:
				Resultat[lldp__['Local Port id']]={'Neighbor': lldp__['System Name'] , 'Interface Neighbor': None, 'Model': lldp__['System Description'] , 'Management IP': lldp__['Management Address']}


	
		
	return Resultat
	
	
def ParseCdpNeighborDetailString(String__):
	Resultat={}
	Limitation=pp.Suppress(pp.lineStart+pp.Literal('----------')+pp.OneOrMore(pp.CharsNotIn('\n')))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	DeviceID=(pp.Literal('Device ID').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'-_().')).setParseAction(lambda s,l,t : re.split('\.|\(',t[0])[0].upper()).setResultsName('Neighbor')
	Interface=(pp.Literal('Interface').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'/')).setResultsName('Interface')
	Virgule=pp.Literal(',').suppress()
	InterfaceNeigh=(Virgule+pp.Literal('Port ID (outgoing port)').suppress()+pp.Literal(':').suppress()+pp.Word(pp.alphanums+'/')).setResultsName('Interface Neighbor')
	
	EntryCDP=Limitation+DeviceID+pp.SkipTo(Interface).suppress()+Interface+InterfaceNeigh
	
	
	temp_list=[]
	for parsingCDPEntry in EntryCDP.scanString(String__):
		temp_list.append(parsingCDPEntry[0].asDict())
		
	#print(temp_list)
		
	for cdp__ in temp_list:
		Resultat[cdp__['Interface'][0]]={'Neighbor': cdp__['Neighbor'] , 'Interface Neighbor': cdp__['Interface Neighbor'][0]}
	
		
	return Resultat
	 
def ParseIntRate(File__):

	Resultat={}
	Space=pp.OneOrMore(pp.White(' '))
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Interface=pp.Combine( (pp.CaselessLiteral('Port-channel') | pp.Literal('FastEthernet') | pp.MatchFirst([pp.Literal('TenGigabitEthernet'),pp.Literal('GigabitEthernet'),pp.Literal('TenGigE'),pp.Literal('HundredGigE'),pp.Literal('Ethernet') ]) | pp.MatchFirst([pp.Literal('nV-Loopback'),pp.Literal('Loopback')]) | pp.Literal('Vlan')  | pp.Literal('Null')| pp.Literal('BVI')) + pp.Word(pp.nums+('\/.')))
	Hardware=pp.Suppress(pp.CaselessLiteral('Hardware')+pp.OneOrMore(pp.CharsNotIn('\n')))
	LigneInterface=Interface.setResultsName('Interface')+pp.Suppress(pp.Literal('is')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Description=pp.Suppress(pp.Literal('Description:'))+pp.OneOrMore(pp.CharsNotIn('\n')).setResultsName('Description')
	Virgule=pp.Literal(',').suppress()
	RateIn=(pp.Word(pp.nums)+pp.Literal('minute input rate')).suppress()  +pp.Combine(pp.Word(pp.nums)+pp.CaselessLiteral(' bits/sec')).setResultsName('Rate in')  + Virgule  + pp.Combine(pp.Word(pp.nums)+pp.CaselessLiteral(' packets/sec')).setResultsName('Packet in')+pp.LineEnd().suppress()
	RateOut=(pp.Word(pp.nums)+pp.Literal('minute output rate')).suppress()+pp.Combine(pp.Word(pp.nums)+pp.CaselessLiteral(' bits/sec')).setResultsName('Rate out') + Virgule  + pp.Combine(pp.Word(pp.nums)+pp.CaselessLiteral(' packets/sec')).setResultsName('Packet out')+pp.LineEnd().suppress()
	OtherLine=pp.Suppress(Space+pp.OneOrMore(pp.CharsNotIn('\n ')))
	EntryIf=LigneInterface+Hardware+pp.Optional(Description,default=None)+pp.SkipTo(RateIn).suppress()+RateIn+RateOut+pp.OneOrMore(OtherLine)
	
	with open(File__,'r') as fich__:	
		file_str=fich__.read()
	
	temp_list=[]
	for parsingIfEntry in EntryIf.scanString(file_str):
		temp_list.append(parsingIfEntry[0].asDict())
		
	#print(temp_list)
		
	for if__ in temp_list:
		try:
			Resultat[if__['Interface']]={'Description': if__['Description'] , 'Rate in': if__['Rate in'], 'Rate out': if__['Rate out'] , 'Packet in':if__['Packet in'] ,'Packet out':if__['Packet out'] }
		except KeyError:
			Resultat[if__['Interface']]={'Description': None , 'Rate in': if__['Rate in'], 'Rate out': if__['Rate out'] , 'Packet in':if__['Packet in'] ,'Packet out':if__['Packet out'] }
	
	return Resultat
	
	
def ParseInterfaceTransceiver(File__):
	"Only For Nexus"
	Resultat={}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	
	Interface=pp.LineStart()+pp.Combine(pp.Literal('Ethernet')  + pp.Word(pp.nums+'/'))+pp.LineEnd()
	Is=pp.Suppress(pp.Keyword('is'))
	Key=pp.OneOrMore(pp.Word(pp.alphanums+'./').addCondition(lambda tokens: str(tokens[0]) != 'is'  and not re.search('Ethernet',str(tokens[0] )))).setParseAction(lambda tokens: str(" ".join(tokens)))
	Entry=(Is+pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(lambda tokens: str(tokens[0]).strip())
	EntryDict=pp.dictOf(Key, Entry)
	BlocsInterfaces=pp.dictOf(pp.Optional(Show)+Interface,EntryDict+pp.Optional(hostname))
	
	Resultat=BlocsInterfaces.parseFile(File__)
	
	return Resultat.asDict()
	
def ParseInterfaceTransceiverString(String__):
	Resultat={}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	
	Interface=pp.LineStart()+pp.Combine(pp.Literal('Ethernet')  + pp.Word(pp.nums+'/'))+pp.LineEnd()
	Is=pp.Suppress(pp.Keyword('is'))
	Key=pp.OneOrMore(pp.Word(pp.alphanums+'./').addCondition(lambda tokens: str(tokens[0]) != 'is'  and not re.search('Ethernet',str(tokens[0] )))).setParseAction(lambda tokens: str(" ".join(tokens)))
	Entry=(Is+pp.OneOrMore(pp.CharsNotIn('\n'))).setParseAction(lambda tokens: str(tokens[0]).strip())
	EntryDict=pp.dictOf(Key, Entry)
	BlocsInterfaces=pp.dictOf(pp.Optional(Show)+Interface,EntryDict+pp.Optional(hostname))
	
	Resultat=BlocsInterfaces.parseString(String__)
	
	return Resultat.asDict()

def ParseVlandb(FileOrStr,mode="str"):
	Resultat={}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress (pp.nestedExpr(opener='VLAN',closer='--\n'))
	VlanId=pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 0 )
	Name=pp.Word(pp.alphanums+'-_:/.@')
	Status=pp.Literal('active')|pp.Literal('suspended')
	Interface=pp.Combine((pp.Literal('Vl')|pp.Literal('Mgmt')|pp.Literal('mgmt')|pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	ListeInterface=pp.Group(pp.OneOrMore(Interface+pp.ZeroOrMore(pp.Suppress(pp.MatchFirst([pp.Literal(',')]))+Interface)))
	InterfaceEntry=pp.dictOf(VlanId,Name+Status+pp.Optional(ListeInterface,default=[]))
	Type=pp.Suppress(pp.Word(pp.alphas))
	Mode=pp.Word(pp.alphas)
	TypeEntry=pp.Group(VlanId+Type+Mode)
	
	All=Show+Legend+pp.Group(InterfaceEntry)+Legend+pp.Group(pp.OneOrMore(TypeEntry))
	
	if mode=="str":
		try:
			Resultat=All.parseString(FileOrStr).asList()
		except:
			pass
			return None
	elif mode=="file":
		Resultat=All.parseFile(FileOrStr).asList()
	else:
		print("mode not supported")
		return None
	
	mode_dict={}
	for mode in Resultat[1]:
		mode_dict[mode[0]]=mode[1]
	
	return { vlan[0]:vlan[1:-1]+[mode_dict[vlan[0]]]+[vlan[-1]] for vlan in Resultat[0] }
	
def ParseStatusCiscoFile(File__):

	
	Status=pp.Literal('connected')|pp.Literal('notconnect')|pp.MatchFirst( [ pp.Literal('err-disabled') , pp.Literal('disabled') ] )|pp.Literal('unassigned')|pp.Literal('monitoring')|pp.Literal('notconnec')|pp.Literal('sfpAbsent')|pp.Literal('sfpInvali')|pp.Literal('xcvrInval')|pp.Literal('xcvrAbsen')|pp.Literal('channelDo')|pp.Literal('noOperMem')|pp.Literal('inactive')|pp.Literal('up')|pp.Literal('unknown e')|pp.Literal('bpdugrdEr')|pp.Literal('linkFlapE')
	Interface=pp.Combine((pp.Literal('Vl')|pp.Literal('Mgmt')|pp.Literal('mgmt')|pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 0 ))|pp.Literal('unassigned')|pp.Literal('trunk')|pp.Literal('f-path')|pp.Literal('routed')
	Speed=pp.MatchFirst([pp.Keyword('a-10G'),pp.Keyword('10G')])|pp.Keyword('40G')|pp.MatchFirst([pp.Keyword('a-1000'),pp.Keyword('1000'),pp.Keyword('a-100'),pp.Keyword('100'),pp.Keyword('a-10'),pp.Keyword('10')])|pp.Keyword('auto')
	Duplex=pp.MatchFirst([pp.Keyword('a-full'),pp.Keyword('full'),pp.Keyword('auto'),pp.Keyword('a-half'),pp.Keyword('half')])
	Type1=pp.Combine(pp.MatchFirst(['10/100/1000','10/100','1000','100G','10G'])+pp.CaselessLiteral('base')+pp.Optional('-')+pp.Word('TSLXR'))
	Type2=pp.Combine(pp.Literal('QSFP-')+pp.Literal('40G-')+pp.Word('SRC',exact=2))
	Type=pp.MatchFirst([pp.Literal('No Transceiver'),pp.Literal('Fabric Exte'),pp.CaselessLiteral('no gbic'),pp.CaselessLiteral('no X2'),pp.Literal('--'),Type1,Type2,pp.Literal('10g')])
	EntryNexus=Interface+pp.GoToColumn(29)+Status+Vlan+Duplex+Speed+pp.Optional(Type)
	EntryOldIOS2=Interface+pp.GoToColumn(27)+Status+Vlan+Duplex+Speed+pp.Optional(Type)
	EntryOldIOS=Interface+pp.GoToColumn(33)+Status+Vlan+Duplex+Speed+pp.Optional(Type)
	Entry=EntryNexus|EntryOldIOS|EntryOldIOS2
	Entries=pp.Group(pp.OneOrMore(Entry))
	
	
	temp_dict_entries={}
	with open(File__,'r') as fich__:
		file_str=fich__.read()
		for parsingEntry in Entry.scanString(file_str):
			temp_list=parsingEntry[0].asList()
			temp_dict_entries[temp_list[0]]=temp_list[1:]
	
	
	return temp_dict_entries	
	
def ParseStatusCisco(Str__):

	
	Status=pp.Literal('connected')|pp.Literal('notconnect')|pp.MatchFirst( [ pp.Literal('err-disabled') , pp.Literal('disabled') ] )|pp.Literal('unassigned')|pp.Literal('monitoring')|pp.Literal('notconnec')|pp.Literal('sfpAbsent')|pp.Literal('sfpInvali')|pp.Literal('xcvrInval')|pp.Literal('xcvrAbsen')|pp.Literal('channelDo')|pp.Literal('noOperMem')|pp.Literal('inactive')|pp.Literal('up')|pp.Literal('unknown e')|pp.Literal('bpdugrdEr')|pp.Literal('linkFlapE')
	Interface=pp.Combine((pp.Literal('Vl')|pp.Literal('Mgmt')|pp.Literal('mgmt')|pp.Literal('Po')|pp.Literal('Te')|pp.Literal('Gi')|pp.Literal('Fa')|pp.Literal('Lo')|pp.Literal('Eth')|pp.Literal('sup-eth'))+pp.Word(pp.nums+('\/.'))) | pp.Literal('Switch')|pp.Literal('Router')| pp.Combine( (pp.Literal('Port-channel') | pp.Literal('FastEthernet') | pp.Literal('GigabitEthernet')  ) + pp.Word(pp.nums+('\/.')) )
	Vlan=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <4096 and int(tokens[0]) >= 0 ))|pp.Literal('unassigned')|pp.Literal('trunk')|pp.Literal('f-path')|pp.Literal('routed')
	Speed=pp.MatchFirst([pp.Keyword('a-10G'),pp.Keyword('10G')])|pp.Keyword('40G')|pp.MatchFirst([pp.Keyword('a-1000'),pp.Keyword('1000'),pp.Keyword('a-100'),pp.Keyword('100'),pp.Keyword('a-10'),pp.Keyword('10')])|pp.Keyword('auto')
	Duplex=pp.MatchFirst([pp.Keyword('a-full'),pp.Keyword('full'),pp.Keyword('auto'),pp.Keyword('a-half'),pp.Keyword('half')])
	Type1=pp.Combine(pp.MatchFirst(['10/100/1000','10/100','1000','100G','10G'])+pp.CaselessLiteral('base')+pp.Optional('-')+pp.Word('TSLXR'))
	Type2=pp.Combine(pp.Literal('QSFP-')+pp.Literal('40G-')+pp.Word('SRC',exact=2))
	Type=pp.MatchFirst([pp.Literal('No Transceiver'),pp.Literal('Fabric Exte'),pp.CaselessLiteral('no gbic'),pp.CaselessLiteral('no X2'),pp.Literal('--'),Type1,Type2,pp.Literal('10g')])
	EntryNexus=Interface+pp.GoToColumn(29)+Status+Vlan+Duplex+Speed+pp.Optional(Type)
	EntryOldIOS2=Interface+pp.GoToColumn(27)+Status+Vlan+Duplex+Speed+pp.Optional(Type)
	EntryOldIOS=Interface+pp.GoToColumn(33)+Status+Vlan+Duplex+Speed+pp.Optional(Type)
	Entry=EntryNexus|EntryOldIOS|EntryOldIOS2
	Entries=pp.Group(pp.OneOrMore(Entry))
	
	
	temp_dict_entries={}

	for parsingEntry in Entry.scanString(Str__):
		temp_list=parsingEntry[0].asList()
		temp_dict_entries[temp_list[0]]=temp_list[1:]
	
	
	return temp_dict_entries	
	
def getShortPort(longPort):

	shortPort=""
	#pdb.set_trace()
	
	if re.match(r'[Gg]igabit[eE]thernet',longPort):
		shortPort=re.sub(r'[Gg]igabit[eE]thernet','Gi',longPort)
	
	elif re.match(r'[Ff]ast[eE]thernet',longPort):
		shortPort=re.sub(r'[Ff]ast[eE]thernet','Fa',longPort)

	elif re.match(r'[Tt]en[Gg]igabit[eE]thernet',longPort):
		shortPort=re.sub(r'[Tt]en[Gg]igabit[eE]thernet','Te',longPort)

	elif re.match(r'[eE]thernet',longPort):
		shortPort=re.sub(r'[eE]thernet','Eth',longPort)
		
	elif re.match(r'[Vv]lan',longPort):
		shortPort=re.sub(r'[Vv]lan','Vl',longPort)
		
	elif re.match(r'[Ll]ooback',longPort):
		shortPort=re.sub(r'[Ll]ooback','Lo',longPort)
		
	elif re.match(r'[Pp]ort-channel',longPort):
		shortPort=re.sub(r'[Pp]ort-channel','Po',longPort)
		
	else: 
		shortPort=longPort
	
	return shortPort
	
def getLongPort(shortPort):

	longPort=""
	#pdb.set_trace()
	
	if re.match(r'[Gg]i[0-9]',shortPort):
		longPort=re.sub(r'[Gg]i','GigabitEthernet',shortPort)
	
	elif re.match(r'[Ff]a[0-9]',shortPort):
		longPort=re.sub(r'[Ff]a','FastEthernet',shortPort)

	elif re.match(r'[Tt]e[0-9]',shortPort):
		longPort=re.sub(r'[Tt]e','TenGigabitEthernet',shortPort)

	elif re.match(r'[eE]th[0-9]',shortPort):
		longPort=re.sub(r'[eE]th','Ethernet',shortPort)
		
	elif re.match(r'[Vv]l[0-9]',shortPort):
		longPort=re.sub(r'[Vv]l','Vlan',shortPort)
		
	elif re.match(r'[Ll]o[0-9]',shortPort):
		longPort=re.sub(r'[Ll]o','Loopback',shortPort)
		
	elif re.match(r'[Pp]o[0-9]',shortPort):
		longPort=re.sub(r'[Pp]o','port-channel',shortPort)
		
	elif re.match(r'port-channel[0-9]',shortPort,re.IGNORECASE):
		longPort=re.sub(r'[Pp]o','Port-channel',shortPort)
		
	else: 
		longPort=shortPort
	
	return longPort
	
def getDictInterfaceMac(Mac__):

	Mac_dict={}
	#pdb.set_trace()
	try:
		for entry in Mac__:
			for interface in entry[2:]:
				try:
					if [entry[0],entry[1]] not in Mac_dict[interface]:
						Mac_dict[entry[2]].append([entry[0],entry[1]])
		
				except KeyError:
					Mac_dict[entry[2]]=[[entry[0],entry[1]]]
	except 	TypeError:
		pass
	return Mac_dict
	
def getDictInterfaceArp(Arp__):

	Arp_dict={}
	#pdb.set_trace()
	for equipement__ in Arp__.keys():
		try:
			for vrf__ in Arp__[equipement__]:
				for entry in Arp__[equipement__][vrf__]:
					if entry:
						try:
							IP__=entry[0]
						except IndexError:
							IP__=None
						try:
							MAC__=entry[1]
						except IndexError:
							MAC__=None
						try:
							interface__=entry[2]
						except IndexError:
							interface__=None
							
						try:
							if [equipement__ ,vrf__,interface__,IP__] not in Arp_dict[MAC__]:
								Arp_dict[MAC__].append([equipement__ ,vrf__,interface__,IP__] )
				
						except KeyError:
							Arp_dict[MAC__]=[[equipement__ ,vrf__,interface__,IP__]]
		except TypeError as typeerror:
			print(typeerror)
			pdb.set_trace()
			
					
	return Arp_dict
		

def getArp(Arp_dict,Macs):
	resultat=[]
	
	
	
	
	if Macs[0] != None:
		for Mac__ in Macs[0]:
			#if Mac__[1]== '0050.56b4.6a0c':
			#	pdb.set_trace()
			try:
				resultat_cur={Mac__[1]:Arp_dict[Mac__[1]]}
			except KeyError:
				resultat_cur={Mac__[1]:None}
			resultat.append(resultat_cur)
	else:
		resultat.append(None)
		
	return resultat

def multiping(ALLIP):
	for mac_cur in ALLIP.keys():
		try:
			for IP_info in ALLIP[mac_cur]['IP']:
				print(IP_info[3],IP_info[1]+'_'+IP_info[2])
		except IndexError as e:
			pdb.set_trace()
			print(e)
		
def ParseMacDescriptionCiscoFile(FileMac__,FileDesc__):
	Resultat=[]
	Mac=ParseMacCiscoFile(FileMac__)
	Desc=ParseDescriptionCiscoOrNexusFile(FileDesc__)
	
	Mac_dict=getDictInterfaceMac(Mac)
	
	

	#pdb.set_trace()
	
	for port in Mac_dict.keys():
		
		shortPort=getShortPort(port)
		try:
			temp_mac=Mac_dict[port]
		except KeyError:
			temp_mac=None
			
		try:
			temp_desc=Desc[shortPort]
			
		except KeyError:
			temp_desc=None
			
		Resultat.append([shortPort,temp_mac,temp_desc])
		

	return Resultat

def ParseMacDescriptionCiscoFile_Dict(FileMac__,FileDesc__):
	Resultat={}
	Mac=ParseMacCiscoFile(FileMac__)
	Desc=ParseDescriptionCiscoOrNexusFile(FileDesc__)
	
	Mac_dict=getDictInterfaceMac(Mac)
			
	#pdb.set_trace()
	
	for port in Mac_dict.keys():
		
		shortPort=getShortPort(port)
		try:
			temp_mac=Mac_dict[port]
		except KeyError:
			temp_mac=None
			
		try:
			temp_desc=Desc[shortPort]
			
		except KeyError:
			temp_desc=None
			
		Resultat[shortPort]=[temp_mac,temp_desc]
		

	return Resultat
	
def ParseDescriptionMacCiscoFile(FileMac__,FileDesc__):
	Resultat=[]
	Mac=None
	try:
		Mac=ParseMacCiscoFile(FileMac__)
	except:
		print("Erreur Parsing Mac:"+FileMac__)
		
	Desc=ParseDescriptionCiscoOrNexusFile(FileDesc__)
	
	Mac_dict=getDictInterfaceMac(Mac)
			
	#pdb.set_trace()
	
	for port in Desc.keys():
		
		longPort=getLongPort(port)
		shortPort=getShortPort(port)
		try:
			mac=Mac_dict[shortPort]
			
		except KeyError:
			try:
				mac=Mac_dict[longPort]
				
			except KeyError:
				mac=None
						
		try:
			Resultat.append([port,mac,Desc[port]])
		
		except KeyError:
			Resultat.append([port,mac,None])
	
	return Resultat
	
def ParseDescriptionMacCiscoFile_Dict(FileMac__,FileDesc__):
	Resultat={}
	Mac=ParseMacCiscoFile(FileMac__)
	Desc=ParseDescriptionCiscoOrNexusFile(FileDesc__)
	
	Mac_dict=getDictInterfaceMac(Mac)
			
	#pdb.set_trace()
	
	for port in Desc.keys():
		#pdb.set_trace()
		longPort=getLongPort(port)
		shortPort=getShortPort(port)
		
		try:
			mac=Mac_dict[shortPort]
			
		except KeyError:
			try:
				mac=Mac_dict[longPort]
				
			except KeyError:
				mac=None
			
		try:
			Resultat[shortPort]=[mac,Desc[port]]
		
		except KeyError:
			Resultat[shortPort]=[mac,None]
	#pdb.set_trace()
	return Resultat
	
def ParsePrefixSet(FileOrStr,mode="file"):
	Resultat={}
	hostname=pp.Suppress(pp.Word(pp.alphanums+'-_')+pp.Literal('#'))
	Show=pp.Suppress(pp.Optional(hostname)+pp.Literal('sh')+pp.OneOrMore(pp.CharsNotIn('\n')))
	Legend=pp.Suppress(pp.Literal('Listing for all Prefix Set objects'))
	virgule=pp.Suppress(pp.Literal(','))
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	slash=(pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <=32 and int(tokens[0]) >= 0 ))
	prefix=pp.Combine(ipAddress+pp.Literal('/')+slash)
	KeyFilter=pp.Literal('ge')|pp.Literal('le')|pp.Literal('eq')
	FilterList=pp.dictOf(KeyFilter,slash)
	filterSetEntry=pp.dictOf(prefix,pp.Optional(FilterList,default=None)+pp.Optional(virgule))
	Name=pp.Literal('prefix-set').suppress()+pp.Word(pp.alphanums+'_-. \/()=[]:{},')
	endSet=pp.Literal('end-set').suppress()
	BlocPrefixSet=pp.Optional(Show)+pp.SkipTo('prefix-set').suppress()+pp.dictOf(Name,filterSetEntry+endSet+pp.Optional(pp.Literal('!')))

	if mode=='str':
		Resultat=BlocPrefixSet.parseString(FileOrStr).asDict()
	elif mode=='file':
		Resultat=BlocPrefixSet.parseFile(FileOrStr).asDict()
		
	return Resultat
		
def writeCsv(list_result,fichier_csv):
	
	with open(fichier_csv,'w+') as csvfile:
		csvwriter=csv.writer(csvfile,delimiter=';',quotechar='"',quoting=csv.QUOTE_ALL)
		for entry in list_result:
			csvwriter.writerow(entry)
	
	return None
	
def writeCsvRaw(list_result,fichier_csv):
	
	with open(fichier_csv,'w+') as csvfile:
		csvwriter=csv.writer(csvfile,delimiter=';')
		for entry in list_result:
			csvwriter.writerow(entry)
	
	return None
	
def getPortChannel(ShortInterface,equipement,ListPo):
	
	resultat=None
	
	#pdb.set_trace()
	
	for Po in ListPo[equipement]:
		try:
			Liste_Interface=Po[3]
		except KeyError:
			os.exit(5)
		
		for int__ in Liste_Interface:
			if ShortInterface == int__[0]:
				resultat='Po'+Po[0]
	
	
	return resultat
	
def getPortChannelComplete(ShortInterface,equipement,ListPo):
	
	resultat=None
	
	#pdb.set_trace()
	
	for Po in ListPo[equipement]:
	
		try:
			Liste_Interface=Po[3]
		except KeyError:
			os.exit(5)
			
		for int__ in Liste_Interface:
			if ShortInterface == int__[0]:
				resultat=Po
				break
	
	
	return resultat
	
def getSwitchport(Interface,equipement,ListSwitchport):
	
	resultat=None
	
	#pdb.set_trace()
	
	try:
		resultat=ListSwitchport[equipement][Interface]
	except KeyError:
		try:	
			LongInterface=getLongPort(Interface)
			resultat=ListSwitchport[equipement][LongInterface]
		except KeyError:
			pass
	
	return resultat
	
def getEquipementFromFilename(str):
	resultat=None
	NomFile1=pp.Word(pp.alphanums+'-')+pp.Literal('_').suppress()+pp.Word(pp.nums,min=8,max=8).suppress()+pp.Literal('_').suppress()+pp.Word(pp.nums+'hms').suppress()+pp.Literal('.log').suppress()
	NomFile2=pp.Word(pp.alphanums+'-_')+pp.Literal('.log').suppress()
	NomFile3=pp.Word(pp.alphanums+'-_')+pp.Suppress(pp.Optional(pp.CaselessLiteral('.dns')+pp.Word(pp.nums,min=2,max=2)+pp.Literal('socgen.log')))
	NomFile=pp.MatchFirst([NomFile1,NomFile2,NomFile3])
	resultat=NomFile.parseString(str).asList()[0]
	
	return resultat


	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	mode_normal = parser.add_argument_group('mode normal','Parse des fichiers simples ou des repertoires')
	mode_interface = parser.add_argument_group('mode evolue','Parse des fichiers et merge des fichiers')
	mode_dump = parser.add_argument_group('mode dump','examine les dumps DC')
	
	group1=mode_normal.add_mutually_exclusive_group(required=False)
	group0=mode_normal.add_mutually_exclusive_group(required=True)
	
	group0.add_argument("-f", "--fichier",action="store",help="fichier le resultat du show vrf")
	group0.add_argument("-r", "--repertoire",action="store",help="repertoire contenant les show")
	group0.add_argument("-L", "--load_dump",action="store",help=u"Utilise un fichier Dump")
	
	parser.add_argument("-F", "--Fichierdescription",action="store",help="Fichier show description",required=False)
	parser.add_argument("-E", "--Extract",action="store",help="Extraction uniquement des infos contenu dans le fichier csv Format nom;interface",required=False)
	group1.add_argument("-v", "--vrf",action="store_true",help="Parse les show vrf")
	group1.add_argument("-a", "--arp",action="store_true",help="Parse les show ip arp")
	group1.add_argument("-p", "--portchannel",action="store_true",help="Parse les show port-channel/etherchannel summary")
	group1.add_argument("-s", "--status",action="store_true",help="Parse les show interface status")
	group1.add_argument("-w", "--switchport",action="store_true",help="Parse les show interface switchport")
	group1.add_argument("-m", "--mac",action="store_true",help="Parse les show mac")
	group1.add_argument("-d", "--description",action="store_true",help="Parse les show ip route")
	group1.add_argument("-o", "--route",action="store_true",help="Parse les show inerface description")
	group1.add_argument("-z", "--cdp",action="store_true",help="Parse les show cdp neighbor detail")
	group1.add_argument("-t", "--transceiver",action="store_true",help="Parse les show interface tranceiver")
	group1.add_argument("-b", "--bgpsummary",action="store_true",help="Parse les show bgp summary")
	group1.add_argument("-n", "--shnextpo",action="store_true",help="Parse les shNextPo")
	group1.add_argument("-g", "--bgptable",action="store_true",help="Parse les show bgp")
	group1.add_argument("-x", "--fex",action="store_true",help="Parse les show fex")
	group1.add_argument("-i", "--interface",action="store_true",help="Parse les show run et extrait les interfaces")
	group1.add_argument("-R", "--interface_rate",action="store_true",help="Parse les show interface et extrait les debits")
	group1.add_argument("-l", "--vlan",action="store_true",help="Parse les show run et extrait vlans")
	group1.add_argument("-k", "--lldp",action="store_true",help="Parse les show lldp neighbor detail")
	group1.add_argument("-u", "--countererror",action="store_true",help="Parse les show interface counter error")
	group1.add_argument("--fexfabric",action="store_true",help="Parse les show interface fex-fabric")
	group1.add_argument("--vlan-db",dest='vlandb',action="store_true",help="Parse les show interface fex-fabric")
	group1.add_argument("--interface-run",dest='interface_deep',action="store_true",help="Parse les show interface plus précisément")
	group1.add_argument("--prefix-set",dest='prefixset',action="store_true",help="Parse les show rpl prefix-set")
	group1.add_argument("--run-acl",dest='runacl',action="store_true",help="Parse les acl dans le show run")
	mode_interface.add_argument("-D", "--Descr",action="store",help="Fichier ou repertoire description")
	mode_interface.add_argument("-M", "--Mac",action="store_true",help="Parse les show mac")
	mode_interface.add_argument("-P", "--PortChannel",action="store",help="Fichier ou repertoire avec show port-channel")
	mode_interface.add_argument("-S", "--Status",action="store",help="Fichier ou repertoire avec show interface status")
	mode_interface.add_argument("-W", "--Switchport",action="store",help="Fichier ou repertoire avec show interface switchport")
	mode_interface.add_argument("-A", "--All_desc",action="store_true",help=u"Affiche tous les ports meme sans informations")
	mode_interface.add_argument("-C", "--Complement_ARP",action="store",help=u"Fichier ou repertoire ARP Cisco/nexus",required=False)
	mode_interface.add_argument("-U", "--filedump",action="store",help=u"Sauvegarde dans un fichier Dump",required=False)
	mode_dump.add_argument("--dump-read",dest='readdump',action="store_true",help="Affiche le dump !!! Verbeux!!!")
	mode_dump.add_argument("--extract-ip",dest='extractip',action="store_true",help="Extrait les IP d'un dump")
	mode_dump.add_argument("--extract-mac",dest='extractip',action="store_true",help="Extrait les mac d'un dump")
	mode_dump.add_argument("--get-macs",dest='getmacs',action="store",help="Fichier Mac pour lequel on cherche des infos")
	mode_dump.add_argument("--format-ping-ip",dest='pingip',action="store_true",help="Extrait les IP d'un dump et affiche un format pour multiping")
	parser.add_argument("-c", "--csvFichier",action="store",help="fichier resultat en csv",required=False)
	parser.add_argument("--save-yaml",dest='yaml_file',action="store",help="Save to yaml",required=False)
	
	args = parser.parse_args()
	resultat=""
	
	#test=ParseDescriptionNexusFile('IMPACT/AQUICLSZEUS/DESC/aquiclszeusr1-05_20170918_16h53m33s.log')
	#print(test)
	
	if args.fichier:
		if args.vrf:
			resultat=ParseVrfFile(args.fichier)
			
		elif args.mac:
			resultat=ParseMacCiscoFile(args.fichier)
	
		elif args.arp:
			resultat=ParseArpCiscoFile(args.fichier)
			
		elif args.description:
			resultat=ParseDescriptionCiscoOrNexusFile(args.fichier)
		
		elif args.Mac and args.Descr:
			if args.All_desc:
				resultat=ParseDescriptionMacCiscoFile(args.fichier,args.Descr)
			else:
				resultat=ParseMacDescriptionCiscoFile(args.fichier,args.Descr)
				
		elif args.portchannel:
			resultat=ParsePortChannelCiscoFile(args.fichier)
		
		elif args.status:
			resultat=ParseStatusCiscoFile(args.fichier)
			
		elif args.switchport:
			resultat=ParseSwitchPort(args.fichier)
			
		elif args.route:
			resultat=ParseIpRoute(args.fichier)
			
		elif args.cdp:
			resultat=ParseCdpNeighborDetail(args.fichier)	
			
		elif args.lldp:
			resultat=ParseLldpNeighborDetail(args.fichier)	
			
		elif args.transceiver:
			resultat=ParseInterfaceTransceiver(args.fichier)
			
		elif args.bgpsummary:
			resultat=ParseBgpNeighborFile(args.fichier)
			
		elif args.bgptable:
			resultat=ParseBgpTable(args.fichier)
			
		elif args.fex:
			resultat=ParseShFex(args.fichier)
			
		elif args.fexfabric:
			resultat=parseShIntFexFile(args.fichier)
			
		elif args.shnextpo:
			resultat=ParseShNextPoFile(args.fichier)
		
		elif args.interface:
			resultat=ParseRunInterfaceFile(args.fichier)	
			
		elif args.interface_rate:
			resultat=ParseIntRate(args.fichier)
		
		elif args.vlan:
			resultat=ParseVlanRunFile(args.fichier)		
		
		elif args.countererror:
			resultat=ParseIntCounterError(args.fichier)		
			
		elif args.interface_deep:
			resultat=ParseRunInterfaceDeeperFile(args.fichier)	
			
		elif args.vlandb:
			resultat=ParseVlandb(args.fichier,mode="file")	
			
		elif args.prefixset:
			resultat=ParsePrefixSet(args.fichier,mode="file")	
			
		elif args.runacl:
			resultat=ParseRunAccessList(args.fichier,mode="file")		
		print(resultat)
		
		if args.csvFichier:
			writeCsv(resultat,args.csvFichier)
			
		if args.yaml_file:
			saveResult(resultat,args.yaml_file)
			
	elif args.repertoire:
	
		if args.mac:
			macs={}
			Liste_file_show=glob.glob(args.repertoire+'/*.log')
				
			for file_show_long in Liste_file_show:
				file_show=file_show_long.split('/')[-1]
				equipement=getEquipementFromFilename(file_show)
				resultat_cur=ParseMacCiscoFile(file_show_long)
				macs[equipement]=resultat_cur
			
			for equipement__ in macs.keys():
				print(equipement__+':')
				print(macs[equipement__])
				
		elif args.Mac and args.Descr:
			macs={}
			macs__={}
			Liste_file_show_mac=glob.glob(args.repertoire+'/*.log')
			Liste_file_show_desc=glob.glob(args.Descr+'/*.log')
			
			if args.Complement_ARP:
				arps__={}
				Liste_file_show_arp=glob.glob(args.Complement_ARP+'/*.log')
				for file_show_arp in Liste_file_show_arp:
					file_show_arp__=file_show_arp.split('/')[-1]
					equipement_l3=getEquipementFromFilename(file_show_arp__)
					arps__[equipement_l3]=ParseArpCiscoFile(file_show_arp)
					#pdb.set_trace()
				print(arps__)
				arps__Dict=getDictInterfaceArp(arps__)
				print(arps__Dict)
				
			if args.Descr:
				desc__={}
				Liste_file_show_desc=glob.glob(args.Descr+'/*.log')
				for file_show_desc in Liste_file_show_desc:
					file_show_desc__=file_show_desc.split('/')[-1]
					equipement__=getEquipementFromFilename(file_show_desc__)
					desc__[equipement__]=ParseDescriptionCiscoOrNexusFile(file_show_desc)
					#pdb.set_trace()*******
				print(desc__)
				
			if args.PortChannel:
				Pos__={}
				Liste_file_show_portchannel=glob.glob(args.PortChannel+'/*.log')
				for file_show_portchannel in Liste_file_show_portchannel:
					file_show_portchannel__=file_show_portchannel.split('/')[-1]
					equipement_po=getEquipementFromFilename(file_show_portchannel__)
					Pos__[equipement_po]=ParsePortChannelCiscoFile(file_show_portchannel)
					#pdb.set_trace()
				print(Pos__)
				
			if args.Status:
				Status__={}
				Liste_file_show_status=glob.glob(args.Status+'/*.log')
				for file_show_status in Liste_file_show_status:
					file_show_status__=file_show_status.split('/')[-1]
					equipement_status=getEquipementFromFilename(file_show_status__)
					Status__[equipement_status]=ParseStatusCiscoFile(file_show_status)
					#pdb.set_trace()
				print(Status__)
				
			if args.Switchport:
				Switchport__={}
				Liste_file_show_switchport=glob.glob(args.Switchport+'/*.log')
				for file_show_switchport in Liste_file_show_switchport:
					file_show_switchport__=file_show_switchport.split('/')[-1]
					equipement_switchport=getEquipementFromFilename(file_show_switchport__)
					Switchport__[equipement_switchport]=ParseSwitchPort(file_show_switchport)
					#pdb.set_trace()
				print(Switchport__)
			
			for file_show_mac_long in Liste_file_show_mac:
				file_show_mac=file_show_mac_long.split('/')[-1]
				equipement=getEquipementFromFilename(file_show_mac)
				try:
					file_show_desc_long=glob.glob(args.Descr+'/'+equipement+'*.log')[0]
				except IndexError:
					pdb.set_trace()
					
				resultat_cur=None
				
				if args.All_desc:
					#pdb.set_trace()
					resultat_cur=ParseDescriptionMacCiscoFile(file_show_mac_long,file_show_desc_long)
					macs__[equipement]=ParseDescriptionMacCiscoFile_Dict(file_show_mac_long,file_show_desc_long)
				else:
					resultat_cur=ParseMacDescriptionCiscoFile(file_show_mac_long,file_show_desc_long)
					macs__[equipement]=ParseMacDescriptionCiscoFile_Dict(file_show_mac_long,file_show_desc_long)
				
				macs[equipement]=resultat_cur

				print('stop')
				print(macs__)
				 
			if not args.Extract:
				
				for equipement__ in macs.keys():
					print(equipement__+':')
					print(macs[equipement__])
					
				if args.filedump and args.Complement_ARP and args.PortChannel and  args.Status and args.Switchport:
					dc_cur=DC(macs__,desc__,arps__Dict,Status__,Pos__,Switchport__)
					print("Save filedump:'+args.filedump")
					dc_cur.save(args.filedump)
					
				print('coucou')
				#print(macs['tigclsr4-01']['Po52'])	
			else:
				if args.filedump:
					dc_cur=DC(macs__,desc__,arps__Dict,Status__,Pos__,Switchport__)
					print("Save filedump:'+args.filedump")
					dc_cur.save(args.filedump)
					
				with open(args.Extract,'r') as file_info_port:
					resultat_csv=[]
					resultat_csv.append(entete__)
					for ligne in file_info_port:
						#print(ligne)
						ligne_col=[ x for x in  re.split(',|;| ',ligne)  if x ]
						#print(ligne_col)
						equipement=ligne_col[0].lower()
						interface=ligne_col[1].replace('\n','')
						#print(interface)
						
						if args.Complement_ARP and not args.PortChannel and not args.Status:			

							try:
								mac_cur=str(macs__[equipement][interface][0])
								description=str(desc__[equipement][interface])
								#pdb.set_trace()
								try:
									#pdb.set_trace()
									Arp_cur=getArp(arps__Dict,macs__[equipement][interface])
									print(equipement+" "+interface+":"+mac_cur+" L3:"+str(Arp_cur))
									resultat_csv.append([equipement,interface,description,mac_cur,str(Arp_cur)])
								except TypeError:
									#pdb.set_trace()
									pass
									print(equipement+" "+interface+":"+mac_cur+" L3:None")
									resultat_csv.append([equipement,interface,description,mac_cur,'None'])
							except KeyError:
								#pdb.set_trace()
								#print('Interface non traitee:'+equipement+"->"+interface)
								print(equipement+" "+interface+":"+'MAC:None'+" L3:None")
								description=str(desc__[equipement][interface])
								resultat_csv.append([equipement,interface,description,['None'],'None'])
								
						elif args.Complement_ARP and args.PortChannel and not args.Status:
							try:
								mac_cur=str(macs__[equipement][interface][0])
								description=str(desc__[equipement][interface])
								Po_cur=getPortChannel(interface,equipement,Pos__)
								#pdb.set_trace()
								try:
									#pdb.set_trace()
									Arp_cur=getArp(arps__Dict,macs__[equipement][interface])
									print(equipement+" "+interface+":"+mac_cur+" L3:"+str(Arp_cur)+"Po:"+str(Po_cur))
									resultat_csv.append([equipement,interface,description,mac_cur,str(Arp_cur),str(Po_cur)])
								except TypeError:
									#pdb.set_trace()
									pass
									print(equipement+" "+interface+":"+mac_cur+" L3:None"+"Po:"+str(Po_cur))
									resultat_csv.append([equipement,interface,description,mac_cur,'None',str(Po_cur)])
							except KeyError:
								#pdb.set_trace()
								#print('Interface non traitee:'+equipement+"->"+interface)
								description=str(desc__[equipement][interface])
								Po_cur=getPortChannel(interface,equipement,Pos__)
								print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+"Po:"+str(Po_cur))
								description=str(desc__[equipement][interface])
								resultat_csv.append([equipement,interface,description,['None'],'None',str(Po_cur)])
						
						
						elif args.Complement_ARP and not args.PortChannel and args.Status:			
						
							try:
								mac_cur=str(macs__[equipement][interface][0])
								description=str(desc__[equipement][interface])
								Status_Cur=str(Status__[equipement][interface])
								#pdb.set_trace()
								try:
									#pdb.set_trace()
									Arp_cur=getArp(arps__Dict,macs__[equipement][interface])
									print(equipement+" "+interface+":"+mac_cur+" L3:"+str(Arp_cur)+" Status:"+Status_Cur)
									resultat_csv.append([equipement,interface,description,mac_cur,str(Arp_cur),Status_Cur])
								except TypeError:
									#pdb.set_trace()
									pass
									print(equipement+" "+interface+":"+mac_cur+" L3:None"+" Status:"+Status_Cur)
									resultat_csv.append([equipement,interface,description,mac_cur,'None'," Status:"+Status_Cur])
							except KeyError:
								#pdb.set_trace()
								#print('Interface non traitee:'+equipement+"->"+interface)
								Status_Cur=str(Status__[equipement][interface])
								print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+" Status:"+Status_Cur)	
								description=str(desc__[equipement][interface])	
								resultat_csv.append([equipement,interface,description,['None'],'None',Status_Cur])
								
						elif args.Complement_ARP and args.PortChannel and  args.Status and not args.Switchport:
						
							try:
								mac_cur=str(macs__[equipement][interface][0])
								description=str(desc__[equipement][interface])
								Po_cur=getPortChannel(interface,equipement,Pos__)
								Status_Cur=str(Status__[equipement][interface])
								#pdb.set_trace()
								try:
									#pdb.set_trace()
									Arp_cur=getArp(arps__Dict,macs__[equipement][interface])
									print(equipement+" "+interface+":"+mac_cur+" L3:"+str(Arp_cur)+"Po:"+str(Po_cur),Status_Cur)
									resultat_csv.append([equipement,interface,description,mac_cur,str(Arp_cur),str(Po_cur),Status_Cur])
								except TypeError:
									#pdb.set_trace()
									pass
									print(equipement+" "+interface+":"+mac_cur+" L3:None"+"Po:"+str(Po_cur))
									resultat_csv.append([equipement,interface,description,mac_cur,'None',str(Po_cur),Status_Cur])		
							except KeyError:		
								#pdb.set_trace()		
								#print('Interface non traitee:'+equipement+"->"+interface)
								#if interface == 'Fa3/45':
								#	pdb.set_trace()	
								description=str(desc__[equipement][interface])
								Status_Cur=str(Status__[equipement][interface])
								Po_cur=getPortChannel(interface,equipement,Pos__)								
								print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+"Po:"+str(Po_cur))			
								resultat_csv.append([equipement,interface,description,['None'],'None',str(Po_cur),Status_Cur])		
											
						
						elif args.Complement_ARP and args.PortChannel and  args.Status and args.Switchport:
							mac_po=False
							try:
								mac_cur=macs__[equipement][interface][0]
								description=str(desc__[equipement][interface])
								Po_cur=getPortChannel(interface,equipement,Pos__)
								Po_comp=getPortChannelComplete(interface,equipement,Pos__)
								if mac_cur == 'None':
									mac_cur=macs__[equipement][str(Po_cur)]
									mac_po=True
								Status_Cur=str(Status__[equipement][interface])
								Switchport_cur=str(getSwitchport(interface,equipement,Switchport__))
								
								#pdb.set_trace()
								try:
									#pdb.set_trace()
									if mac_po:
										Arp_cur=getArp(arps__Dict,macs__[equipement][str(Po_cur)])
									else:
										Arp_cur=getArp(arps__Dict,macs__[equipement][interface])
									print(equipement+" "+interface+":"+str(mac_cur)+" L3:"+str(Arp_cur)+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
									resultat_csv.append([equipement,interface,description,str(mac_cur),str(Arp_cur),str(Po_comp),Status_Cur,Switchport_cur])
								except TypeError:
									pdb.set_trace()
									print(equipement+" "+interface+":"+str(mac_cur)+" L3:None"+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)
									resultat_csv.append([equipement,interface,description,str(mac_cur),'None',str(Po_comp),Status_Cur,Switchport_cur])		
							except KeyError:		
								try:
									description=str(desc__[equipement][interface])
								except:
									pdb.set_trace()
								try:
									Status_Cur=str(Status__[equipement][interface])
								except:
									pdb.set_trace()
								Po_cur=getPortChannel(interface,equipement,Pos__)								
								print(equipement+" "+interface+":"+'MAC:None'+" L3:None"+"Po:"+str(Po_cur)+" STATUS:"+Status_Cur+" VLAN:"+Switchport_cur)			
								resultat_csv.append([equipement,interface,description,['None'],'None',str(Po_comp),Status_Cur,Switchport_cur])					
						
						
						
								
							
					if args.csvFichier:
						writeCsv(resultat_csv,args.csvFichier)
						

		
	elif args.load_dump:
		dc_cur=DC()
		dc_cur.load(args.load_dump)
		resultat_csv_dump=None
		
		if args.extractip:
			AllIP=dc_cur.extract_all_ip()
			print(AllIP)
			
		if args.pingip:
			AllIP=dc_cur.extract_all_ip()
			multiping(AllIP)
			
		if args.getmacs:
			MacListe=[]
			ResultMac=[]
			with open(args.getmacs) as fich_mac:
				MacListe=fich_mac.read().split()
				for mac__ in MacListe:
					ResultMac.append(dc_cur.getInfoMac(mac__))
			
			if args.csvFichier:
				writeCsv(ResultMac,args.csvFichier)
			
		if args.Extract :
			resultat_csv_dump=dc_cur.extractInterfaces(args.Extract)
			
			
			if args.csvFichier:
				writeCsv(resultat_csv_dump,args.csvFichier)
