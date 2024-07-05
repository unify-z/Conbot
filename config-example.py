#请将本文件更名为config.py并填写以下配置项后使用

class Config:
    cookies = {
        'openbmclapi-jwt': ""
    } # 请求 API 用到的 jwt token
    top_query_limit = 100 # 查询上限，默认 100，小于 0 为不限制