from pydantic import BaseModel

class UserFacingError(BaseModel):
    code: str
    message: str
