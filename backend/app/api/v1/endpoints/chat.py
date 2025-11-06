from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import httpx
from app.core.config import settings

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    graph_id: str | None = None


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

    # 调用外部知识图谱问答服务（端口 8001），并将结果转为前端需要的回复格式
    try:
        payload: dict = {"query": req.message}
        if req.graph_id:
            payload["graph_id"] = req.graph_id

        resp = httpx.post(settings.KG_QUERY_API_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        answer = data.get("answer") or "未获取到答案。"
        center_entity = data.get("center_entity")
        paths = data.get("paths")

        extra = ""
        if center_entity:
            extra += f"\n中心实体：{center_entity}"
        if paths:
            paths_str = " | ".join(paths) if isinstance(paths, list) else str(paths)
            extra += f"\n路径：{paths_str}"

        reply_text = f"{answer}{extra}"
    except Exception as e:
        # 外部服务不可用时，给出友好的降级提示
        reply_text = (
            f"外部问答服务暂不可用，请稍后再试。\n"
            f"原因：{e}\n"
            f"原始消息：『{req.message}』"
        )

    return ChatResponse(
        reply=reply_text,
        conversation_id=cid,
        created_at=datetime.utcnow().isoformat() + "Z",
    )