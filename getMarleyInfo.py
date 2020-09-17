#!/usr/bin/env python3.7
# coding: utf-8

import csv
import pdb
import argparse
import pickle
import os
import pprint
import glob
from pathlib import Path
from cdpEnv import interconnexion
from tabulate import tabulate
from collections import OrderedDict
import xlsxwriter
import pyparsing as pp


csv.field_size_limit(2000000000)
CSV_MARLEY="/home/X112097/CSV/MARLEY/hw_EUR_GTS_network.csv"
PATH_IP_DUMP="/home/X112097/CSV/MARLEY/DUMP/"

def get_last_dump(directory):
	return max(glob.glob(directory+'/*'),key=os.path.getctime)
	
def print_tabulate_dict(dict__):
	print(tabulate([[ val for val in dict__.values()]] ,headers=dict__.keys(),tablefmt='psql'))
	
def getbasefilename(file_with_path):
	return Path(file_with_path).stem
	
def ParseMac(macStr):
	resultat=None
	Octet=pp.Word(pp.nums+'abcdef'+'ABCDEF',exact=2).setParseAction(lambda t : t[0].upper())
	Separator=pp.Word(':-. ',exact=1).setParseAction(pp.replaceWith(':'))
	MacWoSep=pp.Combine(6*Octet).setParseAction(lambda t : t[0][0]+t[0][1]+":"+t[0][2]+t[0][3]+":"+t[0][4]+t[0][5]+":"+t[0][6]+t[0][7]+":"+t[0][8]+t[0][9]+":"+t[0][10]+t[0][11])
	MacCisco=pp.Combine((2*Octet+Separator)*2+(2*Octet)).setParseAction(lambda t : t[0][0]+t[0][1]+":"+t[0][2]+t[0][3]+":"+t[0][5]+t[0][6]+":"+t[0][7]+t[0][8]+":"+t[0][10]+t[0][11]+":"+t[0][12]+t[0][13])
	MacUnix=pp.Combine((Octet+Separator)*5+Octet)
	MacSpec1=pp.Suppress(pp.Literal('SEP'))+MacWoSep
	MacSpec2=pp.Suppress(pp.Literal('0x'))+MacWoSep
	Mac=pp.MatchFirst([MacWoSep,MacCisco,MacUnix,MacSpec1,MacSpec2])
	try:
		resultat=Mac.parseString(macStr,parseAll=True).asList()[0]
	except  pp.ParseException as ppError:
		print(f"Vérifiez le format de l'adresse Mac:{macStr}")
		raise(ppError)
			 
	return resultat
	
def ParseIP(IPStr,mode="list"):

	
	octet = (pp.Word(pp.nums).addCondition(lambda tokens:int(tokens[0]) <256 and int(tokens[0]) >= 0 ))
	ipAddress=pp.Combine(octet + ('.'+octet)*3)+pp.Optional(pp.OneOrMore('.'+octet)).suppress()
	
	if mode=="list":
		resultat=[]
		parseResultIP=ipAddress.scanString(IPStr)
		resultat=[ip[0].asList()[0] for ip in parseResultIP ]
	else:
		resultat=None
		try:
			resultat=ipAddress.parseString(IPStr,parseAll=True).asList()[0]
		except pp.ParseException as ppError:
			print(f"Vérifiez le format de l'adresse IP:{IPStr}")
			raise(ppError)
		
	return resultat
	

class intercoMarley(interconnexion):
	def __init__(self,host_src,port_src,host_dest,port_dest,type,PathdbMarley=PATH_IP_DUMP):
		super().__init__(host_src,port_src,host_dest,port_dest)
		self.type=type
		
		self.host_source=host_src
		self.host_destination=host_dest
		self.port_source=port_src
		self.port_destination=port_dest
		
		self.new_header=['Réf Câble','MA','Nom','SN','Model','DC','Salle','Baie','Position','Port','Type']
		self.header_tr={'MA':'Asset ID','Nom':'Usual name','SN':'Serial number','Model':'Model','Salle':'Room','Baie':'Cabinet','Position':'Rack position'}
		self.dbMarley=get_last_dump(PathdbMarley)
		self.info_src=self.getMarleyInfo(self.host_source,self.port_source,self.type)
		self.info_dst=self.getMarleyInfo(self.host_destination,self.port_destination,self.type)
		
		#print_tabulate_dict(self.info_src)
		#print_tabulate_dict(self.info_dst)
		
		
	def toList(self):
		return [self.host_source,self.port_source,self.host_destination,self.port_destination,self.type ]
		
	def toListComplete(self):
		return [element for element in self.info_src.values() ] + [element for element in self.info_dst.values() ] 

	def __str__(self):
		resultat=StringIO()
		for ligne in super().__str__().splitlines():
			resultat.write(ligne+";"+self.type)
		
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
	
	def getMarleyInfo(self,host__,port__,type__):
		resultat=OrderedDict()
		curMarleydb=marleyContainer(dump=self.dbMarley)
		curInfo=curMarleydb.getInfoEquipment(host__)
		
		
		for element in self.new_header:
			if element in self.header_tr.keys():
				try:
					resultat[element]=curInfo[self.header_tr[element]]
				except KeyError as e:
					pdb.set_trace()
					print(e)
					resultat[element]="INCOMPLETE"
					
			else:
				resultat[element]="TBD"
		
		resultat['Port']=port__
		resultat['Type']=type__
		
		return resultat
		
	
class intercoMarleyContainer(object):
	def __init__(self,fichier_csv):
		self.headers=['hostSrc','portSrc','hostDst','portDst','type']
		reader=csv.DictReader(open(fichier_csv, "r",encoding="iso-8859-1"),fieldnames=self.headers,delimiter=';')
		self.intercos=[]
		
		for row in reader:
			self.intercos.append(intercoMarley(row['hostSrc'],row['portSrc'],row['hostDst'],row['portDst'],row['type'] ))
	
	def __repr__(self):
		return tabulate(self.toList(),headers=self.headers,tablefmt='psql')
	
	def __str__(self):
		return tabulate(self.toList(),headers=self.headers,tablefmt='psql')	
		
	def toList(self):
		return [ interco.toList() for interco in self.intercos ]
	
	def printer(self):
		print(str(self))
	
class marleyContainer(object):
	"Marley Container"
	
	def __init__(self,csv_file="",dump=""):
			
		if csv_file:
			reader=csv.DictReader(open(csv_file, "r",encoding="iso-8859-1"),delimiter=';')
			self.header=['Asset ID','Usual name','Brand','Model','Serial number','Type','Building','Room','Cabinet','Rack','Rack position','OOB','OOB Port','MAC Address','Main IP Address','Remote Console IP Address','IP Address']
			self.allDataByHosts={}
			self.allDataBySN={}
			self.allDataByMac={}
			self.allDataByIPMain={}
			self.allDataByIPRemote={}
			self.allDataByIP={}
			
			nb_entry=sum(1 for line in open(csv_file,encoding="iso-8859-1"))-1
			indice=1
			for row in reader:
				self.allDataByHosts[row['Usual name']]={ key:value for key , value in dict(row).items() if key in self.header }
				self.allDataBySN[row['Serial number']]={ key:value for key , value in dict(row).items() if key in self.header }
				if row['MAC Address']:
					try:
						mac_cur=ParseMac(row['MAC Address'])
					except pp.ParseException:
						continue
					if mac_cur:
						if mac_cur not in self.allDataByMac:
							self.allDataByMac[mac_cur]=[]
						self.allDataByMac[mac_cur].append({ key:value for key , value in dict(row).items() if key in self.header })
				if row['Main IP Address']:
					ip_curs=ParseIP(row['Main IP Address'])
					for ip_cur in ip_curs:
						if ip_cur not in self.allDataByIPMain:
							self.allDataByIPMain[ip_cur]=[]
						self.allDataByIPMain[ip_cur].append({ key:value for key , value in dict(row).items() if key in self.header })
						#print(f'ip_cur:{ip_cur}')
				if row['Remote Console IP Address']:
					ip_curs=ParseIP(row['Remote Console IP Address'])
					for ip_cur in ip_curs:
						if ip_cur not in self.allDataByIPRemote:
							self.allDataByIPRemote[ip_cur]=[]
						self.allDataByIPRemote[ip_cur].append({ key:value for key , value in dict(row).items() if key in self.header })
						#print(f'ip_cur:{ip_cur}')
				if row['IP Address']:
					ip_curs=ParseIP(row['IP Address'])
					for ip_cur in ip_curs:
						if ip_cur not in self.allDataByIP:
							self.allDataByIP[ip_cur]=[]
						self.allDataByIP[ip_cur].append({ key:value for key , value in dict(row).items() if key in self.header })
						#print(f'ip_cur:{ip_cur}')
				print(f'avancement:{indice}/{nb_entry}')
				indice+=1
		if dump:
			self.load(dump)
		
		
	def getInfoEquipment(self,hostname):
		resultat={}
		try:
			resultat=self.allDataByHosts[hostname]
			#pprint.pprint(resultat)
		except KeyError as e:
			print('%s inconnue dans le fichier Marley' % hostname)
			
		return resultat
		
	def getInfoSN(self,SN):
		resultat={}
		try:
			resultat=self.allDataBySN[SN]
			#pprint.pprint(resultat)
		except KeyError as e:
			print('SN %s inconnue dans le fichier Marley' % SN)
			
		return resultat
		
	def getInfoMac(self,MacStr):
		resultat={}
		Mac=ParseMac(MacStr)
		try:
			resultat=self.allDataByMac[Mac]
			#pprint.pprint(resultat)
		except KeyError as e:
			print('MAC %s inconnue dans le fichier Marley' % Mac)
			
		return resultat	
		
	def getInfoIP(self,IPStr):
		resultat={}
		IP=ParseIP(IPStr,mode="normal")
		try:
			resultat['ipMain']=self.allDataByIPMain[IP]
			#pprint.pprint(resultat)
		except KeyError as e:
			pass
		try:
			resultat['ipRemoteConsole']=self.allDataByIPRemote[IP]
			#pprint.pprint(resultat)
		except KeyError as e:
			pass
		try:
			resultat['IP']=self.allDataByIP[IP]
			#pprint.pprint(resultat)
		except KeyError as e:
			pass
			
		return resultat
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		base=None
		
		with open(filename,'rb') as file__:
			base=pickle.load(file__)
		
		try:
			self.allDataByHosts=base.allDataByHosts
			self.allDataBySN=base.allDataBySN
			self.allDataByMac=base.allDataByMac
			self.allDataByIPMain=base.allDataByIPMain
			self.allDataByIPRemote=base.allDataByIPRemote
			self.allDataByIP=base.allDataByIP
		except:
			print('ERROR')
			
def setwidth(f):
	def wrapper_setwidth(*args,**kwargs):
		liste_cur=args[1]
		xls=args[0]
		namefile=args[3]
		indice=0
		for element in liste_cur:
			if len(element)>(xls.maxcolumn[indice]):
				xls.maxcolumn[indice]=len(element)
				xls.worksheets[namefile].set_column(indice, indice, xls.maxcolumn[indice]+2)
			indice+=1
		f(*args,**kwargs)
	return wrapper_setwidth
			
class xlsMarleyMatrix(object):
	def __init__(self,filename,intMarleyObjCnr__):
		self.filename=filename
		self.intMarleyObjCnr=intMarleyObjCnr__
		self.workbook  = xlsxwriter.Workbook(filename)
		self.worksheets={}
		self.indices={}
		for name_file in intMarleyObjCnr__.keys():
			self.worksheets[name_file] = self.workbook.add_worksheet(name_file)
			self.indices[name_file]=0
		self.header=['Réf Câble','MA','Nom','SN','Model','DC','Salle','Baie','Position','Port','Type']
		self.initMaxColumn()
		self.initStyle()
		self.initHeader()
		self.writeInterco()
		
		self.workbook.close()
		
	def initHeader(self):
	
		for name_file in self.worksheets.keys():
			self.worksheets[name_file].merge_range('A1:K1', "Source", self.header_format)
			self.worksheets[name_file].merge_range('L1:V1', "Destination", self.header_format)
			self.indices[name_file]+=1
			self.writeList(self.header*2,self.header_format_2,name_file)

	def initMaxColumn(self):
		self.maxcolumn=[]
		for element in self.header*2:
			self.maxcolumn.append(len(element))
	
	@setwidth	
	def writeList(self,liste,style,namefile,offset=0):
		current_offset=offset
		for element in liste:
			self.worksheets[namefile].write(self.indices[namefile],current_offset,element,style)
			current_offset+=1
		self.indices[namefile]+=1
		
	def initStyle(self):
		self.header_format=self.workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': '#A9A9A9'})
			
		self.header_format_2=self.workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': '#DCDCDC'})
			
		self.default_format=self.workbook.add_format({
			'align': 'center',
			'valign': 'vcenter',
			'fg_color': '#B0E0E6'})
	
	def writeInterco(self):
		for name_file in self.intMarleyObjCnr.keys():
			for interco__ in self.intMarleyObjCnr[name_file].intercos:
				self.writeList(interco__.toListComplete(),self.default_format,name_file)

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-e", "--equipement",  action="store",help="hostname de l'équipement Marley",required=False)
	group1.add_argument("--sn",  action="store",help="Serial Number de l'équipement Marley",required=False)
	group1.add_argument("--mac",  action="store",help="mac de l'équipement Marley",required=False)
	group1.add_argument("--ip-address", action="store",dest='IPaddress',help="IP de l'équipement Marley",required=False)
	parser.add_argument("-c", "--csv",  action="store",help="fichier csv contenant les informations Marley",required=False)
	parser.add_argument("-d", "--dump_dir",  action="store",default=PATH_IP_DUMP,help="Répertoire contenant les dump",required=False)
	parser.add_argument("-s", "--save",  action="store",help="fichier de sauvegarde dump",required=False)
	parser.add_argument("-x", "--xls",  action="store",help="Matrice Excel",required=False)
	group1.add_argument("-m", "--matrice", nargs='*', action="store",help="matrice de câblage simplifié en csv",required=False)
	args = parser.parse_args()
	
	if args.equipement:
		if args.csv:
			BaseMarley=marleyContainer(csv_file=args.csv)
			pprint.pprint(BaseMarley.getInfoEquipment(args.equipement))
			if args.save:
				BaseMarley.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseMarley=marleyContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseMarley.getInfoEquipment(args.equipement))
			else:
				print("Ajouter un dump")
				
	elif args.sn:
		if args.csv:
			BaseMarley=marleyContainer(csv_file=args.csv)
			pprint.pprint(BaseMarley.getInfoSN(args.sn))
			if args.save:
				BaseMarley.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseMarley=marleyContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseMarley.getInfoSN(args.sn))
			else:
				print("Ajouter un dump")
	elif args.mac:
		if args.csv:
			BaseMarley=marleyContainer(csv_file=args.csv)
			pprint.pprint(BaseMarley.getInfoMac(args.mac))
			if args.save:
				BaseMarley.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseMarley=marleyContainer(dump=get_last_dump(args.dump_dir))
				pprint.pprint(BaseMarley.getInfoMac(args.mac))
			else:
				print("Ajouter un dump")
	elif args.IPaddress:
		if args.csv:
			BaseMarley=marleyContainer(csv_file=args.csv)
			pprint.pprint(BaseMarley.getInfoIP(args.IPaddress))
			if args.save:
				BaseMarley.save(args.save)
				
		else:	
			if os.listdir(args.dump_dir):
				print("On cherche dans le dump %s" % args.dump_dir)
				BaseMarley=marleyContainer(dump=get_last_dump(args.dump_dir))
				pdb.set_trace()
				pprint.pprint(BaseMarley.getInfoIP(args.IPaddress))
			else:
				print("Ajouter un dump")		
	elif args.matrice:
		Matrix={}
		for matrice_element in args.matrice:
			name__=getbasefilename(matrice_element)
			Matrix[name__]=intercoMarleyContainer(matrice_element)
			print(name__+":")
			Matrix[name__].printer()
		
		if args.xls:
			xlsMarleyMatrix(args.xls,Matrix)
		