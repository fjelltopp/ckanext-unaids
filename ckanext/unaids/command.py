import click
from ckanext.unaids.dataset_transfer.model import init_tables, tables_exists


@click.group()
def unaids():
    '''unaids commands
    '''
    pass


@unaids.command()
@click.pass_context
def initdb(ctx):
    """Creates the necessary tables for dataset transfer in the database.
    """
    if tables_exists():
        click.secho('Dataset versions tables already exist', fg="green")
        ctx.exit(0)

    init_tables()
    click.secho('Dataset versions tables created', fg="green")


def get_commands():
    return [unaids]

