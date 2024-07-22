# -- coding: utf-8 --
# @Time : 2024/7/1 21:49
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : drafts.py

import json
import os
import time
from typing import List, Dict, Any

from app.schemas.movies import VideoParams


def current_timestamp():
    return int(time.time())


class Draft:
    def __init__(self, task_id: str, params: VideoParams):
        width, height = params.video_aspect.to_resolution()
        self.draft = {
            "id": task_id,
            "create_time": current_timestamp(),
            "update_time": current_timestamp(),
            "canvas_config": {
                "height": height,
                "width": width,
                "ratio": "original"
            },
            "duration": 0,
            "fps": params.fps,
            "script_info": {
                "video_script": "",
                "video_terms": [],
                "video_title": ""
            },
            "materials": {
                "videos": [],
                "audios": [],
                "subtitles": [],
                "images": [],
                "cover": []
            },

        }

    def add_script_info(self, script: str, terms: List[str], title: str):
        self.draft["script_info"] = {
            "video_script": script,
            "video_terms": terms,
            "video_title": title
        }

    def add_material(self, material_type: str, material_info: Dict[str, Any]):
        if material_type in self.draft["materials"]:
            self.draft["materials"][material_type].append(material_info)

    def update_duration(self, duration: float):
        self.draft["duration"] = duration
        self.draft["update_time"] = current_timestamp()

    def save_to_file(self, directory: str):
        draft_file = os.path.join(directory, "draft.json")
        with open(draft_file, "w", encoding="utf-8") as f:
            json.dump(self.draft, f, ensure_ascii=False, indent=4)

    def load_from_file(self, draft_file: str):
        with open(draft_file, "r", encoding="utf-8") as f:
            self.draft = json.load(f)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return self.draft
