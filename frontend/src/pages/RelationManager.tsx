import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Select,
  Statistic,
  Row,
  Col,
  message,
  Empty,
  Modal,
  Form,
  Input,
  Popconfirm
} from 'antd';
import {
  BranchesOutlined,
  EyeOutlined,
  DatabaseOutlined,
  ArrowRightOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { apiService, Graph, SourceResource, Relationship, RelationCreateRequest, Entity } from '../services/api';

const { Title, Paragraph } = Typography;
const { Option } = Select;

const RelationManager: React.FC = () => {
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(false);
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [documents, setDocuments] = useState<SourceResource[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<string>('');
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');
  const [entities, setEntities] = useState<Entity[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRelation, setEditingRelation] = useState<Relationship | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

  useEffect(() => {
    if (selectedGraphId) {
      loadDocuments();
      loadRelations();
      loadEntities();
    } else {
      setDocuments([]);
      setSelectedDocumentId('');
      setRelationships([]);
      setEntities([]);
    }
  }, [selectedGraphId]);

  useEffect(() => {
    if (selectedDocumentId) {
      loadDocumentSubgraph();
    } else {
      setRelationships([]);
    }
  }, [selectedDocumentId]);

  const loadGraphs = async () => {
    try {
      const graphList = await apiService.getGraphs();
      setGraphs(graphList);
    } catch (error) {
      console.error('加载图谱列表失败:', error);
      message.error('加载图谱列表失败');
    }
  };

  const loadDocuments = async () => {
    if (!selectedGraphId) return;
    
    try {
      const documentList = await apiService.getDocuments();
      // 新API中文档没有graph_ids属性，显示所有文档
      setDocuments(documentList);
    } catch (error) {
      console.error('加载文档列表失败:', error);
      message.error('加载文档列表失败');
    }
  };

  const loadEntities = async () => {
    if (!selectedGraphId) return;
    
    try {
      const entityList = await apiService.getEntities(selectedGraphId);
      setEntities(entityList || []);
    } catch (error) {
      console.error('加载实体列表失败:', error);
    }
  };

  const loadRelations = async () => {
    if (!selectedGraphId) return;
    
    setLoading(true);
    try {
      const relationList = await apiService.getRelations(selectedGraphId);
      setRelationships(relationList || []);
    } catch (error) {
      console.error('加载关系列表失败:', error);
      message.error('加载关系列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentSubgraph = async () => {
    if (!selectedDocumentId) return;
    
    setLoading(true);
    try {
      const subgraph = await apiService.getDocumentSubgraph(parseInt(selectedDocumentId));
      setRelationships(subgraph.relationships || []);
    } catch (error) {
      console.error('加载文档子图谱失败:', error);
      message.error('加载文档子图谱失败');
    } finally {
      setLoading(false);
    }
  };

  const handleView = (record: Relationship) => {
    message.info(`查看关系: ${record.relation_type}`);
    // 这里可以实现关系详情查看功能
  };

  const handleCreate = () => {
    if (!selectedGraphId) {
      message.warning('请先选择图谱');
      return;
    }
    if (entities.length < 2) {
      message.warning('至少需要2个实体才能创建关系');
      return;
    }
    setEditingRelation(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (record: Relationship) => {
    setEditingRelation(record);
    form.setFieldsValue({
      source_entity_id: record.source_entity_id,
      target_entity_id: record.target_entity_id,
      relation_type: record.relation_type,
      confidence: record.confidence || 1.0,
      description: record.description || ''
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (record: Relationship) => {
    try {
      await apiService.deleteRelation(record.id);
      message.success('关系删除成功');
      loadRelations();
    } catch (error) {
      console.error('删除关系失败:', error);
      message.error('删除关系失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const relationData: RelationCreateRequest = {
        source_entity_id: values.source_entity_id,
        target_entity_id: values.target_entity_id,
        relation_type: values.relation_type,
        confidence: values.confidence || 1.0,
        description: values.description || '',
        graph_id: selectedGraphId
      };

      await apiService.createRelation(relationData);
      message.success('关系创建成功');
      setIsModalVisible(false);
      loadRelations();
    } catch (error) {
      console.error('保存关系失败:', error);
      message.error('保存关系失败');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingRelation(null);
    form.resetFields();
  };

  // 根据实体ID获取实体名称
  const getEntityNameById = (entityId: string): string => {
    const entity = entities.find(e => e.id === entityId);
    return entity ? `${entity.name} (${entity.entity_type})` : entityId;
  };

  const columns: ColumnsType<Relationship> = [
    {
      title: '起始节点',
      dataIndex: 'source_entity_id',
      key: 'source_entity_id',
      ellipsis: true,
      render: (entityId: string) => (
        <span style={{ color: '#1890ff' }}>{getEntityNameById(entityId)}</span>
      )
    },
    {
      title: '关系类型',
      dataIndex: 'relation_type',
      key: 'relation_type',
      ellipsis: true,
      render: (text: string) => (
         <span style={{ 
           backgroundColor: '#f0f0f0',
           color: '#666',
           padding: '4px 8px',
           borderRadius: '4px',
           fontSize: '12px',
           fontWeight: '500',
           display: 'inline-block'
         }}>
           {text}
         </span>
       )
    },
    {
      title: '结束节点',
      dataIndex: 'target_entity_id',
      key: 'target_entity_id',
      ellipsis: true,
      render: (entityId: string) => (
        <span style={{ color: '#fa8c16' }}>{getEntityNameById(entityId)}</span>
      )
    },
    {
      title: '属性',
      key: 'properties',
      ellipsis: true,
      render: (_, record: Relationship) => {
        const properties = [];
        if (record.description) {
          properties.push(`描述: ${record.description}`);
        }
        if (record.confidence !== undefined) {
          properties.push(`置信度: ${record.confidence}`);
        }
        return properties.length > 0 ? properties.join('; ') : '无属性';
      }
    },
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      fixed: 'right',
      render: (_, record) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            disabled
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个关系吗？"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>🔗 关系管理</Title>
        <Paragraph>通过选择图谱和文档来查看关系信息。新的API架构中，关系通过文档子图谱进行管理。</Paragraph>
      </div>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="当前关系数"
              value={relationships.length}
              prefix={<BranchesOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="可用图谱数"
              value={graphs.length}
              prefix={<DatabaseOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="可用文档数"
              value={documents.length}
              prefix={<DatabaseOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 筛选器 */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Space wrap>
            <div>
              <span style={{ marginRight: 8 }}>选择图谱:</span>
              <Select
                placeholder="请选择图谱"
                style={{ width: 200 }}
                value={selectedGraphId || undefined}
                onChange={(value) => {
                  setSelectedGraphId(value || '');
                  setSelectedDocumentId('');
                }}
                allowClear
              >
                {graphs.map(graph => (
                  <Option key={graph.id} value={graph.id}>
                    {graph.name}
                  </Option>
                ))}
              </Select>
            </div>
            
            {selectedGraphId && (
              <div>
                <span style={{ marginRight: 8 }}>选择文档:</span>
                <Select
                  placeholder="请选择文档"
                  style={{ width: 200 }}
                  value={selectedDocumentId || undefined}
                  onChange={(value) => setSelectedDocumentId(value || '')}
                  allowClear
                >
                  {documents.map(doc => (
                    <Option key={doc.id} value={doc.id.toString()}>
                      {doc.filename}
                    </Option>
                  ))}
                </Select>
              </div>
            )}
          </Space>
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
            disabled={!selectedGraphId}
          >
            创建关系
          </Button>
        </div>
      </Card>

      {/* 关系列表 */}
      <Card>
        {!selectedGraphId ? (
          <Empty
            description="请先选择一个图谱"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={relationships}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1400 }}
            pagination={{
              total: relationships.length,
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }}
          />
        )}
      </Card>

      {/* 创建/编辑关系模态框 */}
      <Modal
        title={editingRelation ? '编辑关系' : '创建关系'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            confidence: 1.0
          }}
        >
          <Form.Item
            name="source_entity_id"
            label="源实体"
            rules={[{ required: true, message: '请选择源实体' }]}
          >
            <Select placeholder="请选择源实体">
              {entities.map(entity => (
                <Option key={entity.id} value={entity.id}>
                  {entity.name} ({entity.entity_type})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="target_entity_id"
            label="目标实体"
            rules={[{ required: true, message: '请选择目标实体' }]}
          >
            <Select placeholder="请选择目标实体">
              {entities.map(entity => (
                <Option key={entity.id} value={entity.id}>
                  {entity.name} ({entity.entity_type})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="relation_type"
            label="关系类型"
            rules={[{ required: true, message: '请输入关系类型' }]}
          >
            <Input placeholder="例如：包含、属于、关联等" />
          </Form.Item>

          <Form.Item
            name="confidence"
            label="置信度"
            rules={[{ required: true, message: '请输入置信度' }]}
          >
            <Input type="number" min={0} max={1} step={0.1} placeholder="0.0 - 1.0" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={3} placeholder="关系的详细描述（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RelationManager;