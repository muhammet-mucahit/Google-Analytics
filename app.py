import flask
from flask import request, jsonify, abort

import json
import argparse

from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

import os
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

application = flask.Flask(__name__)
# application.config['DEBUG'] = True

CLIENT_SECRETS_PATH = 'client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

# Used for Analytics Api v4
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')


class SiteInformation:
    def __init__(self, account_id, prop_id, view_id, domain,
                 total_traffic, daily_traffic, start_date):
        self.account_id = account_id
        self.prop_id = prop_id
        self.view_id = view_id
        self.domain = domain
        self.total_traffic = total_traffic
        self.daily_traffic = daily_traffic
        self.start_date = start_date

    def print(self):
        print(
            'Account ID:', self.account_id,
            'Property ID:', self.prop_id,
            'View ID:', self.view_id,
            'Total Traffic:', self.total_traffic,
            'Daily Traffic:', self.daily_traffic,
            'Start Date:', self.start_date,
            'Domain:', self.domain,
        )


def get_service(api_name, api_version):
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope=SCOPES,
        message=tools.message_if_missing(CLIENT_SECRETS_PATH))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage(api_name + '.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())

    # Build the service object.
    if api_version == 'v4':
        return build(
            api_name,
            api_version,
            http=http,
            discoveryServiceUrl=DISCOVERY_URI)

    return build(
        api_name,
        api_version,
        http=http)


def get_views(service):
    profiles = service.management().profiles().list(
        accountId='~all',
        webPropertyId='~all'
    ).execute()

    site_infos = list()

    for profile in profiles.get('items', []):
        info = SiteInformation(
            profile.get('accountId'),
            profile.get('webPropertyId'),
            profile.get('id'),
            profile.get('websiteUrl'),
            0,
            0,
            profile.get('created'),
        )
        site_infos.append(info)

    return site_infos


def get_results(service, view_id, start_date, end_date, metrics, dimensions, flag):
    if not flag:
        return service.data().ga().get(
            ids='ga:' + view_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            dimensions=dimensions,
            max_results=10000).execute()

    pageToken = 0
    pageSize = 100000

    reportRequests = list()

    # Cannot be increased
    BATCH_REQUEST_LIMIT = 5

    for i in range(BATCH_REQUEST_LIMIT):
        reportRequests.append(
            {
                'viewId': view_id,
                'samplingLevel': 'SMALL',
                'dateRanges': [
                    {
                        'startDate': start_date,
                        'endDate': end_date
                    }
                ],
                'metrics': metrics,
                'dimensions': dimensions,
                'pageToken': str(pageToken),
                'pageSize': pageSize
            }
        )
        pageToken += pageSize

    return service.reports().batchGet(
        body={
            'reportRequests': reportRequests
        }
    ).execute()


@application.route('/')
def hello_whale():
    return "Hello"


@application.route('/api/v1/sites', methods=['GET'])
def get_site_list():
    service = get_service('analytics', 'v3')
    views = get_views(service)

    if not views:
        abort(400)

    DAY = '502'
    DIMENSION = 'ga:pageviews'

    for v in views:
        results = get_results(
            service,
            v.view_id,
            DAY+'daysAgo',
            'today',
            DIMENSION,
            '',
            False
        )

        total_traffic = results.get('totalsForAllResults').get(DIMENSION)
        v.total_traffic = total_traffic
        v.daily_traffic = float(total_traffic) / float(DAY)

    return jsonify([view.__dict__ for view in views]), 200


@application.route('/api/v1/site', methods=['GET'])
def get_site_data():
    body = json.loads(request.data)

    service = get_service('analytics', 'v4')

    id, start, end, metrics, dimensions = body['viewId'], \
        body['startDate'] if 'startDate' in body else '502daysAgo', \
        body['endDate'] if 'endDate' in body else 'today', \
        body['metrics'], body['dimensions']

    results = get_results(
        service,
        id,
        start,
        end,
        metrics,
        dimensions,
        True
    )

    return jsonify(results), 200


if __name__ == '__main__':
    # application.debug = True
    application.run(host='0.0.0.0', port=5000)


# VERSION 3 CODE - Maybe For Future Use

# @application.route('/api/v1/sites/<int:ver>', methods=['GET'])
# def get_site_data(ver):
#     body = json.loads(request.data)

#     if ver == 3:
#         service = get_service('analytics', 'v3')

#         metrics = ','.join([metric['expression']
#                             for metric in body['metrics']])
#         dimensions = ','.join([metric['name']
#                                for metric in body['dimensions']])
#     elif ver == 4:
#         service = get_service('analytics', 'v4')

#         metrics = body['metrics']
#         dimensions = body['dimensions']
#     else:
#         abort(400)

#     id, start, end = body['viewId'], \
#         body['startDate'] if 'startDate' in body else '502daysAgo', \
#         body['endDate'] if 'endDate' in body else 'today'

#     results = get_results(
#         service,
#         id,
#         start,
#         end,
#         metrics,
#         dimensions,
#         True if ver == 4 else False
#     )

#     return jsonify(results), 200
