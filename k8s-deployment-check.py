#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=bare-except, too-many-locals, line-too-long, missing-function-docstring

import argparse
from datetime import datetime, timezone
from prettytable import PrettyTable
from kubernetes import client, config

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--days", help="Set the number of days after of which a deployment will be shown by the script.", type=int)

args = parser.parse_args()

def main():

    try:
        # Try to use kube/config
        config.load_kube_config()
    except:
        # Configure using cluster config
        config.load_incluster_config()

    apps_client = client.AppsV1Api()

    deployments = apps_client.list_deployment_for_all_namespaces(watch=False)

    pt_deployments = []

    for deployment in deployments.items:
        if "owner" in deployment.metadata.labels:
            creation_timestamp = deployment.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            owner = (deployment.metadata.labels['owner']).replace(".at.", "@")

            stale_repo_days = (datetime.now(timezone.utc) - deployment.metadata.creation_timestamp.replace(tzinfo=timezone.utc)).days

            if args.days:
                if stale_repo_days > args.days:
                    pt_deployments.append([deployment.metadata.name, deployment.metadata.namespace, stale_repo_days, creation_timestamp, owner])
            else:
                pt_deployments.append([deployment.metadata.name, deployment.metadata.namespace, stale_repo_days, creation_timestamp, owner])

    pt_headers = ["Name", "Namespace", "DaysOld", "CreationTimestamp", "Owner"]

    pt_table = PrettyTable(pt_headers)
    pt_table.align = "l"

    for item in pt_deployments:
        pt_table.add_row(item)

    print(pt_table.get_string(sortby="Owner"))


if __name__ == '__main__':
    main()
