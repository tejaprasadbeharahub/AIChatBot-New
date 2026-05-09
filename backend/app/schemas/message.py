import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MessageRead(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime

    model_config = {"from_attributes": True}
