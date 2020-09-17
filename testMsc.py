#!/bin/python3.7
# coding: utf-8

import aci.Msc
from getHosts import *
from pprint import pprint as ppr
t=aci.Msc.Msc(fabricName='bddf')

t.connect()
list_bu=t.get_backup_list()
print(t)

ppr(list_bu)