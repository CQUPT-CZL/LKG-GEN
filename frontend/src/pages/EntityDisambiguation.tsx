import React, { useEffect, useMemo, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Select,
  Button,
  Table,
  Tag,
  Divider,
  message,
  Radio,
  Modal,
  Descriptions
} from 'antd';
import {
  NodeIndexOutlined,
  DatabaseOutlined,
  BranchesOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  MergeCellsOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { apiService, Graph, Category, Entity, EntityMergeRequest } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

type DetectionMethod = 'similarity' | 'llm' | 'embedding';

interface PairSuggestion {
  key: string; // pair key
  entity_type: string;
  a: Entity;
  b: Entity;
  score: number;
  recommendedTargetId?: string; // 频次更高者为目标
}

// 文本标准化（避免 ES6 正则标志与 Unicode 属性）
function normalizeText(s: string): string {
  const lower = (s || '').toLowerCase();
  // 移除常见中英文标点（在字符类中显式列出，避免使用 \p{...} 与 'u' 标志）
  const withoutPunct = lower.replace(/[!-/:-@\[-`{-~，。；：？！、（）《》【】“”‘’·—…]/g, ' ');
  return withoutPunct.replace(/\s+/g, ' ').trim();
}

// 基于 token 的 Jaccard 相似度（使用对象映射，避免 Set 迭代依赖）
function jaccardSimilarity(a: string, b: string): number {
  const aa = normalizeText(a);
  const bb = normalizeText(b);
  if (!aa || !bb) return 0;
  const tokensA = aa.split(' ');
  const tokensB = bb.split(' ');

  const mapA: { [k: string]: boolean } = {};
  const mapB: { [k: string]: boolean } = {};
  for (let i = 0; i < tokensA.length; i++) {
    const t = tokensA[i];
    if (t) mapA[t] = true;
  }
  for (let j = 0; j < tokensB.length; j++) {
    const t = tokensB[j];
    if (t) mapB[t] = true;
  }

  const keysA = Object.keys(mapA);
  let intersection = 0;
  for (let i = 0; i < keysA.length; i++) {
    const k = keysA[i];
    if (mapB[k]) intersection++;
  }

  // 计算并集大小：先复制 mapB 键，再将 mapA 的键合并去重
  const unionMap: { [k: string]: boolean } = {};
  const keysB = Object.keys(mapB);
  for (let i = 0; i < keysB.length; i++) unionMap[keysB[i]] = true;
  for (let i = 0; i < keysA.length; i++) unionMap[keysA[i]] = true;
  const union = Object.keys(unionMap).length;

  return union === 0 ? 0 : intersection / union;
}

// 计算两个实体的相似度（名称为主，描述加权）
function entitySimilarity(e1: Entity, e2: Entity): number {
  const nameSim = jaccardSimilarity(e1.name || '', e2.name || '');
  const descSim = jaccardSimilarity((e1 as any).description || '', (e2 as any).description || '');
  return nameSim * 0.8 + descSim * 0.2;
}

// 计算全局 Top-N 相似对（仅同类型实体间，两两计算后整体取前N）
function buildTopPairs(entities: Entity[], topN = 3): PairSuggestion[] {
  const byType: Record<string, Entity[]> = {};
  entities.forEach(e => {
    const t = e.entity_type || '';
    if (!byType[t]) byType[t] = [];
    byType[t].push(e);
  });

  const pairs: PairSuggestion[] = [];
  Object.entries(byType).forEach(([type, list]) => {
    const n = list.length;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = list[i];
        const b = list[j];
        const score = entitySimilarity(a, b);
        // 推荐目标：频次更高者，若相同则选择 a
        const freq = (e: Entity) => (e as any).frequency ? Number((e as any).frequency) : 1;
        const target = freq(a) >= freq(b) ? a : b;
        pairs.push({ key: `${type}#${a.id}-${b.id}`, entity_type: type, a, b, score, recommendedTargetId: target.id });
      }
    }
  });

  pairs.sort((x, y) => y.score - x.score);
  return pairs.slice(0, topN);
}

const EntityDisambiguation: React.FC = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<string>('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectionMethod, setDetectionMethod] = useState<DetectionMethod>('similarity');
  const [duplicateGroups, setDuplicateGroups] = useState<PairSuggestion[]>([]);

  useEffect(() => {
    loadGraphs();
  }, []);

  useEffect(() => {
    if (!selectedGraph) {
      setEntities([]);
      setCategories([]);
      setSelectedCategory('');
      setDuplicateGroups([]);
      return;
    }
    loadCategories(selectedGraph);
    loadGraphEntities(selectedGraph);
  }, [selectedGraph]);

  useEffect(() => {
    if (!selectedCategory || !selectedGraph) return;
    // 使用分类子图的实体替换列表
    loadCategoryEntities(selectedCategory);
  }, [selectedCategory]);

  const loadGraphs = async () => {
    try {
      const list = await apiService.getGraphs();
      setGraphs(list || []);
    } catch (error) {
      console.error('加载图谱失败:', error);
      message.error('加载图谱失败');
    }
  };

  const loadCategories = async (graphId: string) => {
    try {
      const cats = await apiService.getGraphCategories(graphId);
      setCategories(cats || []);
    } catch (error) {
      // 分类是可选，不报错提示
      console.warn('加载分类失败或无分类');
      setCategories([]);
    }
  };

  const loadGraphEntities = async (graphId: string) => {
    setLoading(true);
    try {
      // 优先使用图谱子图的实体，回退到实体列表接口
      let ents: Entity[] = [];
      try {
        const subgraph = await apiService.getGraphSubgraph(graphId);
        ents = subgraph.entities || [];
      } catch (e) {
        const list = await apiService.getEntities(graphId);
        ents = list || [];
      }
      setEntities(ents);
    } catch (error) {
      console.error('加载实体失败:', error);
      message.error('加载实体失败');
    } finally {
      setLoading(false);
    }
  };

  const loadCategoryEntities = async (categoryId: string) => {
    setLoading(true);
    try {
      const subgraph = await apiService.getCategorySubgraph(categoryId);
      const ents = subgraph.entities || [];
      setEntities(ents);
    } catch (error) {
      console.error('加载分类实体失败:', error);
      message.error('加载分类实体失败');
    } finally {
      setLoading(false);
    }
  };

  const entityColumns: ColumnsType<Entity> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text>{text}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'entity_type',
      key: 'entity_type',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => <Text type="secondary">{text}</Text>,
    },
  ];

  const onDetect = async () => {
    if (detectionMethod === 'llm') {
      message.info('LLM 检测暂未实现，先用相似度检测～');
      return;
    }
    if (!entities || entities.length === 0) {
      message.warning('请先加载实体');
      return;
    }
    if (detectionMethod === 'embedding') {
      if (!selectedGraph) {
        message.warning('请先选择图谱用于嵌入相似度检测');
        return;
      }
    }
    setDetecting(true);
    try {
      let groups: any[] = [];
      if (detectionMethod === 'embedding') {
        groups = await apiService.detectEmbeddingTopPairs(selectedGraph, 3, 200);
      } else {
        groups = buildTopPairs(entities, 3);
      }
      setDuplicateGroups(groups);
      if (groups.length === 0) {
        message.success('✅ 未发现任何相似对建议');
      } else {
        message.success(`✅ 已选出全局 Top-3 相似对`);
      }
    } catch (error) {
      console.error('检测歧义失败:', error);
      message.error('检测歧义失败');
    } finally {
      setDetecting(false);
    }
  };

  const executeMergeGroup = async (group: PairSuggestion, targetId?: string) => {
    const target = targetId || group.recommendedTargetId;
    if (!target) {
      message.error('未选择合并目标');
      return;
    }
    // 该建议是一对：将另一方合并到目标
    const ids = [group.a.id, group.b.id];
    const toMerge = ids.filter(id => id !== target);
    if (toMerge.length === 0) {
      message.warning('该建议仅包含目标，无需合并');
      return;
    }

    try {
      for (let idx = 0; idx < toMerge.length; idx++) {
        const srcId = toMerge[idx];
        const req: EntityMergeRequest = {
          source_entity_id: srcId,
          target_entity_id: target,
        };
        const resp = await apiService.mergeEntities(req);
        if (!resp.success) {
          throw new Error(resp.message || '合并失败');
        }
      }
      message.success(`合并完成：${toMerge.length} 个实体已合并到目标`);
      // 刷新实体与建议
      if (selectedCategory) await loadCategoryEntities(selectedCategory);
      else if (selectedGraph) await loadGraphEntities(selectedGraph);
      const groups = buildTopPairs(entities, 3);
      setDuplicateGroups(groups);
    } catch (error) {
      console.error('合并组失败:', error);
      message.error('合并组失败');
    }
  };

  const DuplicateGroupsView: React.FC = () => {
    if (duplicateGroups.length === 0) return <EmptyHint />;
    return (
      <div>
        {duplicateGroups.map(group => (
          <Card key={group.key} size="small" style={{ marginBottom: 12 }}
                title={<span>🧩 相似对（类型: {group.entity_type}） | 分数: {typeof group.score === 'number' ? group.score.toFixed(2) : '—'}</span>}
                extra={
                  <Space>
                    <Text type="secondary">推荐目标: {group.recommendedTargetId}</Text>
                    <Button type="primary" icon={<MergeCellsOutlined />} onClick={() => executeMergeGroup(group)}>合并该对</Button>
                  </Space>
                }>
            <Row gutter={[12, 12]}>
              <Col xs={24} md={12}>
                <Card size="small" title={<span>实体 A</span>}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>{group.a.name}</Text>
                    <Tag color="blue">{group.a.entity_type}</Tag>
                    {(group.a as any).description && (
                      <Text type="secondary" style={{ display: 'block' }}>
                        {(group.a as any).description}
                      </Text>
                    )}
                    <Text type="secondary">ID: {group.a.id}</Text>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} md={12}>
                <Card size="small" title={<span>实体 B</span>}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>{group.b.name}</Text>
                    <Tag color="blue">{group.b.entity_type}</Tag>
                    {(group.b as any).description && (
                      <Text type="secondary" style={{ display: 'block' }}>
                        {(group.b as any).description}
                      </Text>
                    )}
                    <Text type="secondary">ID: {group.b.id}</Text>
                  </Space>
                </Card>
              </Col>
            </Row>
          </Card>
        ))}
      </div>
    );
  };

  const EmptyHint: React.FC = () => (
    <Card size="small">
      <Space>
        <ExclamationCircleOutlined style={{ color: '#faad14' }} />
        <Text type="secondary">未检测到歧义组或尚未执行检测</Text>
      </Space>
    </Card>
  );

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>🧩 实体歧义消除</Title>
        <Paragraph>
          选择图谱（可选分支/分类），以表格形式查看所有实体，并可执行基于相似度的歧义检测。检测出的可能重复实体以分组展示，人工确认后一键合并。
        </Paragraph>
      </div>

      {/* 选择器与动作 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <span>选择图谱：</span>
          <Select
            style={{ width: 240 }}
            placeholder="请选择图谱"
            value={selectedGraph || undefined}
            onChange={(v) => setSelectedGraph(v)}
            showSearch
            allowClear
          >
            {graphs.map(g => (
              <Option key={g.id} value={g.id}>{g.name}</Option>
            ))}
          </Select>

          <span>选择分支（分类）：</span>
          <Select
            style={{ width: 240 }}
            placeholder="可选：选择分类作为分支"
            value={selectedCategory || undefined}
            onChange={(v) => setSelectedCategory(v)}
            showSearch
            allowClear
          >
            {categories.map(c => (
              <Option key={c.id} value={c.id}>{c.name}</Option>
            ))}
          </Select>

          <Divider type="vertical" />

          <Radio.Group
            value={detectionMethod}
            onChange={(e) => setDetectionMethod(e.target.value as DetectionMethod)}
          >
            <Radio.Button value="similarity">基于相似度</Radio.Button>
            <Radio.Button value="llm">LLM（暂未实现）</Radio.Button>
            <Radio.Button value="embedding">Qwen Embedding</Radio.Button>
          </Radio.Group>

          <Button type="primary" icon={<SearchOutlined />} onClick={onDetect} loading={detecting}>
            检测歧义
          </Button>
        </Space>
      </Card>

      {/* 实体列表 */}
      <Card title={<span><NodeIndexOutlined /> 实体列表</span>} extra={<Tag>{entities.length} 项</Tag>}>
        <Table<Entity>
          rowKey="id"
          columns={entityColumns}
          dataSource={entities}
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 检测结果 */}
      <Card title={<span><CheckCircleOutlined /> 全局 Top-3 相似对</span>} style={{ marginTop: 16 }}>
        <DuplicateGroupsView />
      </Card>
    </div>
  );
};

export default EntityDisambiguation;