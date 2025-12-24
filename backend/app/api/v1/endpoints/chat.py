from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
import httpx
from typing import List, Optional
from app.core.config import settings

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    graph_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    center_entity: Optional[str] = None
    paths: Optional[List[str]] = None
    referenced_paths: Optional[List[str]] = []
    visualization_base64: Optional[str] = None
    conversation_id: str
    created_at: str


@router.post("/query", response_model=ChatResponse)
def chat_query(req: ChatRequest):
    """
    知识图谱问答接口：接收用户消息并返回基于知识图谱的回答。

    包含回答内容、中心实体、推理路径和可视化图片。
    """
    cid = req.conversation_id or "mock-conv-001"

    # 调用外部知识图谱问答服务（端口 8001），并将结果转为前端需要的结构化格式
    try:
        payload: dict = {"query": req.message}
        if req.graph_id:
            payload["graph_id"] = req.graph_id

        resp = httpx.post(settings.KG_QUERY_API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        answer = data.get("answer") or "未获取到答案。"
        center_entity = data.get("center_entity")
        paths = data.get("paths")
        referenced_paths = data.get("referenced_paths") or []
        visualization_base64 = data.get("visualization_base64")

        # 直接以结构化形式返回，供前端分别展示
    except Exception as e:
        # 外部服务不可用时，给出友好的降级提示
        answer = (
            f"外部问答服务暂不可用，请稍后再试。\n"
            f"原因：{e}\n"
            f"原始消息：『{req.message}』"
        )
        center_entity = None
        paths = []
        referenced_paths = []
        visualization_base64 = None

    return ChatResponse(
        answer=answer,
        center_entity=center_entity,
        paths=paths if isinstance(paths, list) else None,
        referenced_paths=referenced_paths if isinstance(referenced_paths, list) else [],
        visualization_base64=visualization_base64,
        conversation_id=cid,
        created_at=datetime.now(timezone.utc).isoformat(),
    )