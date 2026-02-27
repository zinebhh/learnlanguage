from pydantic import BaseModel, EmailStr

class RegisterIn(BaseModel):
    email: EmailStr
    username: str
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class AuthOut(BaseModel):
    token: str
    user_id: int
    email: EmailStr
    username: str