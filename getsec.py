#!/usr/bin/env python3.7
# coding: utf-8

import getpass
import argparse
import pyAesCrypt
from os import stat, remove
import pyparsing as pp
import pdb

TMP="/home/x112097/TMP/filetsk.txt"
TSK="MaisTueSF0uKouKouTskBillyJoeAzertyRienOublieRubiK5794"
BYPASS="/home/x112097/CONNEXION/LISTE_BYPASS.TXT"
bufferSize = 64 * 1024

class secSbe(object):

	def __init__(self,db__=None):
		if db__:
			self.db=db__
			self.load(self.db)
		else:
			self.getInitTac()
			self.getInitWhs()
			self.getInitWin()
	def getInitTac(self):
		self.tac=getpass.getpass('Entre le tacacs:')
	
	def getInitWhs(self):
		self.whs=getpass.getpass('Entre le whats:')
		
	def getInitWin(self):
		self.win=getpass.getpass('Entre le windows:')
		
	def pri(self):
		print(self.tac)
		print(self.whs)
		print(self.win)
		
	def save(self,file):
		
		
		with open(TMP, "w") as fInTmp:
			fInTmp.write('[\''+self.tac+'\',\''+self.whs+'\',\''+self.win+'\']')
			
		pyAesCrypt.encryptFile(TMP, file, TSK, bufferSize)

	
		remove(TMP)
		
		
	def getMode(self,equipement):
		all_tsk=self.load_bypass(BYPASS)
		connexion=('x112097',self.tac)
		try:
			info_cur=all_tsk[equipement.upper()]
			#print("connexion speciale")
			if info_cur[0]=='CUSTOM':
				connexion=(info_cur[1],info_cur[2])
			if info_cur[0]=='CUSTOM_IP':
				connexion=(info_cur[1],info_cur[2])
		except KeyError:
			#print("connexion normale")
			pass
		
		#print(str(connexion))
		
		return connexion
		
	def load(self,db):
		pyAesCrypt.decryptFile(db, TMP, TSK, bufferSize)
		with open(TMP, "r") as fOutTmp:
			temp_output=eval(fOutTmp.read())
			self.tac=temp_output[0]
			self.whs=temp_output[1]
			self.win=temp_output[2]
		
		#print(str(temp_output))
		
		try:
			remove(TMP)
		except FileNotFoundError:
			pass
		
		return
		
	def load_bypass(self,filename):
		Hostname=pp.Word(pp.alphanums+'-_').setParseAction(lambda t : t[0].upper())
		Mode=pp.Literal("ALTEON_PROXY_EXP")|pp.Literal("CDN")|pp.MatchFirst([pp.Literal("CUSTOM_VPX"),pp.Literal("CUSTOM_IP"),pp.Literal("CUSTOM")])|pp.Literal("EXPOSE_2")|pp.Literal("LOGIN_ACS_TELNET")|pp.Literal("TACACS_SSH_SPEC")
		Info=pp.OneOrMore(pp.CharsNotIn('\n')).setParseAction(lambda t : t[0].split())
		Entry=pp.dictOf(Hostname,pp.Group(Mode+pp.Optional(Info,default=None)))
		All_tsk=Entry.parseFile(filename).asDict()
		return(All_tsk)

		
		
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	group=parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-d", "--db",action="store",help="db tsk",required=False)
	parser.add_argument("-p", "--printing",action="store_true",help=argparse.SUPPRESS,required=False)
	group.add_argument("-s", "--save",action="store",help='Sauvegarde dans le fichier',required=False)
	parser.add_argument('-e',"--equipement",action="store",help='Chercher les u/p pour un equipement',required=False)
	
	args = parser.parse_args()
	
	if args.db:
		A=secSbe(args.db)
	else:
		A=secSbe()
	
	if args.save:
		A.save(args.save)
		
	if args.printing:
		A.pri()
		
	if args.equipement:
		A.getMode(args.equipement)
		