import click, requests, sys

bootstrap_ip = '192.168.0.2'
bootstrap_port = '8000'
base_url = 'http://' + bootstrap_ip + ':' + bootstrap_port


@click.group()
def toychord():
    """CLI client for toy-chord."""
    pass


@toychord.command()
@click.option('--key', required=True, type=str)
@click.option('--value', required=True, type=str)
@click.option('--host', default=bootstrap_ip, type=str)
@click.option('--port', default=bootstrap_port, type=int)
def insert(key, value, host, port):
    """Make an insert request for a key-value pair, to a specific Node.

    NOTE: The key-value pair may not be inserted to the database
    of the Node that receives the request. It will be inserted in
    the database of the Node that is the owner of the hash ID of
    the key-value pair.
    """
    url = 'http://' + host + ':' + str(port) + '/insert'
    data = {
        'key': key,
        'value': value
    }

    r = requests.post(url, data)

    if(r.status_code == 200):
        click.echo('The key value pair was successfully inserted!')
    else:
        click.echo('Something went wrong with inserting the key-value pair.')


@toychord.command()
@click.option('--key', required=True, type=str)
@click.option('--host', default=bootstrap_ip, type=str)
@click.option('--port', default=bootstrap_port, type=int)
def delete(key, host, port):
    """Make a delete request for a key-value pair, to a specific Node.

    NOTE: The key-value pair doesn't have to be stored in the database
    of the Node that receives the request.
    """
    url = 'http://' + host + ':' + str(port) + '/delete'

    data = {
        'key': key
    }

    r = requests.post(url, data)

    click.echo(r.text)


@toychord.command()
@click.option('--key', required=True, type=str)
@click.option('--host', default=bootstrap_ip, type=str)
@click.option('--port', default=bootstrap_port, type=int)
def query(key, host, port):
    """Query for a key-value pair."""
    url = 'http://' + host + ':' + str(port) + '/query'
    data = {
        'key': key
    }

    r = requests.post(url, data)

    click.echo(r.text)


@toychord.command()
@click.option('--host', required=True, type=str)
@click.option('--port', required=True, type=int)
def depart(host, port):
    """Send a request to a specific Node to depart from toy-chord."""
    url = 'http://' + host + ':' + str(port) + '/node/depart'

    r = requests.post(url, {})

    click.echo(r.text)


@toychord.command()
def overlay():
    """Print the placement of the Nodes in toy-chord."""
    url = base_url + '/overlay'

    r = requests.get(url)

    click.echo(r.text)


if __name__ == '__main__':
    toychord()
