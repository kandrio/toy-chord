#!/usr/bin/env python3

import os
import random

host = ['192.168.0.1', '192.168.0.2', '192.168.0.3', '192.168.0.4', '192.168.0.5']
port = ["8000", '9000']

with open ("transactions_query.sh", 'w') as shell:
	with open("../transactions/query.txt", 'r') as file:
		line = file.readline()
		while line:
			line = line.split('\n')
			name = line[0]
			chosen_host = random.choice(host)
			chosen_port = random.choice(port)
			shell.write("curl -X POST -F \"key="+name+"\" http://"+chosen_host+':'+chosen_port+'/query\n')
			line = file.readline()