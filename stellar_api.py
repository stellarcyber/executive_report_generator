import json
import base64
import requests
from urllib.parse import urlencode
import streamlit as st

requests.packages.urllib3.disable_warnings()

class StellarCyberAPI():

    json_headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, url, username, api_key, deployment, org_id=""):
        self.api_baseurl = f"{url}/connect/api"
        self.headers = {
            'Accept': 'application/json', 
            'Content-Type': 'application/json',
            'Authorization': self.gen_auth(url, username, api_key, deployment)
        }
        self.org_id = org_id
        self.tenant_info = []

    def getAccessToken(self, url, username, api_key):
        auth = base64.b64encode(bytes(username + ":" + api_key, "utf-8")).decode("utf-8")
        headers = {
            "Authorization": "Basic " + auth,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        req = url + "/connect/api/v1/access_token"
        print(req)
        print(headers)
        res = requests.post(req, headers=headers, verify=False)
        print("get access token res:", res.status_code)
        return res.json()["access_token"]

    def gen_auth(self, url, username, api_key, deployment):
        if deployment == "On-Prem":
            auth = base64.b64encode(bytes(username + ":" + api_key, "utf-8")).decode("utf-8")
            return "Basic " + auth
        elif deployment == "SaaS":
            token = self.getAccessToken(url, username, api_key)
            return "Bearer " + token
        else:
            raise Exception("unknown deployment: " + deployment)

    def es_search(self, index, query):
        api_url = f"{self.api_baseurl}/data/{index}/_search"
        print("send es request:", api_url, "\n", json.dumps(query))
        try:
            response = requests.get(
                api_url,
                data = json.dumps(query),
                headers = self.headers,
                verify = False
            )
            if response and response.status_code == 200:
                return response.json()
            else:
                st.error(f"ES query failed against url: {api_url}")
                return {}
                # raise RuntimeError("ES query failed:", response, api_url, query)
        except Exception as e:
            print("Send ES query error:", api_url, query)
            st.error(f"ES query failed against url: {api_url}")
            return {}

    def rest_search(self, route, params):
        api_url = f"{self.api_baseurl}/{route}?" + urlencode(params)
        print("send rest request:", api_url)
        try:
            response = requests.get(
                api_url,
                headers = self.headers,
                verify=False
            )
            if response and response.status_code == 200:
                return response.json()
            else:
                raise RuntimeError("ES query failed:", response, api_url, params)
        except Exception as e:
            print("Send ES query error:", api_url, params)
            st.error(f"Query failed against url: {api_url}")
            return {}

    def get_tenants(self):
        api_url = self.api_baseurl + "/v1/tenants"
        response = requests.get(
            api_url,
            headers=self.headers,
            verify=False,
        ).json()
        self.tenant_info = {i["cust_name"]: i for i in response["data"]}
        tenant_options = sorted([i["cust_name"] for i in response["data"]], key=str.lower)     
        return tenant_options

