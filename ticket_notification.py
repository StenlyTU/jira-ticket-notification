#!/usr/bin/env python3
# pylint: disable=global-variable-undefined, line-too-long, invalid-name, broad-except

"""
Stilian Stoilov 
stenlytu@gmail.com
PyLint score - 9.86
This script is going to post into slack channel #some_name
when Team1 Component was added to already created Jira issues.
"""

import configparser
import sys
from datetime import datetime, timedelta
import requests
import urllib3
from dateutil import parser
from jira import JIRA, JIRAError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def authenticate():
    """
        This function authenticate to Jira using credentials
        stored in config.ini files.
    """
    # Open config.ini and read Jira credentials. Easier to ask for forgiveness than permission style.
    try:
        with open("/tmp/config.ini") as config_file:
            config = configparser.RawConfigParser()
            config.read_file(config_file)
    except FileNotFoundError as error:
        print(f"File config.ini is missing!\n{error}")
        return False
    except PermissionError as error:
        print(f"File config.ini cannot be open for reading!\n{error}")
        return False

    user = config["jira"]["username"]
    password = config["jira"]["Password"]

    # Authenticate to JIRA without checking Certificate.
    global jira
    try:
        jira = JIRA(basic_auth=(user, password), options={'server': 'https://JIRA_URL', 'verify': False})
        print('\033[32m➜ Jira Authentication is successful.\033[0m ')
        return True
    except JIRAError as error:
        if error.status_code == 401:
            print('Login to JIRA failed. Check your username and password. ')
        if error.status_code == 500:
            print('There is problem with the JIRA. Exiting... ')
        print(f'Failed to authenticate to https://JIRA_URL\n{error}')
        return False
    except Exception as error:
        print(f'Something weird happened.\n{error}')
        return False


def post_to_slack(message, slack_channel, emoji):
    """
        This funtion prints message to specified slack channel.

        :param message: Message which is going to be posted.
        :type message: str
        :param slack_channel: Slack channel where the message will be posted.
        :type slack_channel: str
        :param emoji: The emoi which is going to be used.
        :type emoji: str
    """

    webhook_url = 'https://hooks.slack.com/services/XXXX'
    response = requests.post(
        webhook_url, json={"text": message, "channel": slack_channel, "icon_emoji": emoji, "username": "Our Jira Integration"},
        headers={'Content-Type': 'application/json'}
    )
    response.raise_for_status()
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
    print('\033[32m➜ Posting to Slack succeeded.\033[0m')
    return True


def time_in_range(x):
    """
        This function checks if the given time is in the range (-5minutes and now)

        :param message: Time to be checked.
        :type message: datetime format.
    """
    # Calculate 6 minutes back in time and return True or False.
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=6)
    return x >= five_minutes_ago


def find_transferred_bugs():
    """
        This function is called to find issues on specific Jira queue
        which have Team1 Component added in the last 5 minutes.
    """
    # Check if authentication is successfull.
    if not authenticate():
        sys.exit(1)

    print(f'\033[36m➜ Current UTC time is: {datetime.utcnow()}\033[0m')
    try:
        # Search for Open and In Progress issues on Team1 queue without assignee.
        for issue in jira.search_issues('project=BUG and status in (open, "in progress", "author action", "reopened") and component=Team1 and assignee=empty', expand='changelog'):
            print(f'\033[36m➜ Start working on issue {issue.key} -> {issue.permalink()}\033[0m')
            # Check length of the history.
            if len(issue.changelog.histories) == 0:
                print(f"\033[91m✘ Issue {issue.key} doesn't have any history, so it will be handle by the Jira Automation. Moving to the next issue.\033[0m")
                continue
            for history in issue.changelog.histories:
                for item in history.items:
                    # Filter only relevant changes to us: Team1 Component.
                    if item.field == 'Component' and item.toString == 'Team1':
                        # Strip the last 5 characters and convert to datetime format.
                        change_time = parser.parse(history.created[:-5])

                        # If Team1 Component was added 5 minutes ago post to Slack.
                        if time_in_range(change_time) is True:
                            print(f'\033[32m➜ Component Team1 was added at {history.created[:-5]}, so post to Slack the following:\033[0m')
                            slack_text = f'There is a new `{issue.fields.priority}` issue with status `{issue.fields.status}` `{issue.fields.summary}` -> {issue.permalink()}'
                            print(f'\033[32m➜ {slack_text} \033[0m')
                            post_to_slack(slack_text, "#some_name", ":bell:")
                        else:
                            print(f'\033[91m✘ Team1 was added at {history.created[:-5]} UTC. Not relevant to the current time. Moving to the next.\033[0m')
    except JIRAError as error:
        sys.exit(f"\033[91m✘ There is problem with the Jira search.\033[0m \n{error}")
    finally:
        print("\033[32m➜ Done!\033[0m")

if __name__ == '__main__':
    find_transferred_bugs()
