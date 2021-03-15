#!/usr/bin/env python3

import os

with open("../transactions/insert.txt", 'r') as file:
	line = file.readline()
	while line:
		line = line.split(',')
		name = "\""+line[0]+"\""
		value = line[1].split('\n')[0].split(' ')[1]
		os.system('python3 cli.py insert --key '+name+' --value '+value)
		line = file.readline()