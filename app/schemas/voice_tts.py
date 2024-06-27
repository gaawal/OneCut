# -- coding: utf-8 --
# @Time : 2024/6/27 17:20
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : voice_tts.py
# @Software: PyCharm
from pydantic import BaseModel


class TTSRequest(BaseModel):
    text: str
    prompt: str = ""
    voice: str = "12.csv"
    speed: int = 4
    temperature: float = 0.44062
    top_p: float = 0.7
    top_k: int = 20
    refine_max_new_token: int = 384
    infer_max_new_token: int = 2048
    text_seed: int = 42
    skip_refine: int = 0
    custom_voice: int = 0