#!/usr/bin/env python3

import os


def respond(http_code: int, message: str):
    return {
        "statusCode": http_code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        # this should be compatible with kaillera's get public IP button
        "body": message,
    }


def lambda_handler(event, context):
    default = 'Unable to retrieve IP'

    try:
        header = os.environ['PROXY_HEADER']
        headers = event.get('headers', {})
        headers_l = dict((k.lower(), v) for k, v in headers.items())
        ip_address = headers_l.get(header, default)

        return respond(200, ip_address)
    except Exception:
        return respond(400, default)
