#!/usr/bin/env python3.7
# coding: utf-8

import pdb


class A:
	def __init__(self):
		self.value='A'
		
	def __str__(self):	
		return self.value
		
	def __repr__(self):	
		return self.value
		

class B:
	def __str__(self):
		a=A()
		return a.__str__()


def test_deco(f):
	
	def init(self):
		self.value='C'
	
	def wrapper__(*args, **kwargs):

		A.__init__=init
		return f(*args, **kwargs)
	return wrapper__

@test_deco
def call_class():

	obj=B()
	print(obj)
	


call_class()
