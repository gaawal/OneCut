# -- coding: utf-8 --
# @Time : 2024/7/14 10:49
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : task_model.py


from fastapi import APIRouter, HTTPException, Request
from tortoise.expressions import Q

from app.controllers.video_task import task_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Success, SuccessExtra
from app.schemas.movies import TaskCreateRequest, TaskIdRequest, TaskUpdateRequest, TaskListRequest

router = APIRouter()


@router.post("/list", summary="查看视频任务列表")
async def list_tasks(request: TaskListRequest):
    q = Q()
    order = []

    if request.query:
        q &= Q(draft_content__script_info__video_title__icontains=request.query)

    if request.taskStatus:
        q &= Q(state=request.taskStatus)

    if request.publishStatus:
        q &= Q(platform_status__contains=request.publishStatus)

    if request.sort:
        sort_order = '-' if request.sort == 'desc' else ''
        order.append(f"{sort_order}created_at")

    total, tasks = await task_controller.list(page=request.page, page_size=request.page_size, search=q, order=order)
    data = [await task.to_dict() for task in tasks]

    return SuccessExtra(data=data, total=total, page=request.page, page_size=request.page_size)


@router.post("/get", summary="查看任务")
async def get_task(request: Request, body: TaskIdRequest):
    """
    查看任务

    - **task_id**: 任务ID
    """
    task = await task_controller.get_by_task_id(task_id=body.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    return Success(data=await task.to_dict())


@router.post("/create", summary="创建任务")
async def create_task(request: Request, body: TaskCreateRequest):
    """
    创建任务

    - **user_id**: 用户ID
    - **task_id**: 任务ID
    - **progress**: 任务进度
    - **state**: 任务状态
    - **draft_content**: 草稿内容
    """
    user_id = CTX_USER_ID.get()
    body.user_id = user_id  # 使用上下文中的 user_id
    new_task = await task_controller.create(obj_in=body)
    return Success(data=await new_task.to_dict())


@router.post("/update", summary="更新任务")
async def update_task(request: Request, body: TaskUpdateRequest):
    """
    更新任务

    - **id**: 任务ID
    - **progress**: 任务进度
    - **state**: 任务状态
    - **draft_content**: 草稿内容
    """
    updated_task = await task_controller.update(obj_in=body)
    return Success(data=await updated_task.to_dict())


@router.post("/delete", summary="删除任务")
async def delete_task(request: Request, body: TaskIdRequest):
    """
    删除任务

    - **task_id**: 任务ID
    """
    await task_controller.remove(id=body.task_id)
    return Success(msg="任务删除成功")
