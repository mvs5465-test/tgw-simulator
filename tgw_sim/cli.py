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


@cli.group()
def zone():
    """Manage Private Hosted Zones (DNS)"""
    pass


@zone.command()
@click.argument("zone_name")
@click.argument("owner_account")
def create(zone_name, owner_account):
    """Create a Private Hosted Zone owned by an account"""
    try:
        zone = network.create_hosted_zone(zone_name, owner_account)
        save_network(network)
        click.echo(f"✓ Created zone: {zone}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@zone.command(name="add-record")
@click.argument("zone_name")
@click.argument("hostname")
@click.argument("ip")
def add_record(zone_name, hostname, ip):
    """Add a DNS record to a zone"""
    try:
        zone = network.get_hosted_zone(zone_name)
        if not zone:
            raise ValueError(f"Zone {zone_name} not found")

        zone.add_record(hostname, ip)
        save_network(network)
        click.echo(f"✓ Added record: {hostname}.{zone_name} -> {ip}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@zone.command()
@click.argument("zone_name")
@click.argument("requester_account")
def list(zone_name, requester_account):
    """List DNS records in a zone (if requester can access)"""
    try:
        zone = network.get_hosted_zone(zone_name)
        if not zone:
            raise ValueError(f"Zone {zone_name} not found")

        acc = network.get_account(requester_account)
        if not acc:
            raise ValueError(f"Account {requester_account} not found")

        if not zone.can_query(acc.account_id):
            raise ValueError(f"Account {requester_account} cannot access zone {zone_name}")

        if not zone.records:
            click.echo(f"No records in {zone_name}")
            return

        click.echo(f"Records in {zone_name}:")
        for hostname, ip in zone.records.items():
            click.echo(f"  {hostname}.{zone_name} -> {ip}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@zone.command()
@click.argument("zone_name")
@click.argument("target_account")
def share(zone_name, target_account):
    """Share a zone with another account"""
    try:
        zone = network.get_hosted_zone(zone_name)
        if not zone:
            raise ValueError(f"Zone {zone_name} not found")

        target = network.get_account(target_account)
        if not target:
            raise ValueError(f"Account {target_account} not found")

        zone.share_with_account(target.account_id)
        save_network(network)
        click.echo(f"✓ Shared {zone_name} with {target_account}")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command(name="query-dns")
@click.argument("hostname")
@click.argument("zone_name")
@click.argument("requester_account")
def query_dns(hostname, zone_name, requester_account):
    """Query a DNS record (simulates resolver lookup)"""
    try:
        acc = network.get_account(requester_account)
        if not acc:
            raise ValueError(f"Account {requester_account} not found")

        ip = network.resolve_dns(hostname, zone_name, acc.account_id)
        if ip:
            click.echo(f"✓ {hostname}.{zone_name} -> {ip}")
        else:
            click.echo(f"✗ Cannot resolve {hostname}.{zone_name} (access denied or not found)")
    except ValueError as e:
        click.echo(f"✗ Error: {e}", err=True)


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
    click.echo()
    click.echo(f"Hosted Zones: {len(network.hosted_zones)}")
    for name, zone in network.hosted_zones.items():
        click.echo(f"  {zone}")
