import click, requests, sys

bootstrap_ip = '127.0.0.1'
bootstrap_port = '8000'
base_url = 'http://' + bootstrap_ip + ':' + bootstrap_port

@click.group()
def toychord():
    pass

@toychord.command()
@click.option('--key', required=True, type=str)
@click.option('--value', required=True, type=str)
@click.option('--host', default=bootstrap_ip, type=str)
@click.option('--port', default=bootstrap_port, type=int)
def insert(key, value, host, port):
    url = 'http://' + host + ':' + str(port) + '/insert'
    data = {
        'key' : key,
        'value' : value
    }

    r = requests.post(url, data)
    
    """
    url = 'http://' + host + ':' + str(port)  + '/insert/replicas'
    data = {
        'key' : key,
        'value' : value
    }

    r = requests.post(url, data)
    """

    if(r.status_code == 200):
        click.echo(f'The key value pair was successfully inserted!')
    else:
        click.echo(f'Something went wrong with inserting the key-value pair.')


@toychord.command()
@click.option('--key', required=True, type=str)
@click.option('--host', default=bootstrap_ip, type=str)
@click.option('--port', default=bootstrap_port, type=int)
def delete(key, host, port):
    url = 'http://' + host + ':' + str(port) + '/delete'

    data = {
        'key' : key
    }

    r = requests.post(url, data)
    """
    url = 'http://' + host + ':' + str(port) + '/delete/replicas'

    data = {
        'key' : key
    }

    r = requests.post(url, data)
    """
    click.echo(r.text)


@toychord.command()
@click.option('--key', required=True, type=str)
@click.option('--host', default=bootstrap_ip, type=str)
@click.option('--port', default=bootstrap_port, type=int)
def query(key, host, port):
    url = 'http://' + host + ':' + str(port) + '/query' 
    data = {
        'key' : key
    }

    r = requests.post(url, data)

    click.echo(r.text)


@toychord.command()
@click.option('--host', required=True, type=str)
@click.option('--port', required=True, type=int)
def depart(host, port):
    
    url = 'http://' + host + ':' + str(port) + '/node/depart'
   
    data = {
        'host' : host,
        'port' : port
    }

    r = requests.post(url, {})

    click.echo(r.text)


@toychord.command()
def overlay():
    url = base_url + '/overlay'
   
    r = requests.get(url)

    click.echo(r.text)


if __name__ == '__main__':
    toychord()
