#!/usr/bin/env python3.7
# coding: utf-8

import argparse
import pdb
import yaml
from ruamel.yaml import YAML
import ruamel.yaml
import sys


from pprint import pprint
from copy import deepcopy
import os

class Loader__(yaml.SafeLoader):
	def __init__(self, stream):
		self._root = os.path.split(stream.name)[0]
		super(Loader__, self).__init__(stream)

	def include(self, node):
		filename = os.path.join(self._root, self.construct_scalar(node))
		with open(filename, 'r') as f:
			return yaml.load(f)

Loader__.add_constructor('!include', Loader__.include)


if __name__ == '__main__':
	"Fonction principale"
	parser = argparse.ArgumentParser()
	
	parser.add_argument('file_yml')
	args = parser.parse_args()
	
	print("load yaml:")
	with open(args.file_yml, 'r') as yml__:
		try:
			yaml_obj = yaml.load(yml__,Loader=yaml.SafeLoader)
		except yaml.constructor.ConstructorError as E:
			print(E)
			yaml_obj = yaml.load(yml__,Loader__)
			
	pdb.set_trace()
	pprint(yaml_obj)


	ruyaml=YAML()
	ruyaml.default_flow_style = None
	ruyaml.preserves_quotes=True
	ruyaml.width = 4096
	ruyaml.indent(mapping=2,sequence=3, offset=3)
	print("load ruamel.yaml:")
	with open(args.file_yml, 'r') as yml__:
		try:
			yaml_obj2 = ruyaml.load(yml__)
		except yaml.constructor.ConstructorError as E:
			print(E)

	pprint(yaml_obj2)		
	
	pdb.set_trace()
	

	
	with open(args.file_yml, 'r') as yml__:
		try:
			yaml_obj3 = ruamel.yaml.round_trip_load(yml__.read())
		except yaml.constructor.ConstructorError as E:
			print(E)
	yaml_obj3['toto']='TITI'
	pdb.set_trace()
	yaml_obj3['CLOUD']['DC2']['DC2A3-CLOUD-CFD-VDC2'][2]["fabricpath"]=[{'a':1} ,{'b':2}]
	ruamel.yaml.round_trip_dump(yaml_obj3, sys.stdout)
	pdb.set_trace()
	pprint(yaml_obj3)	
