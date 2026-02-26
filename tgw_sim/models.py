"""Core data models for the simulator"""

class VPC:
    """Represents an AWS VPC"""
    def __init__(self, name: str, cidr: str, account_id: str):
        self.name = name
        self.cidr = cidr
        self.account_id = account_id
        self.tgw_attachment = None  # Will be set when attached to TGW

    def attach_to_tgw(self, tgw_id: str):
        """Attach this VPC to a Transit Gateway"""
        self.tgw_attachment = tgw_id

    def __repr__(self):
        status = "attached" if self.tgw_attachment else "detached"
        return f"VPC({self.name}, {self.cidr}, {status})"


class Account:
    """Represents an AWS Account"""
    def __init__(self, name: str, account_id: str):
        self.name = name
        self.account_id = account_id
        self.vpcs = {}  # name -> VPC

    def create_vpc(self, vpc_name: str, cidr: str) -> VPC:
        """Create a VPC in this account"""
        if vpc_name in self.vpcs:
            raise ValueError(f"VPC {vpc_name} already exists in {self.name}")

        vpc = VPC(vpc_name, cidr, self.account_id)
        self.vpcs[vpc_name] = vpc
        return vpc

    def get_vpc(self, vpc_name: str) -> VPC:
        """Get a VPC by name"""
        return self.vpcs.get(vpc_name)

    def __repr__(self):
        return f"Account({self.name}, {len(self.vpcs)} VPCs)"


class TransitGateway:
    """Represents an AWS Transit Gateway"""
    def __init__(self, name: str, account_id: str):
        self.name = name
        self.account_id = account_id  # Account that owns the TGW
        self.attachments = {}  # (account_id, vpc_name) -> attachment info
        self.route_table = {}  # destination_cidr -> [(account_id, vpc_name), ...]

    def attach_vpc(self, account_id: str, vpc: VPC) -> bool:
        """Attach a VPC to this TGW"""
        key = (account_id, vpc.name)
        if key in self.attachments:
            raise ValueError(f"VPC {vpc.name} already attached from {account_id}")

        vpc.attach_to_tgw(self.name)
        self.attachments[key] = {
            "vpc": vpc,
            "cidr": vpc.cidr,
            "account_id": account_id
        }

        # Add route for this VPC's CIDR
        if vpc.cidr not in self.route_table:
            self.route_table[vpc.cidr] = []
        self.route_table[vpc.cidr].append(key)

        return True

    def get_route(self, destination_cidr: str) -> list:
        """Get the route for a destination CIDR"""
        return self.route_table.get(destination_cidr, [])

    def list_attachments(self) -> list:
        """List all attachments"""
        return list(self.attachments.values())

    def __repr__(self):
        return f"TransitGateway({self.name}, {len(self.attachments)} attachments)"


class Network:
    """Represents the entire simulated network"""
    def __init__(self):
        self.accounts = {}  # account_name -> Account
        self.transit_gateways = {}  # tgw_name -> TransitGateway

    def create_account(self, name: str, account_id: str) -> Account:
        """Create an account"""
        if name in self.accounts:
            raise ValueError(f"Account {name} already exists")

        account = Account(name, account_id)
        self.accounts[name] = account
        return account

    def get_account(self, name: str) -> Account:
        """Get an account by name"""
        return self.accounts.get(name)

    def create_transit_gateway(self, name: str, owner_account: str) -> TransitGateway:
        """Create a Transit Gateway owned by an account"""
        if name in self.transit_gateways:
            raise ValueError(f"TGW {name} already exists")

        account = self.get_account(owner_account)
        if not account:
            raise ValueError(f"Account {owner_account} not found")

        tgw = TransitGateway(name, account.account_id)
        self.transit_gateways[name] = tgw
        return tgw

    def get_transit_gateway(self, name: str) -> TransitGateway:
        """Get a TGW by name"""
        return self.transit_gateways.get(name)

    def __repr__(self):
        return f"Network({len(self.accounts)} accounts, {len(self.transit_gateways)} TGWs)"
