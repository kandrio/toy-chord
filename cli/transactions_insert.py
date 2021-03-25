#!/usr/bin/env python3

import os
import random

host = ['192.168.0.1', '192.168.0.2', '192.168.0.3', '192.168.0.4', '192.168.0.5']
port = ["8000", '9000']

with open("../transactions/insert.txt", 'r') as file:
	line = file.readline()
	while line:
		line = line.split(',')
		name = "\""+line[0]+"\""
		value = line[1].split('\n')[0].split(' ')[1]
		chosen_host = random.choice(host)
		chosen_port = random.choice(port)
		os.system('python3 cli.py insert --key '+name+' --value '+value+" --host "+chosen_host+" --port "+chosen_port)
		line = file.readline()