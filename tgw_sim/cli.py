"""CLI commands for the simulator"""
import click
from tgw_sim.models import Network
from tgw_sim.storage import load_network, save_network

# Load network state on startup
network = load_network()


@click.group()
def cli():
    """TGW Simulator - Learn AWS cross-account networking"""
    pass


@cli.group()
def account():
    """Manage accounts"""
    pass


@account.command()
@click.argument("name")
@click.argument("account_id")
def create(name, account_id):
    """Create a new account"""
    try:
        acc = network.create_account(name, account_id)
        save_network(network)
        click.echo(f"✓ Created account: {acc}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@account.command()
def list():
    """List all accounts"""
    if not network.accounts:
        click.echo("No accounts yet")
        return

    for name, acc in network.accounts.items():
        click.echo(f"  {acc.name} ({acc.account_id})")
        for vpc_name, vpc in acc.vpcs.items():
            click.echo(f"    └─ {vpc}")


@cli.group()
def vpc():
    """Manage VPCs"""
    pass


@vpc.command()
@click.argument("account_name")
@click.argument("vpc_name")
@click.argument("cidr")
def create(account_name, vpc_name, cidr):
    """Create a VPC in an account"""
    try:
        acc = network.get_account(account_name)
        if not acc:
            raise ValueError(f"Account {account_name} not found")

        vpc_obj = acc.create_vpc(vpc_name, cidr)
        save_network(network)
        click.echo(f"✓ Created VPC: {vpc_obj}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@vpc.command()
@click.argument("account_name")
def list(account_name):
    """List VPCs in an account"""
    acc = network.get_account(account_name)
    if not acc:
        click.echo(f"✗ Account {account_name} not found", err=True)
        return

    if not acc.vpcs:
        click.echo(f"No VPCs in {account_name}")
        return

    for name, vpc in acc.vpcs.items():
        click.echo(f"  {vpc}")


@cli.group()
def tgw():
    """Manage Transit Gateways"""
    pass


@tgw.command()
@click.argument("name")
@click.argument("owner_account")
def create(name, owner_account):
    """Create a Transit Gateway owned by an account"""
    try:
        tgw_obj = network.create_transit_gateway(name, owner_account)
        save_network(network)
        click.echo(f"✓ Created TGW: {tgw_obj}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@tgw.command()
@click.argument("tgw_name")
@click.argument("account_name")
@click.argument("vpc_name")
def attach(tgw_name, account_name, vpc_name):
    """Attach a VPC to a Transit Gateway"""
    try:
        tgw_obj = network.get_transit_gateway(tgw_name)
        if not tgw_obj:
            raise ValueError(f"TGW {tgw_name} not found")

        acc = network.get_account(account_name)
        if not acc:
            raise ValueError(f"Account {account_name} not found")

        vpc_obj = acc.get_vpc(vpc_name)
        if not vpc_obj:
            raise ValueError(f"VPC {vpc_name} not found in {account_name}")

        tgw_obj.attach_vpc(acc.account_id, vpc_obj)
        save_network(network)
        click.echo(f"✓ Attached {account_name}/{vpc_name} to {tgw_name}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@tgw.command()
@click.argument("tgw_name")
def list(tgw_name):
    """List attachments for a TGW"""
    tgw_obj = network.get_transit_gateway(tgw_name)
    if not tgw_obj:
        click.echo(f"✗ TGW {tgw_name} not found", err=True)
        return

    attachments = tgw_obj.list_attachments()
    if not attachments:
        click.echo(f"No attachments on {tgw_name}")
        return

    click.echo(f"{tgw_name} attachments:")
    for att in attachments:
        click.echo(f"  {att['account_id']}/{att['vpc'].name} ({att['cidr']})")


@cli.command()
def status():
    """Show network status"""
    click.echo(f"Network: {network}")
    click.echo()
    click.echo(f"Accounts: {len(network.accounts)}")
    for name, acc in network.accounts.items():
        click.echo(f"  {acc}")
    click.echo()
    click.echo(f"Transit Gateways: {len(network.transit_gateways)}")
    for name, tgw in network.transit_gateways.items():
        click.echo(f"  {tgw}")
