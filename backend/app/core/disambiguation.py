# app/core/disambiguation.py

from difflib import SequenceMatcher
from app.crud.crud_graph import get_entities_by_graph


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    import re
    # 小写、去除空白和标点
    t = text.lower().strip()
    t = re.sub(r"[\s\-_/·•．·\.]+", "", t)
    t = re.sub(r"[，,。.!！?？:：;；（）()\[\]{}<>\"'`]+", "", t)
    return t


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def disambiguate_entities_against_graph(entities_dict: dict, neo4j_driver, graph_id: str | None) -> dict:
    """
    融合“当前文档抽取的新实体”和“图谱中已存在的实体”进行消歧：
    1) 先在本批次内按名称+类型去重与合并频次；
    2) 再与图谱中实体做匹配（优先精确，其次相似度阈值匹配），命中则指向已有实体ID；
    3) 返回用于入库的消歧实体字典（可能包含 existing_id 字段，表示已存在图谱中的实体）。
    """
    graph_key = graph_id or "default-graph-id"

    # 1) 从图谱读出现有实体
    try:
        existing_entities = get_entities_by_graph(neo4j_driver, graph_key) or []
    except Exception as e:
        print(f"⚠️ 读取图谱实体失败，fallback为空列表: {e}")
        existing_entities = []

    # 建索引：按类型分组、以及精确键（规范名+类型）索引
    existing_by_type: dict[str, list] = {}
    existing_exact_index: dict[str, dict] = {}
    for e in existing_entities:
        etype = e.get("entity_type") or e.get("type") or ""
        name = e.get("name") or e.get("entity_text") or ""
        norm_key = f"{_normalize_text(name)}|{etype}"
        existing_exact_index[norm_key] = e
        existing_by_type.setdefault(etype, []).append(e)

    # 2) 本批次内合并去重
    # 将输入字典的值（每个是 {text,type,description,chunk_id,frequency?}）转为列表处理
    new_entities = list(entities_dict.values()) if isinstance(entities_dict, dict) else (entities_dict or [])

    # 先按精确规范键去重，再对同类型做轻量相似合并
    local_canon_map: dict[str, dict] = {}
    for ent in new_entities:
        name = ent.get('text', ent.get('name', ''))
        etype = ent.get('type', ent.get('entity_type', ''))
        if not name or not etype:
            continue
        norm_key = f"{_normalize_text(name)}|{etype}"
        if norm_key in local_canon_map:
            # 合并频次
            local_canon_map[norm_key]['frequency'] = local_canon_map[norm_key].get('frequency', 1) + ent.get('frequency', 1)
            # 描述择优保留更长的
            old_desc = local_canon_map[norm_key].get('description') or ''
            new_desc = ent.get('description') or ''
            if len(new_desc) > len(old_desc):
                local_canon_map[norm_key]['description'] = new_desc
        else:
            # 初始化副本，避免外部引用
            local_canon_map[norm_key] = {
                'text': name,
                'type': etype,
                'description': ent.get('description'),
                'frequency': ent.get('frequency', 1)
            }

    # 轻量相似合并（同类型内名称相似的合并），避免 O(N^2) 大量匹配，数量通常不大可接受
    keys_by_type: dict[str, list[str]] = {}
    for key, ent in local_canon_map.items():
        etype = ent['type']
        keys_by_type.setdefault(etype, []).append(key)

    for etype, keys in keys_by_type.items():
        merged = {}
        keys_to_remove = set()
        for key in keys:
            if key in merged:
                continue
            base = local_canon_map[key]
            base_norm = key.split('|')[0]
            merged[key] = True
            # 与同类型其余项比较
            for other_key in keys:
                if other_key in merged or other_key == key:
                    continue
                other_norm = other_key.split('|')[0]
                if _similarity(base_norm, other_norm) >= 0.92:
                    # 合并到 base
                    base['frequency'] = base.get('frequency', 1) + local_canon_map[other_key].get('frequency', 1)
                    # 描述择优
                    old_desc = base.get('description') or ''
                    new_desc = local_canon_map[other_key].get('description') or ''
                    if len(new_desc) > len(old_desc):
                        base['description'] = new_desc
                    merged[other_key] = True
                    keys_to_remove.add(other_key)
        # 将被合并项从映射中移除，避免后续重复输出
        for rm_key in keys_to_remove:
            if rm_key in local_canon_map:
                del local_canon_map[rm_key]

    # 3) 与图谱实体匹配（精确优先，相似兜底）
    result: dict[str, dict] = {}
    for key, ent in local_canon_map.items():
        name = ent['text']
        etype = ent['type']
        norm_name = _normalize_text(name)
        exact_key = f"{norm_name}|{etype}"

        matched_entity = existing_exact_index.get(exact_key)
        if matched_entity is None:
            # 相似匹配（在同类型中寻找最相似项）
            candidates = existing_by_type.get(etype, [])
            best = None
            best_score = 0.0
            for c in candidates:
                c_name = c.get('name') or c.get('entity_text') or ''
                score = _similarity(norm_name, _normalize_text(c_name))
                if score > best_score:
                    best_score = score
                    best = c
            if best is not None and best_score >= 0.90:
                matched_entity = best

        if matched_entity is not None:
            # 命中已有实体，采用已有实体的规范名，并记录 existing_id
            canonical_name = matched_entity.get('name') or matched_entity.get('entity_text') or name
            out = {
                'text': canonical_name,
                'type': etype,
                'description': ent.get('description'),
                'frequency': ent.get('frequency', 1),
                'existing_id': matched_entity.get('id')
            }
        else:
            # 作为新实体保留
            out = ent.copy()
        result_key = f"{out['text']}_{out['type']}"
        result[result_key] = out

    print(f"✅ 实体消歧(全图谱)完成：输入 {len(new_entities)} → 合并 {len(result)}，其中命中已有实体 {sum(1 for v in result.values() if v.get('existing_id'))} 个")
    return result