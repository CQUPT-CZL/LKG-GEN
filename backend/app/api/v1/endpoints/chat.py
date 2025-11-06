from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    created_at: str


@router.post("/mock", response_model=ChatResponse)
def mock_chat(req: ChatRequest):
    """
    模拟聊天回复接口：接收用户消息并返回一个简单的模拟回答。

    前端可用于对话UI联调，后续可替换为真实LLM服务。
    """
    cid = req.conversation_id or "mock-conv-001"
    reply_text = f"模拟回答：你说的是『{req.message}』，这是一个测试回复。"
    return ChatResponse(
        reply=reply_text,
        conversation_id=cid,
        created_at=datetime.utcnow().isoformat() + "Z",
    )