#!/usr/bin/python3

import os
import sys
import argparse
import base64
from kubernetes import client, config
from slack import WebClient # pip3 install slackclient
from slack.errors import SlackApiError

try:
    # Try to use kube/config
    config.load_kube_config()
except:
    # Configure using cluster config
    config.load_incluster_config()

v1 = client.CoreV1Api()
secret = (v1.read_namespaced_secret("slack-token", "default")).data['token']
slack_token = base64.b64decode(secret).decode('utf-8').rstrip()

def post(slack_message, slack_channel, bot_username):

    response = { 'ok': False }
    
    slack_message = "```" + slack_message + "```"
    
    client = WebClient(token=slack_token)
    
    print("Posting new message to: " + slack_channel )
    
    try:
        response = client.chat_postMessage(
                          channel = slack_channel,
                          text = slack_message,
                          username = bot_username,
                          blocks = [{
                                      "type": "section",
                                      "text": {
                                              "type": "mrkdwn",
                                              "text": slack_message
                                              }
                                    }]
                          ) 


    except SlackApiError as e:
      assert e.response["error"]
      print(e)
      exit()

    if response.get('ok') == True:
        print("Message sent")

def upload(file_path, slack_channel, bot_username):

    response = { 'ok': False }
    
    client = WebClient(token=slack_token)
    
    print("Posting new message to: " + slack_channel )

    try:
        response = client.files_upload(
                    channels = slack_channel,
                    file = file_path,
                    username = bot_username
                    )


    except SlackApiError as e:
      assert e.response["error"]
      print(e)
      exit()

    if response.get('ok') == True:
        print("Message sent")

