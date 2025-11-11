import React, { useEffect, useMemo, useState } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Space,
  Select,
  Button,
  Tag,
  Divider,
  message,
  Modal,
  Form,
  Input
} from 'antd';
import { SearchOutlined, ExclamationCircleOutlined, MergeCellsOutlined } from '@ant-design/icons';
import { apiService, Graph, Category, Entity, EntityMergeRequest, BasicEntityInfoDTO } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

interface PairSuggestion {
  key: string; // pair key
  entity_type: string;
  a: BasicEntityInfoDTO | Entity;
  b: BasicEntityInfoDTO | Entity;
  score: number;
  recommendedTargetId?: string; // 频次更高者为目标
}

// 仅使用 MCP（嵌入）相似度建议

const EntityDisambiguation: React.FC = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<string>('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  // 建议与编辑状态
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [allSuggestions, setAllSuggestions] = useState<PairSuggestion[]>([]);
  const [ignoredKeys, setIgnoredKeys] = useState<string[]>([]);
  const [mergeVisible, setMergeVisible] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<PairSuggestion | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

  useEffect(() => {
    if (!selectedGraph) {
      setCategories([]);
      setSelectedCategory('');
      setAllSuggestions([]);
      setIgnoredKeys([]);
      return;
    }
    loadCategories(selectedGraph);
  }, [selectedGraph]);

  useEffect(() => {
    if (!selectedCategory || !selectedGraph) return;
    // 分类切换时清空建议
    setAllSuggestions([]);
    setIgnoredKeys([]);
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

  // 当前页面不再展示实体列表，因此移除实体加载逻辑

  const visibleSuggestions = useMemo(() => {
    const filtered = allSuggestions.filter(g => !ignoredKeys.includes(g.key));
    return filtered.slice(0, 10);
  }, [allSuggestions, ignoredKeys]);

  const onDetect = async () => {
    if (!selectedGraph) {
      message.warning('请先选择图谱用于 MCP 检测');
      return;
    }
    setDetecting(true);
    try {
      // 一次性获取更多建议，通过“忽略”让位
      const groups = await apiService.detectEmbeddingTopPairs(selectedGraph, 10, 200);
      setAllSuggestions(groups as unknown as PairSuggestion[]);
      if (!groups || groups.length === 0) {
        message.success('✅ 未发现任何相似对建议');
      } else {
        message.success('✅ 已获得 MCP 相似对建议（当前展示最多 10 条）');
      }
    } catch (error) {
      console.error('检测歧义失败:', error);
      message.error('检测歧义失败');
    } finally {
      setDetecting(false);
    }
  };

  const openMergeModal = (group: PairSuggestion) => {
    setSelectedGroup(group);
    const a = group.a as BasicEntityInfoDTO;
    form.setFieldsValue({
      name: a.name,
      entity_type: a.entity_type,
      description: (a as any).description || ''
    });
    setMergeVisible(true);
  };

  const handleMergeConfirm = async () => {
    if (!selectedGroup) return;
    try {
      const values = await form.validateFields();
      const targetId = (selectedGroup.a as any).id as string; // 默认第一个为目标
      const sourceId = (selectedGroup.b as any).id as string; // 第二个合并到第一个

      const req: EntityMergeRequest = {
        source_entity_id: sourceId,
        target_entity_id: targetId,
        merged_name: values.name,
        merged_description: values.description || ''
      };

      const resp = await apiService.mergeEntities(req);
      if (!resp.success) {
        throw new Error(resp.message || '合并失败');
      }

      // 若修改了类型，额外更新目标实体类型
      if (selectedGraph) {
        const updateData = {
          name: values.name,
          entity_type: values.entity_type,
          description: values.description || '',
          graph_id: selectedGraph
        };
        try {
          await apiService.updateEntity(targetId, updateData as any);
        } catch (e) {
          console.warn('更新实体类型失败（已合并成功）');
        }
      }

      message.success('✅ 合并成功，信息已更新');
      setMergeVisible(false);
      setSelectedGroup(null);

      // 将该建议标记为忽略，空位由下一条补上
      setIgnoredKeys(prev => [...prev, selectedGroup.key]);

      // 重新检测以确保最新建议
      onDetect();
    } catch (error) {
      console.error('合并组失败:', error);
      message.error('合并组失败');
    }
  };

  const handleIgnore = (group: PairSuggestion) => {
    setIgnoredKeys(prev => [...prev, group.key]);
    message.success('已忽略该建议，下一条已补位 ✅');
  };

  const DuplicateGroupsView: React.FC = () => {
    if (visibleSuggestions.length === 0) return <EmptyHint />;
    return (
      <div>
        {visibleSuggestions.map(group => (
          <Card key={group.key} size="small" style={{ marginBottom: 12 }}
                title={<span>🧩 相似对（类型: {group.entity_type}） | 分数: {typeof group.score === 'number' ? group.score.toFixed(2) : '—'}</span>}
                extra={
                  <Space>
                    <Button onClick={() => handleIgnore(group)}>忽略该对</Button>
                    <Button type="primary" icon={<MergeCellsOutlined />} onClick={() => openMergeModal(group)}>合并该对</Button>
                  </Space>
                }>
            <Row gutter={[12, 12]}>
              <Col xs={24} md={12}>
                <Card size="small" title={<span>实体 A</span>}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>{(group.a as any).name}</Text>
                    <Tag color="blue">{(group.a as any).entity_type}</Tag>
                    {(group.a as any).description && (
                      <Text type="secondary" style={{ display: 'block' }}>
                        {(group.a as any).description}
                      </Text>
                    )}
                    <Text type="secondary">ID: {(group.a as any).id}</Text>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} md={12}>
                <Card size="small" title={<span>实体 B</span>}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>{(group.b as any).name}</Text>
                    <Tag color="blue">{(group.b as any).entity_type}</Tag>
                    {(group.b as any).description && (
                      <Text type="secondary" style={{ display: 'block' }}>
                        {(group.b as any).description}
                      </Text>
                    )}
                    <Text type="secondary">ID: {(group.b as any).id}</Text>
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
          选择图谱（可选分支/分类），使用 MCP 嵌入相似度进行检测。对可能重复实体进行人工确认，并可在合并时编辑信息。
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
          <Text type="secondary">检测方式：MCP（嵌入相似度）</Text>

          <Button type="primary" icon={<SearchOutlined />} onClick={onDetect} loading={detecting}>
            MCP 检测
          </Button>
        </Space>
      </Card>

      {/* 检测结果 */}
      <Card title={<span>✅ 当前建议（最多展示 10 条）</span>} style={{ marginTop: 16 }}>
        <DuplicateGroupsView />
      </Card>

      {/* 合并弹窗：默认用实体A信息，可编辑 */}
      <Modal
        title="🔗 合并实体（默认使用实体 A 信息）"
        open={mergeVisible}
        onOk={handleMergeConfirm}
        onCancel={() => setMergeVisible(false)}
        okText="确认合并"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入合并后的名称' }]}> 
            <Input placeholder="请输入合并后的名称" />
          </Form.Item>
          <Form.Item name="entity_type" label="类型" rules={[{ required: true, message: '请输入实体类型' }]}> 
            <Input placeholder="请输入实体类型" />
          </Form.Item>
          <Form.Item name="description" label="描述"> 
            <Input.TextArea rows={4} placeholder="可选：请输入合并后的描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EntityDisambiguation;