# -- coding: utf-8 --
# @Time : 2024/6/27 17:18
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : chat_tts.py
# @Software: PyCharm
# API调用代码

import requests

res = requests.post('http://192.168.1.109:9966/tts', data={
    "text": "你是否曾经梦想过能流利地说英语，但却感觉进步缓慢？别担心，今天我将分享一些实用的技巧，帮助你快速提高英语水平。首先，让我们谈谈为什么传统的学习方法往往效果不佳。大多数人依赖教科书和课堂学习，但这些方法往往缺乏实际应用，导致学习效率低下。接下来，我要介绍的是一种结合了听、说、读、写全方位练习的方法。通过观看英语电影、听英文歌曲、参与英语角活动，以及每天坚持写英语日记，你可以在不知不觉中提高英语能力。最后，记得持之以恒是关键。每天抽出一定的时间来练习，哪怕只有十分钟，长期积累下来也会有显著的效果。现在就开始行动吧，让英语成为你的第二语言！",
    "prompt": "",
    "voice": "12.csv",
    "speed": 4,
    "temperature": 0.44062,
    "top_p": 0.7,
    "top_k": 20,
    "refine_max_new_token": 384,
    "infer_max_new_token": 2048,
    "text_seed": 42,
    "skip_refine": 0,
    "custom_voice": 0
})
print(res.json())

data = {
    'audio_files': [
        {
            'audio_duration': 50.86,
            'filename': 'F:/Python/ChatTTS-ui/static/wavs/172709_use59.08s-audio50.86s-seed12.csv-te0.44062-tp0.7-tk20-textlen270-37138.wav',
            'inference_time': 59.08,
            'url': 'http://192.168.1.109:9966/static/wavs/172709_use59.08s-audio50.86s-seed12.csv-te0.44062-tp0.7-tk20-textlen270-37138.wav'
        }
    ],
    'code': 0,
    'filename': 'F:/Python/ChatTTS-ui/static/wavs/172709_use59.08s-audio50.86s-seed12.csv-te0.44062-tp0.7-tk20-textlen270-37138.wav',
    'msg': 'ok',
    'url': 'http://192.168.1.109:9966/static/wavs/172709_use59.08s-audio50.86s-seed12.csv-te0.44062-tp0.7-tk20-textlen270-37138.wav'}
# error {code:1, msg:"error"}
