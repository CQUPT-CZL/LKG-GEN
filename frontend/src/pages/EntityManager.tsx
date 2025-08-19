import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Statistic,
  Row,
  Col,
  Tooltip,
  Popconfirm,
  message,
  Badge,
  Descriptions
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  NodeIndexOutlined,
  EyeOutlined,
  FilterOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { apiService, Entity, Graph } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const EntityManager: React.FC = () => {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isDetailVisible, setIsDetailVisible] = useState(false);
  const [editingEntity, setEditingEntity] = useState<Entity | null>(null);
  const [viewingEntity, setViewingEntity] = useState<Entity | null>(null);
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [graphFilter, setGraphFilter] = useState<string>('');
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

  // 当graphs数组更新时，重新加载实体
  useEffect(() => {
    if (graphs.length > 0) {
      loadEntities();
    }
  }, [graphs, graphFilter]);

  const loadGraphs = async () => {
    try {
      const graphList = await apiService.getGraphs();
      setGraphs(graphList);
    } catch (error) {
      console.error('加载图谱列表失败:', error);
      message.error('加载图谱列表失败');
    }
  };

  const loadEntities = async () => {
    setLoading(true);
    try {
      // 如果有选中的图谱，加载该图谱的实体
      if (graphFilter) {
        const entityList = await apiService.getEntities(graphFilter);
        setEntities(entityList);
      } else {
        // 否则加载所有图谱的实体
        const allEntities: Entity[] = [];
        for (const graph of graphs) {
          try {
            const entityList = await apiService.getEntities(graph.id);
            allEntities.push(...entityList);
          } catch (error) {
            console.error(`加载图谱 ${graph.name} 的实体失败:`, error);
          }
        }
        setEntities(allEntities);
      }
    } catch (error) {
      console.error('加载实体失败:', error);
      message.error('加载实体失败');
    } finally {
      setLoading(false);
    }
  };

  const handleView = (record: Entity) => {
    setViewingEntity(record);
    setIsDetailVisible(true);
  };

  const handleEdit = (record: Entity) => {
    setEditingEntity(record);
    form.setFieldsValue({
      ...record,
      aliases: record.aliases?.join(', ') || ''
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await apiService.deleteEntity(id);
      message.success('删除成功');
      loadEntities(); // 重新加载实体列表
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleBatchDelete = async () => {
    try {
      await Promise.all(selectedRowKeys.map(id => apiService.deleteEntity(id as string)));
      setSelectedRowKeys([]);
      message.success(`批量删除 ${selectedRowKeys.length} 个实体`);
      loadEntities(); // 重新加载实体列表
    } catch (error) {
      console.error('批量删除失败:', error);
      message.error('批量删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const aliases = values.aliases ? values.aliases.split(',').map((s: string) => s.trim()).filter(Boolean) : [];
      
      if (editingEntity) {
        // 更新实体
        await apiService.updateEntity(editingEntity.id, {
          name: values.name,
          type: values.type,
          description: values.description,
          graph_id: values.graph_id
        });
        message.success('更新成功');
      } else {
        // 创建新实体
        await apiService.createEntity({
          name: values.name,
          type: values.type,
          description: values.description,
          graph_id: values.graph_id
        });
        message.success('创建成功');
      }
      setIsModalVisible(false);
      setEditingEntity(null);
      form.resetFields();
      loadEntities(); // 重新加载实体列表
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingEntity(null);
    form.resetFields();
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      '概念': 'blue',
      '算法': 'green',
      '模型': 'orange',
      '疾病': 'red',
      '药物': 'purple',
      '人物': 'cyan',
      '组织': 'magenta'
    };
    return colors[type] || 'default';
  };

  const columns: ColumnsType<Entity> = [
    {
      title: '实体名称',
      dataIndex: 'name',
      key: 'name',
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => {
        const searchValue = value.toString().toLowerCase();
        return record.name.toLowerCase().includes(searchValue) ||
          (record.description?.toLowerCase().includes(searchValue) || false) ||
          (record.aliases?.some(alias => alias.toLowerCase().includes(searchValue)) || false);
      },
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          {record.aliases && record.aliases.length > 0 && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              别名: {record.aliases.join(', ')}
            </div>
          )}
        </div>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      filters: [
        { text: '概念', value: '概念' },
        { text: '算法', value: '算法' },
        { text: '模型', value: '模型' },
        { text: '疾病', value: '疾病' },
        { text: '药物', value: '药物' }
      ],
      filteredValue: typeFilter ? [typeFilter] : null,
      onFilter: (value, record) => record.type === value,
      render: (type) => (
        <Tag color={getTypeColor(type)}>{type}</Tag>
      )
    },
    {
      title: '频次',
      dataIndex: 'frequency',
      key: 'frequency',
      sorter: (a, b) => a.frequency - b.frequency,
      render: (frequency) => (
        <Badge 
          count={frequency} 
          style={{ backgroundColor: frequency > 100 ? '#52c41a' : '#1890ff' }}
        />
      )
    },
    {
      title: '所属图谱',
      dataIndex: 'graph_id',
      key: 'graph_id',
      render: (graphId: string) => {
        const graph = graphs.find(g => g.id === graphId);
        return graph ? graph.name : graphId;
      },
      filters: [
        { text: 'AI技术图谱', value: 'AI技术图谱' },
        { text: '医学文献图谱', value: '医学文献图谱' },
        { text: '法律条文图谱', value: '法律条文图谱' }
      ],
      filteredValue: graphFilter ? [graphFilter] : null,
      onFilter: (value, record) => record.graph_id === value
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 200 }}>{text}</Text>
        </Tooltip>
      )
    },

    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个实体吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="text" 
                danger 
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    }
  };

  const entityTypes = Array.from(new Set(entities.map(e => e.type)));
  const totalFrequency = entities.reduce((sum, entity) => sum + entity.frequency, 0);
  const avgFrequency = entities.length > 0 ? Math.round(totalFrequency / entities.length) : 0;
  const highFreqEntities = entities.filter(e => e.frequency > 100).length;

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">🏷️ 实体管理</Title>
        <Paragraph className="page-description">
          管理知识图谱中的实体，包括查看、编辑、删除和创建新实体。
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="实体总数"
              value={entities.length}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="实体类型"
              value={entityTypes.length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均频次"
              value={avgFrequency}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="高频实体"
              value={highFreqEntities}
              suffix={`/ ${entities.length}`}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Card>
        {/* 工具栏 */}
        <div className="toolbar">
          <Space wrap>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setIsModalVisible(true)}
            >
              新建实体
            </Button>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个实体吗？`}
                onConfirm={handleBatchDelete}
                okText="确定"
                cancelText="取消"
              >
                <Button danger icon={<DeleteOutlined />}>
                  批量删除 ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
            )}
          </Space>
          
          <Space wrap>
            <Input.Search
              placeholder="搜索实体名称、描述或别名"
              allowClear
              style={{ width: 280 }}
              onSearch={setSearchText}
              onChange={(e) => !e.target.value && setSearchText('')}
            />
            <Select
              placeholder="类型筛选"
              allowClear
              style={{ width: 120 }}
              onChange={setTypeFilter}
            >
              {entityTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
            <Select
              placeholder="图谱筛选"
              allowClear
              style={{ width: 150 }}
              onChange={(value) => {
                setGraphFilter(value || '');
                // 当图谱筛选改变时重新加载实体
                setTimeout(() => loadEntities(), 100);
              }}
            >
              {graphs.map((graph) => (
                <Option key={graph.id} value={graph.id}>
                  {graph.name}
                </Option>
              ))}
            </Select>
          </Space>
        </div>

        {/* 表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={entities}
          rowKey="id"
          loading={loading}
          pagination={{
            total: entities.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 编辑/新建模态框 */}
      <Modal
        title={editingEntity ? '编辑实体' : '新建实体'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
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
            rules={[{ required: true, message: '请选择实体类型' }]}
          >
            <Select placeholder="请选择实体类型">
              <Option value="概念">概念</Option>
              <Option value="算法">算法</Option>
              <Option value="模型">模型</Option>
              <Option value="疾病">疾病</Option>
              <Option value="药物">药物</Option>
              <Option value="人物">人物</Option>
              <Option value="组织">组织</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入实体描述" 
            />
          </Form.Item>
          
          <Form.Item
            name="aliases"
            label="别名"
            help="多个别名用逗号分隔"
          >
            <Input placeholder="请输入别名，用逗号分隔" />
          </Form.Item>
          
          <Form.Item
            name="graph_id"
            label="所属图谱"
            rules={[{ required: true, message: '请选择所属图谱' }]}
          >
            <Select placeholder="请选择所属图谱">
              {graphs.map((graph) => (
                <Option key={graph.id} value={graph.id}>
                  {graph.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="实体详情"
        open={isDetailVisible}
        onCancel={() => setIsDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsDetailVisible(false)}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {viewingEntity && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="实体名称" span={2}>
                <Text strong style={{ fontSize: '16px' }}>{viewingEntity.name}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={getTypeColor(viewingEntity.type)}>{viewingEntity.type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="频次">
                <Badge 
                  count={viewingEntity.frequency} 
                  style={{ backgroundColor: viewingEntity.frequency > 100 ? '#52c41a' : '#1890ff' }}
                />
              </Descriptions.Item>
              <Descriptions.Item label="所属图谱" span={2}>
                {(() => {
                  const graph = graphs.find(g => g.id === viewingEntity.graph_id);
                  return graph ? graph.name : viewingEntity.graph_id;
                })()}
              </Descriptions.Item>
              {viewingEntity.description && (
                <Descriptions.Item label="描述" span={2}>
                  {viewingEntity.description}
                </Descriptions.Item>
              )}
              {viewingEntity.aliases && viewingEntity.aliases.length > 0 && (
                <Descriptions.Item label="别名" span={2}>
                  {viewingEntity.aliases.map(alias => (
                    <Tag key={alias} style={{ marginBottom: 4 }}>{alias}</Tag>
                  ))}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="创建时间">
                {(() => {
                  const date = new Date(viewingEntity.created_at);
                  return date.toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                })()}
              </Descriptions.Item>
            </Descriptions>
            

          </div>
        )}
      </Modal>
    </div>
  );
};

export default EntityManager;