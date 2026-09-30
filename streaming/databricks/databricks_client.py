"""
Databricks REST API Client for AromaBank Pipeline Automation.
Allows testing connections, listing clusters, and submitting Databricks jobs
using Databricks Personal Access Token (PAT).
"""
import os
import sys
import argparse
import requests
def _load_env():
    cur = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.abspath(os.path.join(cur, "..", "..", ".env")),
        os.path.abspath(os.path.join(cur, ".env")),
    ]
    for p in candidates:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"\''))
            break

_load_env()
DEFAULT_TOKEN = os.getenv("DATABRICKS_TOKEN", "")


class DatabricksClient:
    def __init__(self, host: str, token: str):
        # Normalize host URL
        self.host = host.rstrip("/")
        if not self.host.startswith("http"):
            self.host = f"https://{self.host}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def list_clusters(self):
        url = f"{self.host}/api/2.0/clusters/list"
        resp = requests.get(url, headers=self.headers, timeout=10)
        return resp.json()

    def list_jobs(self):
        url = f"{self.host}/api/2.1/jobs/list"
        resp = requests.get(url, headers=self.headers, timeout=10)
        return resp.json()

    def current_user(self):
        url = f"{self.host}/api/2.0/preview/scim/v2/Me"
        resp = requests.get(url, headers=self.headers, timeout=10)
        return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Databricks Automation CLI")
    parser.add_argument("--host", default=os.getenv("DATABRICKS_HOST", "https://community.cloud.databricks.com"),
                        help="Databricks workspace URL (e.g. https://community.cloud.databricks.com or https://adb-xxx.azuredatabricks.net)")
    parser.add_argument("--token", default=os.getenv("DATABRICKS_TOKEN", DEFAULT_TOKEN),
                        help="Databricks Personal Access Token")
    parser.add_argument("--action", choices=["test-connection", "list-clusters", "list-jobs"], default="test-connection")
    args = parser.parse_args()

    client = DatabricksClient(args.host, args.token)
    print(f"Connecting to Databricks Workspace: {args.host}")

    try:
        if args.action == "test-connection":
            user_info = client.current_user()
            print("✔ Connected to Databricks API successfully!")
            print(f"User / Identity: {user_info.get('userName', user_info)}")
        elif args.action == "list-clusters":
            clusters = client.list_clusters()
            print("Clusters:")
            print(clusters)
        elif args.action == "list-jobs":
            jobs = client.list_jobs()
            print("Jobs:")
            print(jobs)
    except Exception as e:
        print(f"Error communicating with Databricks API: {e}")


if __name__ == "__main__":
    main()
