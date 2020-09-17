#!/usr/bin/env python3.7
# coding: utf-8

from __future__ import unicode_literals



import argparse
from pprint import pprint
import pdb
import re
import sys



	
if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('csv1',help="1st File that contains route")
	parser.add_argument('csv2',help="1st File that contains route")
	parser.add_argument("-x", "--xlsx", action="store",help="Excel file result",required=True)
	
	args = parser.parse_args()

	
