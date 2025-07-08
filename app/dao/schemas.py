from pydantic import BaseModel, ConfigDict, Field

class TelegramIDModel(BaseModel):
    telegram_id: int
    model_config = ConfigDict(from_attributes=True)
    