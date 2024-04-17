# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: TGOODBODY
"""

import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
# https://github.com/slackapi/python-slack-sdk/issues/561

# ID of the channel you want to send the message to
def msgslack(MESSAGE = None):
    logger = logging.getLogger(__name__)
    client = WebClient(token="<YOUR_TOKEN_HERE>")
    try:
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel="#bcgovtlidar", 
            text=MESSAGE)
            
        logger.info(result)

    except SlackApiError as e:
        logger.error(f"Error posting message: {e}")



