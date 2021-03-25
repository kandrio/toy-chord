#!/usr/bin/env python3
import os
import random

host = ['192.168.0.1', '192.168.0.2', '192.168.0.3', '192.168.0.4', '192.168.0.5']
port = ["8000", '9000']

with open ("transactions_requests.sh", 'w') as shell:
	with open("../transactions/requests.txt", 'r') as file:
		line = file.readline()
		while line:
			chosen_host = random.choice(host)
			chosen_port = random.choice(port)
			line = line.split(', ')
			operation = line[0]
			if len(line) == 2:
				key = line[1].split('\n')[0]
				shell.write("curl -X POST -F \"key="+key+"\" http://"+chosen_host+':'+chosen_port+'/query\n')
			else:
				key = line[1]
				value = line[2].split('\n')[0]
				shell.write("curl -X POST -F \"key="+key+"\" -F \"value="+value+"\" http://"+chosen_host+':'+chosen_port+'/insert\n')
			line = file.readline()