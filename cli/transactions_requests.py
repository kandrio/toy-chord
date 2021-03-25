#!/usr/bin/env python3
import os
import random

host = ['192.168.0.1', '192.168.0.2', '192.168.0.3', '192.168.0.4', '192.168.0.5']
port = ["8000", '9000']

with open("../transactions/requests.txt", 'r') as file:
	line = file.readline()
	while line:
		line = line.split(', ')
		operation = line[0]
		if len(line) == 2:
			key = "\""+line[1].split('\n')[0]+"\""
		else:
			key = "\""+line[1]+"\""
		command = 'python3 cli.py '+operation+' --key '+key
		if len(line) > 2:
			value = line[2].split('\n')[0]
			command += ' --value '+value
		chosen_host = random.choice(host)
		chosen_port = random.choice(port)
		command += " --host "+chosen_host+" --port "+chosen_port
		print(command)
		os.system(command)
		line = file.readline()