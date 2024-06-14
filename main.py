from __future__ import annotations
from flask import Flask, request, jsonify

import asyncio
import json
import os
import re
from getpass import getpass

import click
from telethon.sync import TelegramClient, errors, functions
from telethon.tl import types

app = Flask(__name__)


async def send_code(
        api_id: str | None, api_hash: str | None, phone_number: str | None
) -> int:
    client = TelegramClient(phone_number, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        try:
            await client.send_code_request(phone_number)
        except Exception as err:
            print(err)
            return 500
    else:
        return 200

    print("send code is successfully")
    return 201


async def login(
        api_id: str | None, api_hash: str | None, phone_number: str | None
) -> TelegramClient:
    """Create a telethon session or reuse existing one"""
    client = TelegramClient(phone_number, api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        try:
            await client.sign_in(
                phone_number, input("Enter the code (sent on telegram): ")
            )
        except errors.SessionPasswordNeededError:
            pw = getpass(
                "Two-Step Verification enabled. Please enter your account password: "
            )
            await client.sign_in(password=pw)
    print("Done.")
    return client


@app.route('/v1/api/auth/send-code', methods=['POST'])
async def handle_send_code_request():
    if 'api-key' not in request.headers or request.headers['api-key'] != os.getenv("API_KEY"):
        response = {
            "data": {},
            "message": "api key is invalid",
            "code": 401
        }
        return jsonify(response), 401

    try:
        data = request.get_json()
        status_code = await send_code(data["app_id"], data["api_hash"], data["phone_number"])
        return jsonify(
            {
                "data": {},
                "message": "api key is invalid",
                "code": status_code
            }
        ), 200
    except Exception as err:
        print(err)
        return jsonify(
            {
                "data": {},
                "message": "send code request is failed",
                "code": 500
            }
        ), 500


@app.route('/v1/api/auth/login', methods=['POST'])
async def handle_login_request():
    if 'api-key' not in request.headers or request.headers['api-key'] != os.getenv("API_KEY"):
        response = {
            "data": {},
            "message": "api key is invalid",
            "code": 401
        }
        return jsonify(response), 401

    try:
        data = request.get_json()
        client_tele = await login(data["app_id"], data["api_hash"], data["phone_number"])
        client_tele.disconnect()
        return res, 200
    except ValueError:
        return jsonify(
            {
                "data": {},
                "message": "login is failed",
                "code": 500
            }
        ), 500


# @app.route('/test', methods=['POST'])
# async def handle_post_request():
#     if 'api-key' not in request.headers:
#         return "Token is missing.", 401
#
#     if request.headers['api-key'] != "SECRET_KEY":
#         return "Invalid token.", 401
#     try:
#         data = request.get_json()
#         client_tele = await login(os.getenv("API_ID"), os.getenv("API_HASH"), os.getenv("PHONE_NUMBER"))
#         res = await validate_users(client_tele, data["phone_number"])
#         client_tele.disconnect()
#         return res, 200
#     except ValueError:
#         return "Format_Error", 413
#

if __name__ == '__main__':
    app.run()
