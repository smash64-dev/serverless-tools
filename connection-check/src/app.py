#!/usr/bin/env python3

import json
import socket
import kaillera.client as Kaillera


def respond(http_code: int, success: bool, message: str):
    return {
        "statusCode": http_code,
        "body": json.dumps({
            "message": message,
            "success": success,
        }),
    }


def server_check(event, context):
    try:
        body = json.loads(event['body'])
        client = Kaillera.Client(body['host'], int(body['port']))
    except socket.error:
        return respond(400, False, "Unable to connect")
    except Exception:
        return respond(400, False, "Invalid parameters")

    try:
        client.ping(3)
    except ConnectionRefusedError as e:
        return respond(200, False, "Unable to connect")

    return respond(200, True, "Connection successful")
