from enum import Enum
from typing import Optional
from pydantic import model_validator

from aiogram.filters.callback_data import CallbackData


class UserInfoParameters(str, Enum):
    status = "status"


class UserInfoParameterValue(str, Enum):
    on = "on"
    off = "off"


class UsersList(CallbackData, prefix="users_list"):
    page_number: int


class UserInfo(CallbackData, prefix="user_info"):
    user_id: int
    parameter: Optional[UserInfoParameters] = None
    parameter_value: Optional[UserInfoParameterValue] = None
    delete_message: bool = False

    @model_validator(mode="after")
    def model_validate(self):
        if self.parameter and not self.parameter_value:
            raise ValueError("parameter_value must be specified when parameter is specified")
        return self
