import aiohttp
import asyncio
import json
import os
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import re
from loguru import logger
import websockets
from config import Config
clusterList = {}
async def connect():
    global websocket
    websocket =await websockets.connect('ws://127.0.0.1:3001')
    logger.info("Bot Connected")
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
        #message.append()
    return "\n".join( message)
async def format_rank_message(matching_jsons):
    messages = []
    rank = int(matching_jsons[0].get('rank', 0)) + 1
    metric = matching_jsons[1].get('metric', {})  
    _id = metric.get('clusterId', '未知')  
    sponsor = matching_jsons[1].get('sponsor', {})  
    sporsor_name = sponsor.get('name', '未知')  
    user = matching_jsons[1].get('user', {})  
    user_name = user.get('name', '未知')
        #version = item['version']
        #if item['version'] is None:
            #version = "版本获取失败，Keyerror 'version'"
    try:
            if matching_jsons[1]['version'] == await lastest_version():
                    version = matching_jsons[1]['version'] + "🟢"
            else :
                    version = matching_jsons[1]['version'] + "🟠"
    except KeyError:
                version = "版本获取失败, KeyError:'version'"
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

async def send_message(group_id , message):
    send_data = {
                        "action": "send_group_msg",
                        "params": {
                                "group_id": group_id,
                                "message":  f"OpenBMCLAPI 2.0-rc.0\n{message}"
                                 },
                        "echo": "echo_value"
                            }
    logger.info(f"Sending Message: {json.dumps(send_data, indent=4, ensure_ascii=False)}")
    await websocket.send(json.dumps(send_data))
async def reply_message(group_id,message, message_id):
    send_data = {
                        "action": "send_group_msg",
                        "params": {
                                "group_id": group_id,
                                "message": f'[CQ:reply,id={message_id}]' + f"OpenBMCLAPI 2.0-rc.0\n {message}"
                                 },
                        "echo": "echo_value"
                            }
    logger.info(f"Sending Message: {json.dumps(send_data, indent=4, ensure_ascii=False)}")
    await websocket.send(json.dumps(send_data))
async def _():
        message = await websocket.recv()
        data = json.loads(message) 
        message_id = data.get("message_id")
        logger.info(f"Received Message: {json.dumps(data, indent=4, ensure_ascii=False)}")
        msg = data.get("raw_message", "")
        group_id = data.get("group_id")
        match (msg.split(' ')[0]):
            case ".brrs":
                params = msg[5:].strip()
                if params == "" or params is None:
                    await reply_message(group_id, "请输入节点名称" , message_id)
                if params:
                    data = clusterList
                    matching_jsons = [
                        {"rank": idx + 1, **item} 
                        for idx, item in enumerate(data) 
                        if re.search(params, item.get("name", ""), re.IGNORECASE)
                        ]
                    if matching_jsons:
                        logger.info(f"Matched {len(matching_jsons)} matching cluster(s),{matching_jsons}")
                        await reply_message(group_id, await format_message(matching_jsons) , message_id)
                    else:
                        logger.info("No matching clusters")
                        await reply_message(group_id, "未找到节点" , message_id)
            case ".bmcl":
                                async def get_bmcl_data():
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get('https://bd.bangbang93.com/openbmclapi/metric/version') as response:
                                            version = await response.json()
                                        async with session.get('https://bd.bangbang93.com/openbmclapi/metric/dashboard') as response:
                                            dashboard = await response.json()
                                    #version = requests.get('https://bd.bangbang93.com/openbmclapi/metric/version').json()
                                    #dashboard = requests.get('https://bd.bangbang93.com/openbmclapi/metric/dashboard').json()
                                    await reply_message(group_id, f"官方版本 {version.get('version')}\n在线节点数 {dashboard.get('currentNodes')} 个\n负载: {round(dashboard.get('load')*100, 2)}%\n总出网带宽： {dashboard.get('bandwidth')}mbps\n当前出网带宽：{dashboard.get('currentBandwidth')}mbps\n当日请求：{await format_commas(dashboard.get('hits'))}\n数据量：{await format_units(dashboard.get('bytes'))}\n请求时间：{datetime.datetime.now()}\n数据源 https://bd.bangbang93.com/pages/dashboard" , message_id)
                                await get_bmcl_data()
            case ".bm93":
                        file = msg[6:].strip()
                        if file is None or file == "":
                                async with aiohttp.ClientSession() as session:
                                    async with session.get('https://apis.bmclapi.online/api/93/random?type=json') as response:
                                        data = await response.json()
                                        url = data.get('data',{}).get('url')
                                        await reply_message(group_id, f'[CQ:image,file={url}]' , message_id)
                        else:
                            matchList = []
                            async with aiohttp.ClientSession() as session:
                                async with session.get('https://apis.bmclapi.online/api/93/filelist') as response:
                                    imageList = await response.json()
                            #imageList = requests.get('https://ttb-network.top:8800/mirrors/bangbang93hub/filelist').json()
                            for i in imageList:
                                if str(file).lower() in i:
                                        matchList.append(i)
                            if len(matchList) < 1:
                                        await reply_message(group_id, f"未找到文件" , message_id)
                            elif len(matchList) == 1:
                                        await reply_message(group_id, f"[CQ:image,file=https://unifyz.s3.bitiful.net/mirrors/93hub/{matchList[0]}]", message_id)
                            else:
                                        await reply_message(group_id, f"找到文件过多，请使用更精确的名字" , message_id)
            case ".user":
                clusterid = msg[6:].strip()
                if clusterid:
                    data = clusterList
                    matching_jsons = [
                        {"rank": idx + 1, **item} 
                        for idx, item in enumerate(data) 
                        if re.search(clusterid, item.get("_id", ""), re.IGNORECASE)
                        ]
                    logger.info(f"Matching {len(matching_jsons)} matching cluster(s),{matching_jsons}")
                    if matching_jsons:
                        await reply_message(group_id, await format_message(matching_jsons) , message_id)
                    else:
                        await reply_message(group_id, "未找到节点" , message_id)
            case ".rank":
                try:
                    rank_num = int(msg[6:].strip())
                    if_num_is_int = True
                except ValueError:
                    if_num_is_int = False
                if if_num_is_int is True:
                    try:
                        json_data = clusterList
                        matching_jsons = [
                            {"rank" :rank_num -1},
                            json_data[rank_num -1]

                        ]
                        #logger.debug(f"Matching {len(matching_jsons)} matching cluster(s),{matching_jsons}")
                        await reply_message(group_id, await format_rank_message(matching_jsons), message_id)
                    except IndexError:
                        await reply_message(group_id, "索引超出范围,请输入正确的排名" , message_id)
                else:
                    await reply_message(group_id, "请输入正确的数字" , message_id)
            case ".top":
                try:
                    top_num = int(msg[5:].strip())
                    if_num_is_int = True
                    if top_num == "" or top_num is None:
                        top_num = 10
                    if Config.top_query_limit > 0 and top_num > Config.top_query_limit:
                        await reply_message(group_id, f"请输入小于{Config.top_query_limit}的数字" , message_id)
                        return
                except ValueError:
                    if_num_is_int = False
                data = clusterList
                if if_num_is_int is True:
                    matching_jsons = [
                                {"rank": idx + 1, **item} 
                                for idx, item in enumerate(data) 
                                if idx < int(top_num)
                                    ]  
                    await reply_message(group_id, await format_message(matching_jsons) , message_id)
                else:
                    await reply_message(group_id, "请输入正确的数字" , message_id)
            case ".help":
                await reply_message(group_id , "命令列表：\n.brrs [节点名] 查找节点\n.bmcl 查看OpenBMCLAPI负载\n.bm93 [文件名] 获取该文件名字最相近的图片，为空随机返回\n.user [节点id] 通过id查找节点所有者\n.rank [排名] 获取指定排名的节点\n.top [数量] 获取1-指定数字的节点范围，为空则返回前十名\n.help 查看帮助", message_id)
async def main():
    await connect()
    await fetch_data()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_data, 'interval', seconds=30)
    scheduler.start()
    while True:
            await _()
if __name__ == '__main__':
    asyncio.run(main())
