import os
import json
from pathlib import Path
import requests
from datetime import datetime
from collections import defaultdict

requests.packages.urllib3.disable_warnings()

aps_host = os.environ.get("APS_HOST", "apsdev.stellarcyber.ai")
baseurl = f"https://{aps_host}/acgs/api/v2/organization_usage/"

headers = {'Accept': 'application/json'}
parent_dir = Path(__file__).parent.parent.absolute()
cert = (os.path.join(parent_dir, "cluster-controller.crt"), 
        os.path.join(parent_dir, "cluster-controller.key"))

def get_org_usage(org_id, start_date, end_date, license_type="volume"):
    url = baseurl + org_id
    params = {'start': f"{start_date}T00:00:00Z",
              'end': f"{end_date}T23:59:59Z",
              'license_type': license_type,
              'include_tenant': "true"}
    resp = requests.get(url,
                        headers = headers,
                        params = params,
                        cert = cert,
                        verify = False)
    return resp.json()

def get_saas_tenant_id_from_name(org_id, start_date, end_date, tenant_name):
    data = get_org_usage(org_id, start_date, end_date)
    for entry in data["data"]["entries"]:
        for saas in entry["saas"]["entries"]:
            for tenant in saas["tenants"]:                
                if tenant_name == tenant["tenant_name"]:
                    return tenant["tenantid"]
    raise Exception("Cannot find Tenant Id for", tenant_name)

def get_saas_tenant_names(org_id, start_date, end_date):
    data = get_org_usage(org_id, start_date, end_date)
    all_tenant_names = set()
    for entry in data["data"]["entries"]:
        for saas in entry["saas"]["entries"]:
            for tenant in saas["tenants"]:                
                tenant_name = tenant["tenant_name"]
                all_tenant_names.add(tenant_name)
    return list(all_tenant_names)

def get_daily_usage(org_id, start_date, end_date, license_type):
    data = get_org_usage(org_id, start_date, end_date, license_type)
    usage_by_date = defaultdict(lambda: defaultdict(dict))
    usage_by_tenant = defaultdict(lambda: defaultdict(dict))
    for entry in data["data"]["entries"]:
        timestamp = datetime.fromtimestamp(entry['timestamp']/1000)
        date = timestamp.strftime("%Y-%m-%d")
        for saas in entry["saas"]["entries"]:
            for tenant in saas["tenants"]:
                usage_by_date[date][tenant["tenant_name"]] = tenant["usage"]
                usage_by_tenant[tenant["tenant_name"]][date] = tenant["usage"]
    return {"by_date": json.loads(json.dumps(usage_by_date)),
            "by_tenant": json.loads(json.dumps(usage_by_tenant))}

def get_volume_usage(org_id, start_date, end_date):
    return get_daily_usage(org_id, start_date, end_date, "volume")

def get_asset_usage(org_id, start_date, end_date):
    return get_daily_usage(org_id, start_date, end_date, "asset")


if  __name__ == "__main__":
    get_asset_usage("695eb0b8a92946619f87d7c4c527ceac", "2023-01-01", "2023-01-31") 
    #get_asset_usage("b86e449dbda34826ac7e82e7bce208fa", "2023-01-01", "2023-01-31") 
