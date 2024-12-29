from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token for authentication")
    token_type: str = Field(..., description="Type of the token (e.g., bearer)")

class UserCreate(BaseModel):
    username: str = Field(..., description="Username for account creation")
    password: str = Field(..., description="Password for account creation")

class UserInDB(BaseModel):
    id: int = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username of the user")

    class Config:
        from_attributes = True 