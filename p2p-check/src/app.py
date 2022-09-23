#!/usr/bin/env python3

import json
import socket

import kaillera.p2pclient as Kaillera


# FIXME: the number of messages is limited until PING is implemented
def bot_message_en(user: str, host: str, port: int, check_from: str):
    return [
        f'\n',
        f"Hey {user}! Your P2P is WORKING CORRECTLY!",
        f"Just share '{host}:{port}' with your opponent to play.\n",
        f'Remember to only share your IP with people you trust.',
        f'This bot check came from {check_from}.',
        f'If you did not ask for this check, please report it in Discord.\n',
        f'ggs',
    ]


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
        host = body['host']
        port = int(body['port']) if 'port' in body else 27886
        check_from = body['from'] if 'from' in body else 'unknown'

        client = Kaillera.P2PClient(host, port)
    except socket.error:
        return respond(400, False, "Unable to connect")
    except Exception as e:
        return respond(400, False, "Invalid parameters")

    try:
        username = 'smash64.online'
        client_name = 'p2p-checker-bot'
        connect, response = client.connect(username, client_name)

        if connect is True:
            user, game = client.get_host_info(response)
            message = bot_message_en(user, host, port, check_from)

            for id, line in enumerate(message):
                wait = True if id == 0 else False
                client.chat(line, wait=wait)
            client.disconnect()

            #return respond(200, True, json.dumps({'user': user, 'game': game}))
            return respond(200, True, json.dumps(event))
        else:
            return respond(200, False, "Unable to connect")
    except Exception as e:
        return respond(200, False, "Unable to connect")
