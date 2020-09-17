#!/usr/bin/env python3.7
# coding: utf-8

import re
import argparse
import os
import pdb


def compZero(min,id):
	return (min-len(id))*'0'+id
	
def splitFile(filename,filter,mode="normal"):
	blocInfo=[]
	match=[]
	
	
	with open(filename,"r") as file__:
		all_lines=file__.read()
		
		blocCur=""
		for line in all_lines.splitlines(all_lines.count('\n')):
			regresult=re.search(filter,line)
			if mode=="normal":
				if regresult and regresult.group(0) not in match:
					match.append(regresult.group(0))
					
					if blocCur:
						blocInfo.append(blocCur)
						
					blocCur=line
				else:
					blocCur+=line
			else:
				if regresult:
					match.append(regresult.group(0))
					
					if blocCur:
						blocInfo.append(blocCur)
						
					blocCur=line
				else:
					blocCur+=line
		blocInfo.append(blocCur)
	return blocInfo
	
def saveStrFile(str__,filename):
		with open(filename,"w+") as file__:
			file__.write(str__)
		
class FilenameGenerator(object):
	def __init__(self,filename):
		self.path = os.path.dirname(filename)
		self.filename = os.path.basename(filename)
		self.current=1
		self.filename_cur=os.path.splitext(self.filename)[0]+'_'+compZero(3,str(self.current))+os.path.splitext(self.filename)[1]
		self.initDir()
		self.high=999

	def __iter__(self):
		return self
		
	def __repr__(self):
		return self.repertoire+'/'+self.filename_cur

	def __next__(self):
		if self.current > self.high:
			raise StopIteration
		else:
			self.oldfile=self.filename_cur
			self.current+=1
			self.filename_cur=os.path.splitext(self.filename)[0]+'_'+compZero(3,str(self.current))+os.path.splitext(self.filename)[1]
		return self.repertoire+'/'+self.oldfile
			
	def initDir(self):
		self.repertoire=self.path+"/SPLIT"
		if not os.path.exists(self.repertoire):
			os.makedirs(self.repertoire)

if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file')
	parser.add_argument("--filter", action="store",help="filtre regex",required=True)
	parser.add_argument("--strict", action="store_true",help="split si le regex change",required=False)
	
	args = parser.parse_args()
	
	fileIter=FilenameGenerator(args.file)
	
	if args.strict:
		mode="strict"
	else:
		mode="normal"
	
	resultats_str=splitFile(args.file,args.filter,mode=mode)
	
	for resultat in resultats_str:
		saveStrFile(resultat,next(fileIter))
	
	