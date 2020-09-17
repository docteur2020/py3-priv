import sys
import os


if os.isatty(0):
	with open(sys.argv[1],'r') as file:
		for line in file:
			print("no "+line)
else:
	for line in sys.stdin:
		print("no "+line)