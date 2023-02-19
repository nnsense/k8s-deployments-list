#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=bare-except, too-many-locals, line-too-long, missing-function-docstring

import argparse
from datetime import datetime, timezone
from prettytable import PrettyTable
from kubernetes import client, config
import slack_alert

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--days", help="Set the number of days after of which a deployment will be shown by the script.", type=int)
parser.add_argument("-b", "--bot-username", help="OPTIONAL: set the bot username")
parser.add_argument("-c", "--slack-channel", help="Destination channel for slack alerts")

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

    deployments = pt_table.get_string(sortby="Owner")
    print(deployments)
    
    if args.slack_channel:
        slack_channel = args.slack_channel
    else:
        print("slack channel (-c) is required")
        exit()

    if args.bot_username:
        bot_username = args.bot_username
    else:
        bot_username = "InfraBOT"

    f = open("Test deployments older than " + str(args.days) + " days.txt", "w")
    f.write(deployments)
    f.close()

    slack_alert.upload("Test deployments older than " + str(args.days) + " days.txt", slack_channel, bot_username)

if __name__ == '__main__':
    main()
