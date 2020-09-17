#!/usr/bin/env python3.7
# coding: utf-8



import re
import os
import argparse
import pdb

TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + list(range(0x20, 0x100))))
is_binary_string = lambda bytes: bool(bytes.translate(TEXTCHARS))

if __name__ == '__main__':
	parser = argparse.ArgumentParser('pygrep')
	parser.add_argument('-d', '--directory', type=str, required=False,
						default='.', help='root directory to search')
	parser.add_argument('pattern', type=str, help='search pattern')
	parser.add_argument('-s', '--silent',action="store_true", help='silent mode')
	parser.add_argument('-i', '--ignore-case', dest='ignorecase' ,action="store_true", help='silent mode')
	args = parser.parse_args()
	if args.ignorecase:
		pattern = re.compile(args.pattern, re.IGNORECASE)
	else:
		pattern = re.compile(args.pattern)
	for path, _, files in os.walk(args.directory):
		for fn in files:
			filepath = os.path.join(path, fn)
			try:
				with open(filepath) as handle:
					try:
						for lineno, line in enumerate(handle):
							mo = pattern.search(line)
							if mo:
								print("%s:%s: %s" % (filepath, lineno,
									line.strip().replace(mo.group(), "\033[92m%s\033[0m"%
										mo.group())))
					except UnicodeDecodeError:
						if not args.silent:
							print("Fichier non traité:"+ handle.name)
						pass
			except PermissionError as e:
				if not args.silent:
					print("Fichier non traité,raison:"+str(e))
				pass
			except FileNotFoundError as e:
				if not args.silent:
					print("Fichier non traité,raison:"+str(e))
				pass

