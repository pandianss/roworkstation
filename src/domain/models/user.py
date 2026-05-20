from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    username: str
    role: str = "USER"
    dept: str = "3933"
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True

class UserSession(BaseModel):
    username: str
    start_time: datetime
    ip_address: Optional[str] = None
    is_active: bool = True
