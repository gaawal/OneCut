# -- coding: utf-8 --
# @Time : 2024/8/3 12:26
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : image.py
# @Software: PyCharm

import os


from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.utils import utils

router = APIRouter()


@router.get("/stream-coverimg", summary="返回生成的封面文件")
async def stream_coverimg(task_id: str = Query(...)):
    # 假设视频文件保存在一个以 task_id 命名的目录下
    task_dir = os.path.join(utils.task_dir(), task_id)
    coverimg = os.path.join(task_dir, "cover.png")
    if not os.path.exists(coverimg):
        image_dir = os.path.join(utils.image_dir())
        coverimg = os.path.join(image_dir, "cover-default.jpeg")
        return FileResponse(coverimg, media_type="image/jpeg")

    # 返回封面文件
    return FileResponse(coverimg, media_type="image/png")