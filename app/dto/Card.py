from pydantic import BaseModel


class CardDTO(BaseModel): 
   suit: str | None = None
   rank: str | None = None