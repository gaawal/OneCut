from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

# NewType 是 Python 的 typing 模块提供的一个函数，用于创建类型的别名（新类型）。
# Total = NewType("Total", int) 这行代码创建了一个名为 Total 的新类型，它本质上是 int 类型的别名。
Total = NewType("Total", int)
# ModelType 是一个类型变量，它表示将会是 Model 类或其子类
ModelType = TypeVar("ModelType", bound=Model)
# CreateSchemaType 是一个类型变量，它表示将会是 BaseModel 类或其子类。
# bound=BaseModel 表示 CreateSchemaType 类型变量只能是 BaseModel 类或其子类。
# 这种类型变量通常用于约束函数或类中的参数或返回值，使它们只能接受特定类型的对象。
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: int) -> ModelType:
        return await self.model.get(id=id)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[Total, List[ModelType]]:
        query = self.model.filter(search)
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True)
        obj = await self.get(id=id)
        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def remove(self, id: int) -> None:
        obj = await self.get(id=id)
        await obj.delete()
