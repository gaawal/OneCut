# -- coding: utf-8 --
# @Time : 2024/5/30 02:01
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : audio.py
# @Software: PyCharm

import json
import os

import numpy as np
from loguru import logger
from pydub import AudioSegment
from mutagen.id3 import ID3
import base64
from app.services.redis_service import RedisService
REDIS_WAVEFORM_KEY = "audio_waveform_{}"

async def get_album_art(file_path):
    try:
        audio_tags = ID3(file_path)
        apic_data = audio_tags.getall('APIC')
        if apic_data:
            # 假设我们取第一个APIC帧
            album_art = apic_data[0].data
            return base64.b64encode(album_art).decode('utf-8'), apic_data[0].mime
    except Exception as e:
        print(f"Error retrieving album art: {e}")
    return None, None

async def format_duration(seconds):
    hours = seconds // 3600  # 获取小时数
    minutes = (seconds % 3600) // 60  # 获取剩余分钟数
    seconds = seconds % 60  # 获取剩余秒数
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

async def get_audio_metadata(file_path):
    try:
        audio_tags = ID3(file_path)
        title = audio_tags.getall('TIT2')
        artist = audio_tags.getall('TPE1')
        title = title[0].text[0] if title else ''
        artist = artist[0].text[0] if artist else '未知作者'
        return (title, artist)
    except Exception as e:
        print(f"Error retrieving audio metadata: {e}")
        return 'Unknown Title', 'Unknown Artist'

async def get_waveform_data(redis_service: RedisService, file_path: str):
    file_name = os.path.basename(file_path)
    cache_key = REDIS_WAVEFORM_KEY.format(file_name)
    cached_data = await redis_service.get(cache_key)
    if cached_data:
        logger.info(f"从缓存中获取波形数据: {file_name}")
        return json.loads(cached_data)
    else:
        waveform_data = generate_waveform_data(file_path)
        await redis_service.set(cache_key, json.dumps(waveform_data), expire=3600)
        logger.info(f"波形数据缓存: {file_name}")
        return waveform_data

def generate_waveform_data(file_path: str):
    audio = AudioSegment.from_file(file_path, format="mp3")
    samples = np.array(audio.get_array_of_samples())
    samples = samples / np.max(np.abs(samples))  # 标准化样本值
    waveform_data = samples[::len(samples) // 500].tolist()  # Downsample to 500 points
    return waveform_data