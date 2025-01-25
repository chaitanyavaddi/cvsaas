from pydantic import BaseModel

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: str