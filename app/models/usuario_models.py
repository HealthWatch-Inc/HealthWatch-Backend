from pydantic import BaseModel


class FCMTokenUpdate(BaseModel):
    fcm_token: str
