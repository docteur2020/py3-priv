#!/usr/bin/env python3.7
# coding: utf-8

import pdb

def test_deco(f):
	def wrapper(*args, **kwargs):
		if args[0]==args[1]:
			return 1000+f(*args, **kwargs)
		return f(*args, **kwargs)
	return wrapper

@test_deco
def somme(a,b):
	return a+b
	
	
res=somme(5,5)
print(f'resultat:{res}')