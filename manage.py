import click
from flask.cli import FlaskGroup
from app import create_app
from scripts.process_payouts import process_payouts

# Create an application instance
# app = create_app() # No longer needed here, FlaskGroup handles it

@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """
    Main entry point for Flask CLI commands.
    """
    pass

# Register commands
cli.add_command(process_payouts, name='process-payouts')

if __name__ == '__main__':
    cli() 