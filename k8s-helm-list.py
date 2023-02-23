#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=bare-except, too-many-locals, line-too-long, missing-function-docstring, missing-module-docstring

import argparse
import sys
import time
import base64
import json
import operator
import gzip
import re
from datetime import datetime, timezone
from prettytable import PrettyTable, MSWORD_FRIENDLY
from kubernetes import client, config
import slack_alert

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--days", help="Set the number of days after of which a deployment will be shown by the script.", type=int)
parser.add_argument("-b", "--bot-username", help="OPTIONAL: set the bot username", default="")
parser.add_argument("-c", "--slack-channel", help="Destination channel for slack alerts")

args = parser.parse_args()

def main():

    try:
        # Try to use kube/config
        config.load_kube_config()
    except:
        # Configure using cluster config
        config.load_incluster_config()

    core_client = client.CoreV1Api()

    secrets = core_client.list_secret_for_all_namespaces()

    pt_deployments = []

    for secret in secrets.items:
        if secret.type == "helm.sh/release.v1" and "operations" not in secret.metadata.namespace:
            if secret.metadata.labels['status'] == "deployed":
                helm_chart_ns = secret.metadata.namespace
                helm_chart_name = secret.metadata.labels['name']
                helm_chart_modifiedat = secret.metadata.labels['modifiedAt']
                helm_chart_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(helm_chart_modifiedat)))
                date_object = datetime.strptime(helm_chart_datetime, '%Y-%m-%d %H:%M:%S')
                stale_repo_days = (datetime.now(timezone.utc) - date_object.replace(tzinfo=timezone.utc)).days

                chart_data = json.loads(gzip.decompress(base64.b64decode(base64.b64decode(secret.data['release']))).decode("utf-8"))

                try:
                    chart_owner = chart_data['config']['global']['labels']['owner'].replace(".at.", "@")
                except:
                    chart_owner = re.search("((?:\w|\.){1,}?\.at\..*?\.com)", str(chart_data))[1].replace(".at.", "@")

                chart_name = chart_data['chart']['metadata']['name']
                version = chart_data['chart']['metadata']['version']
                chart = chart_name + "-" + version

                if args.days:
                    if stale_repo_days > args.days:
                        pt_deployments.append([helm_chart_name, helm_chart_ns, stale_repo_days, helm_chart_datetime, chart_owner, chart])
                else:
                    pt_deployments.append([helm_chart_name, helm_chart_ns, stale_repo_days, helm_chart_datetime, chart_owner, chart])

    pt_headers = ["Name", "Namespace", "DaysOld", "CreationTimestamp", "Owner", "Chart"]

    pt_table = PrettyTable(pt_headers)
    pt_table.align = "l"

    for chart in pt_deployments:
        pt_table.add_row(chart)

    pt_table.set_style(MSWORD_FRIENDLY)
    deployments = pt_table.get_string(sort_key=operator.itemgetter(5, 3), sortby="DaysOld", reversesort=True)
    
    print(deployments)

    if args.slack_channel:
        slack_channel = args.slack_channel

        bot_username = args.bot_username

        filename = "Test_deployments_older_than_" + str(args.days) + "_days.txt"

        with open(filename, 'w', encoding="utf-8") as temp_output:
            temp_output.write(deployments)

        slack_alert.upload(filename, slack_channel, bot_username)

    else:
        print("Post to slack requires a slack channel (-c)")
        sys.exit(1)

if __name__ == '__main__':
    main()
