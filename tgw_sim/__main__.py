import click

@click.command()
def cli():
    """TGW Simulator - Learn AWS cross-account networking"""
    click.echo("TGW Simulator v0.1")
    click.echo("Ready to build!")

if __name__ == "__main__":
    cli()
