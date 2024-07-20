# -- coding: utf-8 --
# @Time : 2024/7/14 10:49
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : tasks.py

from fastapi import APIRouter, Query, HTTPException
from app.controllers.video_task import task_controller
from sympy import Q

from app.schemas.base import Success, SuccessExtra
from app.schemas.video_task import *

router = APIRouter()

@router.get("/list", summary="查看任务列表")
async def list_tasks(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    user_id: int = Query(None, description="用户ID"),
):
    q = Q()
    if user_id:
        q &= Q(user_id=user_id)
    total, tasks = await task_controller.list(page=page, page_size=page_size, search=q)
    data = [await task.to_dict() for task in tasks]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)

@router.get("/get", summary="查看任务")
async def get_task(
    task_id: str = Query(..., description="任务ID"),
):
    task = await task_controller.get_by_task_id(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    return Success(data=await task.to_dict())

@router.post("/create", summary="创建任务")
async def create_task(
    task_in: TaskCreate,
):
    new_task = await task_controller.create(obj_in=task_in)
    return Success(data=await new_task.to_dict())

@router.post("/update", summary="更新任务")
async def update_task(
    task_in: TaskUpdate,
):
    updated_task = await task_controller.update(obj_in=task_in)
    return Success(data=await updated_task.to_dict())

@router.delete("/delete", summary="删除任务")
async def delete_task(
    task_id: str = Query(..., description="任务ID"),
):
    await task_controller.remove(id=task_id)
    return Success(msg="任务删除成功")
