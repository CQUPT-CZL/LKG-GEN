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
  NodeIndexOutlined,
  EyeOutlined,
  DatabaseOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { apiService, Graph, SourceResource, Entity, EntityCreateRequest } from '../services/api';

const { Title, Paragraph } = Typography;
const { Option } = Select;

const EntityManager: React.FC = () => {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [documents, setDocuments] = useState<SourceResource[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<string>('');
  const [selectedDocumentId, setSelectedDocumentId] = useState<string>('');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingEntity, setEditingEntity] = useState<Entity | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

  useEffect(() => {
    if (selectedGraphId) {
      loadDocuments();
      loadEntities();
    } else {
      setDocuments([]);
      setSelectedDocumentId('');
      setEntities([]);
    }
  }, [selectedGraphId]);

  useEffect(() => {
    if (selectedDocumentId) {
      loadDocumentSubgraph();
    } else {
      setEntities([]);
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
    
    setLoading(true);
    try {
      const entityList = await apiService.getEntities(selectedGraphId);
      setEntities(entityList || []);
    } catch (error) {
      console.error('加载实体列表失败:', error);
      message.error('加载实体列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentSubgraph = async () => {
    if (!selectedDocumentId) return;
    
    setLoading(true);
    try {
      const subgraph = await apiService.getDocumentSubgraph(parseInt(selectedDocumentId));
      setEntities(subgraph.entities || []);
    } catch (error) {
      console.error('加载文档子图谱失败:', error);
      message.error('加载文档子图谱失败');
    } finally {
      setLoading(false);
    }
  };

  const handleView = (record: Entity) => {
    message.info(`查看实体: ${record.name}`);
    // 这里可以实现实体详情查看功能
  };

  const handleCreate = () => {
    if (!selectedGraphId) {
      message.warning('请先选择图谱');
      return;
    }
    setEditingEntity(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (record: Entity) => {
    setEditingEntity(record);
    form.setFieldsValue({
      name: record.name,
      type: record.type,
      description: record.properties?.description || ''
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (record: Entity) => {
    try {
      await apiService.deleteEntity(record.id);
      message.success('实体删除成功');
      loadEntities();
    } catch (error) {
      console.error('删除实体失败:', error);
      message.error('删除实体失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const entityData: EntityCreateRequest = {
        name: values.name,
        type: values.type,
        description: values.description || '',
        graph_id: selectedGraphId
      };

      if (editingEntity) {
        await apiService.updateEntity(editingEntity.id, entityData);
        message.success('实体更新成功');
      } else {
        await apiService.createEntity(entityData);
        message.success('实体创建成功');
      }

      setIsModalVisible(false);
      loadEntities();
    } catch (error) {
      console.error('保存实体失败:', error);
      message.error('保存实体失败');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingEntity(null);
    form.resetFields();
  };

  const columns: ColumnsType<Entity> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
      ellipsis: true
    },
    {
      title: '实体名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      ellipsis: true
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string) => text || '暂无描述'
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
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
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个实体吗？"
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
        <Title level={2}>🔍 实体管理</Title>
        <Paragraph>通过选择图谱和文档来查看实体信息。新的API架构中，实体通过文档子图谱进行管理。</Paragraph>
      </div>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="当前实体数"
              value={entities.length}
              prefix={<NodeIndexOutlined style={{ color: '#1890ff' }} />}
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
          </Space>
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
            disabled={!selectedGraphId}
          >
            创建实体
          </Button>
        </div>
        
        <Space wrap>
          
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
      </Card>

      {/* 实体列表 */}
      <Card>
        {!selectedGraphId ? (
          <Empty
            description="请先选择一个图谱"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Table
            columns={columns}
            dataSource={entities}
            rowKey="id"
            loading={loading}
            pagination={{
              total: entities.length,
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }}
          />
        )}
      </Card>

      {/* 创建/编辑实体模态框 */}
      <Modal
        title={editingEntity ? '编辑实体' : '创建实体'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          name="entityForm"
        >
          <Form.Item
            name="name"
            label="实体名称"
            rules={[{ required: true, message: '请输入实体名称' }]}
          >
            <Input placeholder="请输入实体名称" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="实体类型"
            rules={[{ required: true, message: '请输入实体类型' }]}
          >
            <Input placeholder="请输入实体类型" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea 
              placeholder="请输入实体描述（可选）" 
              rows={3}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EntityManager;