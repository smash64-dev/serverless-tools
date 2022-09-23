#!/usr/bin/env python3

import json
import socket

import kaillera.p2pclient as Kaillera


# FIXME: the number of messages is limited until PING is implemented
def bot_message_en(user: str, host: str, port: int,
                   check_from: str, check_via: str):
    return [
        f'\n',
        f"Hey {user}! Your P2P is WORKING CORRECTLY!",
        f"Just share '{host}:{port}' with your opponent to play.\n",
        f'Remember to only share your IP with people you trust.',
        f'This bot request came from {check_from} via {check_via}.',
        f'If you did not ask for this check, please report it in Discord.\n',
        f'ggs',
    ]


def respond(http_code: int, success: bool, message: str, meta: dict = {}):
    return {
        "statusCode": http_code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "body": json.dumps({
            "message": message,
            "meta": json.dumps(meta),
            "success": success,
        }),
    }


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        header = 'cf-connecting-ip'

        port = int(body['port']) if 'port' in body else 27886
        check_via = body['via'] if 'via' in body else 'unknown'
        check_from = event.get('headers', {}).get(header, 'unknown')
        host = check_from if body['host'] == 'self' else body['host']

        meta = {'host': host, 'port': port}

        client = Kaillera.P2PClient(host, port)
    except socket.error:
        return respond(400, False, "Unable to connect", meta)
    except Exception as e:
        return respond(400, False, "Invalid parameters")

    try:
        username = 'smash64.online'
        client_name = 'p2p-checker-bot'
        connect, response = client.connect(username, client_name)

        if connect is True:
            user, game = client.get_host_info(response)
            meta['user'] = user
            meta['game'] = game

            message = bot_message_en(user, host, port, check_from, check_via)

            for id, line in enumerate(message):
                wait = True if id == 0 else False
                client.chat(line, wait=wait)
            client.disconnect()

            return respond(200, True, "OK", meta)
        else:
            return respond(200, False, "Unable to connect", meta)
    except Exception as e:
        return respond(200, False, "Unable to connect", meta)
