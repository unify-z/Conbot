import aiohttp
import asyncio
import json
import os
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import re
import logging as logger
from .config import Config
from core import bot
from core.events import *
from core.command import *
from core.common import Matcher
from core.messages import Message , MessageSegment
clusterList = {}


async def format_commas(num):
    return '{:,}'.format(num)

async def format_units(value):
    mb_value = value / 1024 / 1024
    gb_value = mb_value / 1024  
    tb_value = gb_value / 1024  
    if tb_value >= 1:  
        return f"{tb_value:.2f}TB"  
    else:  
        return f"{gb_value:.2f}GB"

async def lastest_version():
        async with aiohttp.ClientSession() as session:
            async with session.get('https://bd.bangbang93.com/openbmclapi/metric/version') as response:
                version = await response.json()
        #ersion = requests.get('https://bd.bangbang93.com/openbmclapi/metric/version').json()
        return version.get('version')

async def format_message(data):
    message =[]
    for item in data:
        rank = item['rank']
        metric = item.get('metric', {})  
        _id = metric.get('clusterId', '未知')  
        sponsor = item.get('sponsor', {})  
        sporsor_name = sponsor.get('name', '未知')  
        #user = item.get('user', {})  
        if item.get('user', None) is None:
            user = {"name": "未知"}
        else:
            user = item.get('user', {})  
        user_name = user.get('name', '未知')
        try:
                if item['version'] == await lastest_version():
                    version = item['version'] + "🟢"
                else :
                    version = item['version'] + "🟠"
        except KeyError:
                version = "版本获取失败"
        bytes_mb = await format_units(metric.get('bytes', 0))  
        hits = await format_commas(metric.get('hits', 0))  
        name = item['name']

        is_enabled = "✅" if item['isEnabled'] else "❌"
        message.append(f"{rank} | {_id} | {name} | {is_enabled} | {bytes_mb} | {hits} | 所有者 {user_name} | 赞助商 {sporsor_name} | 版本 {version}")
    return "\n".join(message)

async def format_rank_message(matching_jsons):
    messages = []
    rank = int(matching_jsons[0].get('rank', 0)) + 1
    metric = matching_jsons[1].get('metric', {})  
    _id = metric.get('clusterId', '未知')  
    sponsor = matching_jsons[1].get('sponsor', {})  
    sporsor_name = sponsor.get('name', '未知')  
    user = matching_jsons[1].get('user', {})  
    user_name = user.get('name', '未知')
    try:
            if matching_jsons[1]['version'] == await lastest_version():
                    version = matching_jsons[1]['version'] + "🟢"
            else :
                    version = matching_jsons[1]['version'] + "🟠"
    except KeyError:
                version = "版本获取失败"
    bytes_mb = await format_units(metric.get('bytes', 0))  
    hits = await format_commas(metric.get('hits', 0))  
    name = matching_jsons[1]['name']
    is_enabled = "✅" if matching_jsons[1]['isEnabled'] else "❌"
    messages.append(f"{rank} | {_id} | {name} | {is_enabled} | {bytes_mb} | {hits} | 所有者 {user_name} | 赞助商 {sporsor_name} | 版本 {version}")
    return "\n".join(messages)

async def fetch_data():
    global clusterList
    cookies = Config.cookies
    base_url = "https://bd.bangbang93.com/openbmclapi/metric/rank"
    async with aiohttp.ClientSession(cookies=cookies) as session:
        logger.info("Fetching data")
        async with session.get(base_url) as response:
            logger.info("Data fetched")
            clusterList = await response.json()
async def init():
     await fetch_data()
     scheduler = AsyncIOScheduler()
     scheduler.add_job(fetch_data, 'interval', seconds=30)
     scheduler.start()
     msg =Message()
