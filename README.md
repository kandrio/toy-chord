# Toy-chord

## Install Dependencies

cd toy-chord
python3 -m pip install -r requirements.txt

## CLI Client

### List CLI commands:

    cd cli
    python3 cli.py --help

### See how a command works:

    python3 cli.py [command] --help

### Run a CLI command:

    python3 cli.py [command] [arguments]


## Node Server

### Run the Bootstrap Node

    cd backend
    python3 server.py --is_bootstrap

### Run a Regular Node

    cd backend 
    python3 server.py --host "host" --port "port"

