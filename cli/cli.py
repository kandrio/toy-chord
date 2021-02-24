import click, requests

base_url = 'http://localhost:8080'

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

    if(r.status_code == 200):
        click.echo(f'The key was succesfully deleted')
    else:
        click.echo(f'Something went wrong.')

@toychord.command()
@click.option('--key', required=True, type=str)
def query(key):
    url = base_url + '/query'

    r = requests.get(url)

    if(r.status_code == 200):
        click.echo(f{r.content})
    else:
        click.echo(f'Something went wrong.')

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
        click.echo(f{r.content})
    else:
        click.echo(f'Something went wrong.')

if __name__ == '__main__':
    toychord()