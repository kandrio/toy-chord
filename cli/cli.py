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
def insert(key, value):
    url = base_url + '/insert'
    
    data = {
        'key' : key,
        'value' : value
    }

    r = requests.post(url, data)

    if(r.status_code == 200):
        click.echo(f'The key value pair was inserted!')
    else:
        click.echo(f'Something went wrong.')

@toychord.command()
@click.option('--key', required=True, type=str)
def delete(key):
    url = base_url + '/delete'

    data = {
        'key' : key
    }

    r = requests.post(url, data)

    click.echo(r.text)

@toychord.command()
@click.option('--key', required=True, type=str)
def query(key):
    
    url = base_url + '/query/' + key 

    r = requests.get(url)

    if(r.status_code == 200):
        click.echo(r.text)
    else:
        click.echo("That song doesn't exist.")


@toychord.command()
@click.option('--nodekey', required=True, type=str)
def depart(nodekey):
    url = base_url + '/depart'
   
    data = {
        'nodekey' : nodekey
    }

    r = requests.post(url, data=data)

    if(r.status_code == 200):
        click.echo(f'The node has departed.')
    else:
        click.echo(f'Something went wrong.')

@toychord.command()
def overlay():
    url = base_url + '/overlay'
   
    r = requests.get(url, data=data)

    if(r.status_code == 200):
        click.echo(f'{r.content}')
    else:
        click.echo(f'Something went wrong.')

if __name__ == '__main__':

    toychord()