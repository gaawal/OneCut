# -- coding: utf-8 --
# @Time : 2024/7/14 10:47
# @Author : JiahuaLInk
# @Email : 840132699@qq.com
# @File : task_model.py


from typing import List, Optional, Dict, Any, Tuple

from app.core.crud import CRUDBase
from app.models.task_model import TaskModel
from app.schemas.video_task import TaskCreate, TaskUpdate
from tortoise.expressions import Q

class TaskController(CRUDBase[TaskModel, TaskCreate, TaskUpdate]):
    def __init__(self):
        super().__init__(model=TaskModel)

    async def get_by_task_id(self, task_id: str) -> Optional[TaskModel]:
        return await self.model.filter(task_id=task_id).first()

    async def get_by_user_id(self, user_id: int) -> List[TaskModel]:
        return await self.model.filter(user_id=user_id).all()

    async def create(self, obj_in: TaskCreate) -> TaskModel:
        obj = await super().create(obj_in.create_dict())
        return obj

    async def update(self, obj_in: TaskUpdate) -> TaskModel:
        return await super().update(id=obj_in.id, obj_in=obj_in.update_dict())

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[
        int, List[TaskModel]]:
        query = self.model.filter(search)
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)
task_controller = TaskController()
