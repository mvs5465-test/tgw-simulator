"""Simple file-based storage for network state"""
import json
import os
from pathlib import Path
from tgw_sim.models import Network, Account, VPC, TransitGateway, PrivateHostedZone

STORAGE_FILE = Path.home() / ".tgw_simulator" / "network.json"


def ensure_storage_dir():
    """Ensure storage directory exists"""
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_network(network: Network):
    """Save network state to disk"""
    ensure_storage_dir()

    data = {
        "accounts": {},
        "tgws": {},
        "zones": {},
    }

    # Save accounts and VPCs
    for acc_name, acc in network.accounts.items():
        data["accounts"][acc_name] = {
            "account_id": acc.account_id,
            "vpcs": {}
        }
        for vpc_name, vpc in acc.vpcs.items():
            data["accounts"][acc_name]["vpcs"][vpc_name] = {
                "cidr": vpc.cidr,
                "tgw_attachment": vpc.tgw_attachment
            }

    # Save TGWs and attachments
    for tgw_name, tgw in network.transit_gateways.items():
        data["tgws"][tgw_name] = {
            "account_id": tgw.account_id,
            "attachments": [],
            "routes": {}
        }
        for (acc_id, vpc_name), att in tgw.attachments.items():
            data["tgws"][tgw_name]["attachments"].append({
                "account_id": acc_id,
                "vpc_name": vpc_name,
                "cidr": att["cidr"]
            })

        # Save routes
        for cidr, targets in tgw.route_table.items():
            data["tgws"][tgw_name]["routes"][cidr] = [
                {"account_id": acc_id, "vpc_name": vpc_name}
                for acc_id, vpc_name in targets
            ]

    # Save hosted zones
    for zone_name, zone in network.hosted_zones.items():
        data["zones"][zone_name] = {
            "account_id": zone.account_id,
            "records": zone.records,
            "shared_with": list(zone.shared_with)
        }

    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_network() -> Network:
    """Load network state from disk"""
    ensure_storage_dir()

    network = Network()

    if not STORAGE_FILE.exists():
        return network

    with open(STORAGE_FILE, "r") as f:
        data = json.load(f)

    # Restore accounts and VPCs
    for acc_name, acc_data in data.get("accounts", {}).items():
        acc = network.create_account(acc_name, acc_data["account_id"])
        for vpc_name, vpc_data in acc_data.get("vpcs", {}).items():
            vpc = VPC(vpc_name, vpc_data["cidr"], acc.account_id)
            vpc.tgw_attachment = vpc_data.get("tgw_attachment")
            acc.vpcs[vpc_name] = vpc

    # Restore TGWs and attachments
    for tgw_name, tgw_data in data.get("tgws", {}).items():
        tgw = TransitGateway(tgw_name, tgw_data["account_id"])
        network.transit_gateways[tgw_name] = tgw

        # Restore attachments
        for att_data in tgw_data.get("attachments", []):
            acc_id = att_data["account_id"]
            vpc_name = att_data["vpc_name"]
            cidr = att_data["cidr"]

            # Find the VPC in accounts
            for acc in network.accounts.values():
                if acc.account_id == acc_id and vpc_name in acc.vpcs:
                    vpc = acc.vpcs[vpc_name]
                    tgw.attachments[(acc_id, vpc_name)] = {
                        "vpc": vpc,
                        "cidr": cidr,
                        "account_id": acc_id
                    }

        # Restore routes
        for cidr, targets in tgw_data.get("routes", {}).items():
            tgw.route_table[cidr] = [
                (t["account_id"], t["vpc_name"]) for t in targets
            ]

    # Restore hosted zones
    for zone_name, zone_data in data.get("zones", {}).items():
        zone = PrivateHostedZone(zone_name, zone_data["account_id"])
        zone.records = zone_data.get("records", {})
        zone.shared_with = set(zone_data.get("shared_with", []))
        network.hosted_zones[zone_name] = zone

    return network


def clear_storage():
    """Clear all stored data"""
    if STORAGE_FILE.exists():
        STORAGE_FILE.unlink()
