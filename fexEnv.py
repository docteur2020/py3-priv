#!/usr/bin/env python3.7
# coding: utf-8


from ParsingShow import ParseShFex,writeCsv,getEquipementFromFilename
import csv
import sys
import os
import argparse
import glob
import pdb
import pickle
from io import StringIO
import pyparsing as pp
from getMarleyInfo import *

class fex(object):
	def __init__(self,parent,nom,status,model,SN,fexId,marleyInfo=""):
		self.n5k=parent
		self.nom=nom
		self.status=status
		self.model=model
		self.SN=SN
		self.fexId=fexId
		self.marleyInfo=marleyInfo
		
	def __eq__(self,other_fex):
		return (self.SN==other_fex.SN ) 
		
	def __str__(self):
		return self.n5k+";"+self.nom+";"+self.status+";"+self.model+";"+self.SN+";"+str(self.marleyInfo)
		
	def getListe(self):
		return [self.n5k,self.nom,self.status,self.model,self.SN,self.fexId,*self.marleyInfo.values()]
		

	

class fexs(object):
	def __init__(self):
		self.liste_fex=[]
		
	def add_element(self,fex__):
		if fex__ not in self:
			self.liste_fex.append(fex__)
			
	def __contains__(self,fex__):
		result=False
		for fex__cur in self.liste_fex:
			if fex__cur == fex__:
				result=True
				
		return result
		
	def __str__(self):
		resultat=StringIO()
		for fex__ in self.liste_fex:
			resultat.write(str(fex__)+"\n")
			
		resultat_str=resultat.getvalue()
		resultat.close()
		
		return resultat_str
		
	
		
class DC_fex(object):
	def __init__(self,repertoire="",dump=""):
		self.fex_DC=[]
		self.SN=[]
		self.baseMarley=marleyContainer(dump=get_last_dump(PATH_IP_DUMP))
		if repertoire:
			Liste_file_show_fex=glob.glob(repertoire+'/*.log')
			for file_show_fex in Liste_file_show_fex:
				file_show_fex__=file_show_fex.split('/')[-1]
				equipement__=getEquipementFromFilename(file_show_fex__).upper()
				try:
					fex_cur_parsed=ParseShFex(file_show_fex)
					for fex_id in fex_cur_parsed:
						fex_cur=fex(equipement__,fex_cur_parsed[fex_id ][0],fex_cur_parsed[fex_id ][1],fex_cur_parsed[fex_id ][2],fex_cur_parsed[fex_id ][3],fex_id,self.baseMarley.getInfoSN(fex_cur_parsed[fex_id ][3]))
						
						if fex_cur.SN not in self.SN:
							self.fex_DC.append(fex_cur)
							self.SN.append(fex_cur.SN)
					
				except pp.ParseException:
					print("pas de fex sur "+equipement__)
		if dump:
			self.load(dump)
			
		#pdb.set_trace()
			
	def __str__(self):
	
		resultat=StringIO()
		for fex__ in self.fex_DC:
			resultat.write(fex__.__str__())
			
		resultat_str=resultat.getvalue()
		resultat.close()
			
		return resultat_str
		
	def getListe(self):
		resultat=[]
		
		for fex__ in self.fex_DC:
			resultat.append(fex__.getListe())
				
		
		return resultat
		
	def save(self,filename):
		with open(filename,'wb') as file__:
			pickle.dump(self,file__)
			
	def load(self,filename):
		dc=None
		
		with open(filename,'rb') as file__:
			dc=pickle.load(file__)
		
		try:
			self.fex_DC=dc.fex_DC

		except:
			print('ERROR')
			
	
	

if __name__ == '__main__':
	"Fonction principale"
	
	parser = argparse.ArgumentParser()
	group1=parser.add_mutually_exclusive_group(required=True)
	group1.add_argument("-r", "--repertoire",action="store",help="Répertoire contenant les output show fex")
	group1.add_argument("-d", "--dumpfile",action="store",help="Contient le fichier dump type fex")
	parser.add_argument("-e", "--exportcsv",action="store",help=u"Résultat sous forme fichier csv",required=False)
	parser.add_argument("-s", "--save",action="store",help=u"Résultat dans fichier dump",required=False)
	args = parser.parse_args()
	
	if args.repertoire:
		A=DC_fex(repertoire=args.repertoire)
	elif args.dumpfile:
		A=DC_fex(dump=args.dumpfile)
		
	print(str(A))
	
	if args.exportcsv:
		writeCsv(A.getListe(),args.exportcsv)
		
	if args.save:
		A.save(args.save)
		
	print(A)