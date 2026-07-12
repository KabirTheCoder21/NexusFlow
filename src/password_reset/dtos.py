from re import S

from pydantic import BaseModel, EmailStr, Field

class ForgetPasswordDTO(BaseModel):
    email:EmailStr

class ResetPasswordDTO(BaseModel):
    token:str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )