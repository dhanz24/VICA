from pydantic import BaseModel

class AskQuestionDTO(BaseModel):
    user_id: str
    chat_id: str
    question: str
    