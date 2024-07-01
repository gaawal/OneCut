# -- coding: utf-8 --
# @Time : 2024/6/30 09:59
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : redis_const.py
# @Software: PyCharm
class RedisExpireTime:
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    TEN_MINUTES = 600
    THIRTY_MINUTES = 1800
    ONE_HOUR = 3600
    TWO_HOURS = 7200
    ONE_DAY = 86400
    ONE_WEEK = 604800
    ONE_MONTH = 2592000


class RedisKeyPrefix:
    WEIBO_HOT_SEARCH = 'weibo_hotsearch'
    WEIBO_HOT_ARTICLE = 'weibo_hot_article:{}'
    VIDEO_TASK = 'video-{}'
    BGM_FILE = 'bgm_file_cache:{}'
    BGMS_LIST= 'bgm_list_cache'


