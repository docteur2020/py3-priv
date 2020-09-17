#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import unicode_literals

import time
from time import gmtime, strftime , localtime
import threading
import sys
import os
import argparse
import pdb
import re
from io import StringIO 
from io import BytesIO
from pexpect import pxssh
from pexpect import ExceptionPexpect , exceptions
import pickle
from ipcalc import *
import dns.resolver
import ipaddress
import random

class ResetError(Exception):
	def __init__(self, message):
		super(ResetError, self).__init__(message)

class ErrorNeedRetry(Exception):
	def __init__(self, message,valeur):
		super(ErrorNeedRetry, self).__init__(message)
		self.valeur_to_retry=valeur
	
class ThreadPrintNimp(threading.Thread):
	def __init__(self,nimp_obj):
		threading.Thread.__init__(self)
		self.nimp=nimp_obj
		self.pid=self.nimp.entier*13+7
		self.etape=0
		
	def run(self):

		
		for i in range(1,100,1):
			self.etape=self.etape+1
			time.sleep(3)
			print('Thread PID'+self.pid.__str__()+' NIMP:'+self.nimp.__str__())
			if self.etape%5==0:
				print('Etape*13:')
				valeur=int(input('Entrer la nouvelle valeur (old:'+self.nimp.entier.__str__()+'):'))
				
				try:
					self.nimp.fonction_intermediaire(valeur)
				except ErrorNeedRetry as E:
					print("Probleme remonté:"+E.valeur_to_retry.__str__())
					raise ErrorNeedRetry("Valeur non conforme level 2",self.nimp.entier)
					
		print("Exiting Thread PID"+self.pid.__str__())
	
		
class nimp(object):
	def __init__(self,entier):
		self.entier=entier
		
	
	def set_value(self,entier):
		self.entier=entier
		if self.entier==0:
			raise ResetError("Valeur 0:, merci de reiniatiliser passer au plan B.")
			
	def __str__(self):
		return "=="+self.entier.__str__()+"=="
		
	def set_value_with_test(self,entier):
		try:
			try:
				self.set_value(entier)
			except ResetError:
				print("Probleme")
				raise ErrorNeedRetry("Valeur non conforme",A.entier)
		except IOError:
			print("ALL")
			
	def fonction_intermediaire(self,entier):
		try:
			self.set_value_with_test(entier)
		except IOError:
			print("ALL PLUS HAUT")
			
class nimp_plus_haut(object):
	def __init__(self,nimp):
		self.nimp=nimp
	
	def set_value_plus_haut(self,valeur):
		self.nimp.fonction_intermediaire(valeur)

if __name__ == '__main__':
	"Fonction principale"
	A=nimp(5)
	valeur=int(input('Entrer la nouvelle valeur (old:'+A.entier.__str__()+'):'))
	try:
		A.fonction_intermediaire(valeur)
	except ErrorNeedRetry as E:
		print("Probleme remonté:"+E.valeur_to_retry.__str__())
		
	print(A)
	
	B=nimp_plus_haut(A)
	
	valeur=int(input('Entrer la nouvelle valeur en mode plus haut (old:'+B.nimp.entier.__str__()+'):'))
	try:
		B.set_value_plus_haut(valeur)
	except ErrorNeedRetry as E2:
		print("Probleme remonté en mode plus haut:"+E2.valeur_to_retry.__str__())	
		
	print("On fait du nimp threadé, let' go...")
	
	nimp_thread=[]
	for i in range(1,10,1):
		nimp_thread.append(ThreadPrintNimp(nimp(i)))
		
	for nimp_to_print in nimp_thread:
		try:
			nimp_to_print.start()
		except ErrorNeedRetry as E: 
			print("Probleme remonté en mode plus haut en thread:"+E.valeur_to_retry.__str__()+" PID:"+nimp_to_print.pid._str__())
		
		

		