#!/usr/bin/env python3

import json
import socket
import kaillera.client as Kaillera


def respond(http_code: int, success: bool, message: str):
    return {
        "statusCode": http_code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "body": json.dumps({
            "message": message,
            "success": success,
        }),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        client = Kaillera.Client(body['host'], int(body['port']))
    except socket.error:
        return respond(400, False, "Unable to connect")
    except Exception:
        return respond(400, False, "Invalid parameters")

    try:
        latency, drops = client.ping(3)
    except Exception as e:
        return respond(200, False, "Unable to connect")

    return respond(200, True, f"{latency}ms")
