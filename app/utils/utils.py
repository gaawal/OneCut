import locale
import os
import threading
from typing import Any
from loguru import logger
import json
from uuid import uuid4
import urllib3

from app.constant import video_const

urllib3.disable_warnings()


def get_response(status: int, data: Any = None, message: str = ""):
    obj = {
        'status': status,
    }
    if data:
        obj['data'] = data
    if message:
        obj['message'] = message
    return obj


def to_json(obj):
    try:
        # 定义一个辅助函数来处理不同类型的对象
        def serialize(o):
            # 如果对象是可序列化类型，直接返回
            if isinstance(o, (int, float, bool, str)) or o is None:
                return o
            # 如果对象是二进制数据，转换为base64编码的字符串
            elif isinstance(o, bytes):
                return "*** binary data ***"
            # 如果对象是字典，递归处理每个键值对
            elif isinstance(o, dict):
                return {k: serialize(v) for k, v in o.items()}
            # 如果对象是列表或元组，递归处理每个元素
            elif isinstance(o, (list, tuple)):
                return [serialize(item) for item in o]
            # 如果对象是自定义类型，尝试返回其__dict__属性
            elif hasattr(o, '__dict__'):
                return serialize(o.__dict__)
            # 其他情况返回None（或者可以选择抛出异常）
            else:
                return None

        # 使用serialize函数处理输入对象
        serialized_obj = serialize(obj)

        # 序列化处理后的对象为JSON字符串
        return json.dumps(serialized_obj, ensure_ascii=False, indent=4)
    except Exception as e:
        return None


def get_uuid(remove_hyphen: bool = False):
    u = str(uuid4())
    if remove_hyphen:
        u = u.replace("-", "")
    return u


def root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def storage_dir(sub_dir: str = "", create: bool = False):
    d = os.path.join(root_dir(), "storage")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if create and not os.path.exists(d):
        os.makedirs(d)

    return d


def cache_videos_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), storage_dir(), "cache_videos")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d
def cache_browser_info_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), storage_dir(), "cache_browser_material")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d

def resource_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), "resource")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d


def task_dir(sub_dir: str = ""):
    d = os.path.join(storage_dir(), "tasks")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def font_dir(sub_dir: str = ""):
    d = resource_dir(f"fonts")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def song_dir(sub_dir: str = ""):
    d = resource_dir(f"songs")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def i18n_dir(sub_dir: str = ""):
    d = resource_dir(f"i18n")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def voice_dir(sub_dir: str = ""):
    d = resource_dir(f"voices")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def public_dir(sub_dir: str = ""):
    d = resource_dir(f"public")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def run_in_background(func, *args, **kwargs):
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"run_in_background error: {e}")

    thread = threading.Thread(target=run)
    thread.start()
    return thread


def time_convert_seconds_to_hmsm(seconds) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, seconds, milliseconds)


def text_to_srt(idx: int, msg: str, start_time: float, end_time: float) -> str:
    start_time = time_convert_seconds_to_hmsm(start_time)
    end_time = time_convert_seconds_to_hmsm(end_time)
    srt = """%d
%s --> %s
%s
        """ % (
        idx,
        start_time,
        end_time,
        msg,
    )
    return srt


def str_contains_punctuation(word):
    for p in video_const.PUNCTUATIONS:
        if p in word:
            return True
    return False


def split_string_by_punctuations(s):
    result = []
    txt = ""

    previous_char = ""
    next_char = ""
    for i in range(len(s)):
        char = s[i]
        if char == "\n":
            result.append(txt.strip())
            txt = ""
            continue

        if i > 0:
            previous_char = s[i - 1]
        if i < len(s) - 1:
            next_char = s[i + 1]

        if char == "." and previous_char.isdigit() and next_char.isdigit():
            # 取现1万，按2.5%收取手续费, 2.5 中的 . 不能作为换行标记
            txt += char
            continue

        if char not in video_const.PUNCTUATIONS:
            txt += char
        else:
            result.append(txt.strip())
            txt = ""
    result.append(txt.strip())
    # filter empty string
    result = list(filter(None, result))
    return result


def md5(text):
    import hashlib
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_system_locale():
    try:
        loc = locale.getdefaultlocale()
        # zh_CN, zh_TW return zh
        # en_US, en_GB return en
        language_code = loc[0].split("_")[0]
        return language_code
    except Exception as e:
        return "en"


def load_locales(i18n_dir):
    _locales = {}
    for root, dirs, files in os.walk(i18n_dir):
        for file in files:
            if file.endswith(".json"):
                lang = file.split(".")[0]
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    _locales[lang] = json.loads(f.read())
    return _locales


def parse_extension(filename):
    return os.path.splitext(filename)[1].strip().lower().replace(".", "")


def tr(key: str, language: str = 'zh') -> str:
    locales = load_locales(i18n_dir())
    loc = locales.get(language, {})
    return loc.get("Translation", {}).get(key, key)

def calculate_duration(start_time, end_time):
    duration = end_time - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return minutes, seconds
if __name__ == '__main__':
    result = split_string_by_punctuations('千万不要再相信那些博主说自媒体文案随随便便就能生成爆款！今天，我要揭露一个真相：爆款文案背后隐藏的秘密。你可能不知道，每一篇爆款文案都是经过精心策划和数据分析的结果。首先，你需要了解你的目标受众，他们的痛点、需求和兴趣点。接着，运用心理学原理，比如稀缺性、紧迫感，来激发他们的购买欲望。然后，巧妙地使用故事叙述技巧，让读者产生共鸣，增强文案的吸引力。最后，别忘了测试和优化，通过数据反馈不断调整文案策略。掌握了这些技巧，你也能写出让人眼前一亮的爆款文案。别再盲目跟风，学会这些，让你的自媒体文案独树一帜！')
    print(result)