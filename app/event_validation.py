from pydantic import BaseModel


class ActionEvent(BaseModel):
    id: str
    trigger: str


class Action(BaseModel):
    event: ActionEvent
