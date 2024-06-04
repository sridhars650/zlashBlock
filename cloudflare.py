from typing import List
import requests
import logging
import os

logger = logging.getLogger("cloudflare")


from dotenv import load_dotenv
load_dotenv()

CF_IDENTIFIER="2c8a885b3ceb38485393b1fa4c3604ca"
CF_API_TOKEN="z__PUJZfA8sHfauYi-ySY78g5lwx6j0rqdEbtgLa"
if not CF_API_TOKEN or not CF_IDENTIFIER:
    raise Exception("Missing Cloudflare credentials")

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {CF_API_TOKEN}"})


def get_lists(name_prefix: str):
    r = session.get(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/lists",
    )

    logger.debug(f"[get_lists] {r.status_code}")

    if r.status_code != 200:
        raise Exception("Failed to get Cloudflare lists")

    lists = r.json()["result"] or []

    return [l for l in lists if l["name"].startswith(name_prefix)]


def create_list(name: str, domains: List[str]):
    r = session.post(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/lists",
        json={
            "name": name,
            "description": "Created by script.",
            "type": "DOMAIN",
            "items": [*map(lambda d: {"value": d}, domains)],
        },
    )

    logger.debug(f"[create_list] {r.status_code}")

    if r.status_code != 200:
        raise Exception("Failed to create Cloudflare list: " + str(r.content))
    print ("Created list " + name)
    return r.json()["result"]


def delete_list(list_id: str):
    r = session.delete(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/lists/{list_id}",
    )

    logger.debug(f"[delete_list] {r.status_code}")
    if r.status_code != 200:
        raise Exception("Failed to delete Cloudflare list: " + str(r.content))

    return r.json()["result"]


def get_firewall_policies(name_prefix: str):
    r = session.get(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/rules",
    )

    logger.debug(f"[get_firewall_policies] {r.status_code}")

    if r.status_code != 200:
        raise Exception("Failed to get Cloudflare firewall policies")

    lists = r.json()["result"] or []

    return [l for l in lists if l["name"].startswith(name_prefix)]

def delete_firewall_policy(policy_id: str):
    r = session.delete(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/rules/{policy_id}",
    )

    logger.debug(f"[delete_policy] {r.status_code}")

    if r.status_code != 200:
        raise Exception("Failed to delete Cloudflare policy")

    return r.json()["result"]


def create_gateway_policy(name: str, list_ids: List[str]):
    r = session.post(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/rules",
        json={
            "name": name,
            "description": "Created by script.",
            "action": "block",
            "enabled": True,
            "filters": ["dns"],
            "traffic": "or".join([f"any(dns.domains[*] in ${l})" for l in list_ids]),
            "rule_settings": {
                "block_page_enabled": False,
            },
        },
    )

    logger.debug(f"[create_gateway_policy] {r.status_code}")

    if r.status_code != 200:
        raise Exception("Failed to create Cloudflare firewall policy")

    return r.json()["result"]


def update_gateway_policy(name: str, policy_id: str, list_ids: List[str]):
    r = session.put(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway/rules/{policy_id}",
        json={
            "name": name,
            "action": "block",
            "enabled": True,
            "traffic": "or".join([f"any(dns.domains[*] in ${l})" for l in list_ids]),
        },
    )

    logger.debug(f"[update_gateway_policy] {r.status_code}")

    if r.status_code != 200:
        raise Exception("Failed to update Cloudflare firewall policy")

    return r.json()["result"]
