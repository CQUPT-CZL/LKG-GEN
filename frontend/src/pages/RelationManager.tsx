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
  Descriptions,
  Divider
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  BranchesOutlined,
  EyeOutlined,
  ArrowRightOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface Relation {
  id: string;
  name: string;
  type: string;
  sourceEntity: string;
  targetEntity: string;
  description?: string;
  properties?: Record<string, any>;
  confidence: number;
  frequency: number;
  graphId: string;
  graphName: string;
  createdAt: string;
  updatedAt: string;
}

const RelationManager: React.FC = () => {
  const [relations, setRelations] = useState<Relation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isDetailVisible, setIsDetailVisible] = useState(false);
  const [editingRelation, setEditingRelation] = useState<Relation | null>(null);
  const [viewingRelation, setViewingRelation] = useState<Relation | null>(null);
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [graphFilter, setGraphFilter] = useState<string>('');
  const [form] = Form.useForm();

  useEffect(() => {
    loadRelations();
  }, []);

  const loadRelations = async () => {
    setLoading(true);
    // 模拟API调用
    setTimeout(() => {
      const mockData: Relation[] = [
        {
          id: '1',
          name: '包含',
          type: '层次关系',
          sourceEntity: '人工智能',
          targetEntity: '机器学习',
          description: '人工智能包含机器学习作为其子领域',
          properties: { strength: '强', direction: '单向' },
          confidence: 0.95,
          frequency: 89,
          graphId: '1',
          graphName: 'AI技术图谱',
          createdAt: '2024-01-15',
          updatedAt: '2024-01-20'
        },
        {
          id: '2',
          name: '基于',
          type: '依赖关系',
          sourceEntity: '深度学习',
          targetEntity: '神经网络',
          description: '深度学习基于神经网络技术实现',
          properties: { strength: '强', direction: '单向' },
          confidence: 0.92,
          frequency: 76,
          graphId: '1',
          graphName: 'AI技术图谱',
          createdAt: '2024-01-16',
          updatedAt: '2024-01-19'
        },
        {
          id: '3',
          name: '应用于',
          type: '应用关系',
          sourceEntity: '机器学习',
          targetEntity: '图像识别',
          description: '机器学习技术应用于图像识别领域',
          properties: { strength: '中', direction: '单向' },
          confidence: 0.88,
          frequency: 54,
          graphId: '1',
          graphName: 'AI技术图谱',
          createdAt: '2024-01-17',
          updatedAt: '2024-01-18'
        },
        {
          id: '4',
          name: '相似于',
          type: '相似关系',
          sourceEntity: '卷积神经网络',
          targetEntity: '循环神经网络',
          description: '两种神经网络架构在某些方面具有相似性',
          properties: { strength: '弱', direction: '双向' },
          confidence: 0.72,
          frequency: 23,
          graphId: '1',
          graphName: 'AI技术图谱',
          createdAt: '2024-01-18',
          updatedAt: '2024-01-20'
        },
        {
          id: '5',
          name: '导致',
          type: '因果关系',
          sourceEntity: '高血糖',
          targetEntity: '糖尿病',
          description: '持续高血糖状态可能导致糖尿病',
          properties: { strength: '强', direction: '单向' },
          confidence: 0.89,
          frequency: 156,
          graphId: '2',
          graphName: '医学文献图谱',
          createdAt: '2024-01-10',
          updatedAt: '2024-01-18'
        },
        {
          id: '6',
          name: '治疗',
          type: '治疗关系',
          sourceEntity: '胰岛素',
          targetEntity: '糖尿病',
          description: '胰岛素用于治疗糖尿病',
          properties: { strength: '强', direction: '单向' },
          confidence: 0.96,
          frequency: 234,
          graphId: '2',
          graphName: '医学文献图谱',
          createdAt: '2024-01-10',
          updatedAt: '2024-01-17'
        },
        {
          id: '7',
          name: '副作用',
          type: '副作用关系',
          sourceEntity: '胰岛素',
          targetEntity: '低血糖',
          description: '胰岛素使用可能引起低血糖副作用',
          properties: { strength: '中', direction: '单向' },
          confidence: 0.78,
          frequency: 67,
          graphId: '2',
          graphName: '医学文献图谱',
          createdAt: '2024-01-12',
          updatedAt: '2024-01-16'
        }
      ];
      setRelations(mockData);
      setLoading(false);
    }, 1000);
  };

  const handleView = (record: Relation) => {
    setViewingRelation(record);
    setIsDetailVisible(true);
  };

  const handleEdit = (record: Relation) => {
    setEditingRelation(record);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      setRelations(relations.filter(r => r.id !== id));
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleBatchDelete = async () => {
    try {
      setRelations(relations.filter(r => !selectedRowKeys.includes(r.id)));
      setSelectedRowKeys([]);
      message.success(`批量删除 ${selectedRowKeys.length} 个关系`);
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRelation) {
        // 更新关系
        setRelations(relations.map(r => 
          r.id === editingRelation.id 
            ? { ...r, ...values, updatedAt: new Date().toISOString().split('T')[0] }
            : r
        ));
        message.success('更新成功');
      } else {
        // 创建新关系
        const newRelation: Relation = {
          id: Date.now().toString(),
          ...values,
          frequency: 0,
          createdAt: new Date().toISOString().split('T')[0],
          updatedAt: new Date().toISOString().split('T')[0]
        };
        setRelations([...relations, newRelation]);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      setEditingRelation(null);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingRelation(null);
    form.resetFields();
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      '层次关系': 'blue',
      '依赖关系': 'green',
      '应用关系': 'orange',
      '相似关系': 'purple',
      '因果关系': 'red',
      '治疗关系': 'cyan',
      '副作用关系': 'magenta'
    };
    return colors[type] || 'default';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return '#52c41a';
    if (confidence >= 0.8) return '#1890ff';
    if (confidence >= 0.7) return '#fa8c16';
    return '#f5222d';
  };

  const columns: ColumnsType<Relation> = [
    {
      title: '关系名称',
      dataIndex: 'name',
      key: 'name',
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => {
        const searchValue = value.toString().toLowerCase();
        return record.name.toLowerCase().includes(searchValue) ||
          (record.description?.toLowerCase().includes(searchValue) || false) ||
          record.sourceEntity.toLowerCase().includes(searchValue) ||
          record.targetEntity.toLowerCase().includes(searchValue);
      },
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            <Text>{record.sourceEntity}</Text>
            <ArrowRightOutlined style={{ margin: '0 8px', color: '#1890ff' }} />
            <Text>{record.targetEntity}</Text>
          </div>
        </div>
      )
    },
    {
      title: '关系类型',
      dataIndex: 'type',
      key: 'type',
      filters: [
        { text: '层次关系', value: '层次关系' },
        { text: '依赖关系', value: '依赖关系' },
        { text: '应用关系', value: '应用关系' },
        { text: '相似关系', value: '相似关系' },
        { text: '因果关系', value: '因果关系' },
        { text: '治疗关系', value: '治疗关系' },
        { text: '副作用关系', value: '副作用关系' }
      ],
      filteredValue: typeFilter ? [typeFilter] : null,
      onFilter: (value, record) => record.type === value,
      render: (type) => (
        <Tag color={getTypeColor(type)}>{type}</Tag>
      )
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      sorter: (a, b) => a.confidence - b.confidence,
      render: (confidence) => (
        <div>
          <div 
            style={{ 
              color: getConfidenceColor(confidence),
              fontWeight: 'bold'
            }}
          >
            {(confidence * 100).toFixed(1)}%
          </div>
        </div>
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
      dataIndex: 'graphName',
      key: 'graphName',
      filters: [
        { text: 'AI技术图谱', value: 'AI技术图谱' },
        { text: '医学文献图谱', value: '医学文献图谱' },
        { text: '法律条文图谱', value: '法律条文图谱' }
      ],
      filteredValue: graphFilter ? [graphFilter] : null,
      onFilter: (value, record) => record.graphName === value
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
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      sorter: (a, b) => new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime()
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
              title="确定要删除这个关系吗？"
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

  const relationTypes = Array.from(new Set(relations.map(r => r.type)));
  const totalFrequency = relations.reduce((sum, relation) => sum + relation.frequency, 0);
  const avgConfidence = relations.length > 0 
    ? Math.round(relations.reduce((sum, r) => sum + r.confidence, 0) / relations.length * 100) 
    : 0;
  const highConfidenceRelations = relations.filter(r => r.confidence >= 0.9).length;

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">🔗 关系管理</Title>
        <Paragraph className="page-description">
          管理知识图谱中的关系，包括查看、编辑、删除和创建新关系。
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="关系总数"
              value={relations.length}
              prefix={<BranchesOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="关系类型"
              value={relationTypes.length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均置信度"
              value={avgConfidence}
              suffix="%"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="高置信度关系"
              value={highConfidenceRelations}
              suffix={`/ ${relations.length}`}
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
              新建关系
            </Button>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个关系吗？`}
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
              placeholder="搜索关系名称、实体或描述"
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
              {relationTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
            <Select
              placeholder="图谱筛选"
              allowClear
              style={{ width: 150 }}
              onChange={setGraphFilter}
            >
              <Option value="AI技术图谱">AI技术图谱</Option>
              <Option value="医学文献图谱">医学文献图谱</Option>
              <Option value="法律条文图谱">法律条文图谱</Option>
            </Select>
          </Space>
        </div>

        {/* 表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={relations}
          rowKey="id"
          loading={loading}
          pagination={{
            total: relations.length,
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
        title={editingRelation ? '编辑关系' : '新建关系'}
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
            label="关系名称"
            rules={[{ required: true, message: '请输入关系名称' }]}
          >
            <Input placeholder="请输入关系名称" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="关系类型"
            rules={[{ required: true, message: '请选择关系类型' }]}
          >
            <Select placeholder="请选择关系类型">
              <Option value="层次关系">层次关系</Option>
              <Option value="依赖关系">依赖关系</Option>
              <Option value="应用关系">应用关系</Option>
              <Option value="相似关系">相似关系</Option>
              <Option value="因果关系">因果关系</Option>
              <Option value="治疗关系">治疗关系</Option>
              <Option value="副作用关系">副作用关系</Option>
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="sourceEntity"
                label="源实体"
                rules={[{ required: true, message: '请输入源实体' }]}
              >
                <Input placeholder="请输入源实体" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="targetEntity"
                label="目标实体"
                rules={[{ required: true, message: '请输入目标实体' }]}
              >
                <Input placeholder="请输入目标实体" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入关系描述" 
            />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="confidence"
                label="置信度"
                rules={[{ required: true, message: '请输入置信度' }]}
              >
                <Input 
                  type="number" 
                  min={0} 
                  max={1} 
                  step={0.01}
                  placeholder="0.00 - 1.00" 
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="graphId"
                label="所属图谱"
                rules={[{ required: true, message: '请选择所属图谱' }]}
              >
                <Select placeholder="请选择所属图谱">
                  <Option value="1">AI技术图谱</Option>
                  <Option value="2">医学文献图谱</Option>
                  <Option value="3">法律条文图谱</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="关系详情"
        open={isDetailVisible}
        onCancel={() => setIsDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsDetailVisible(false)}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {viewingRelation && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="关系名称" span={2}>
                <Text strong style={{ fontSize: '16px' }}>{viewingRelation.name}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="关系类型">
                <Tag color={getTypeColor(viewingRelation.type)}>{viewingRelation.type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                <span style={{ color: getConfidenceColor(viewingRelation.confidence), fontWeight: 'bold' }}>
                  {(viewingRelation.confidence * 100).toFixed(1)}%
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="源实体">
                <Text strong>{viewingRelation.sourceEntity}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="目标实体">
                <Text strong>{viewingRelation.targetEntity}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="频次">
                <Badge 
                  count={viewingRelation.frequency} 
                  style={{ backgroundColor: viewingRelation.frequency > 100 ? '#52c41a' : '#1890ff' }}
                />
              </Descriptions.Item>
              <Descriptions.Item label="所属图谱">
                {viewingRelation.graphName}
              </Descriptions.Item>
              {viewingRelation.description && (
                <Descriptions.Item label="描述" span={2}>
                  {viewingRelation.description}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="创建时间">
                {viewingRelation.createdAt}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {viewingRelation.updatedAt}
              </Descriptions.Item>
            </Descriptions>
            
            {viewingRelation.properties && Object.keys(viewingRelation.properties).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>扩展属性</Title>
                <Descriptions column={1} size="small" bordered>
                  {Object.entries(viewingRelation.properties).map(([key, value]) => (
                    <Descriptions.Item key={key} label={key}>
                      {Array.isArray(value) ? value.join(', ') : String(value)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </div>
            )}
            
            <Divider />
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <Space size="large" align="center">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                    {viewingRelation.sourceEntity}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>源实体</div>
                </div>
                <ArrowRightOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#722ed1' }}>
                    {viewingRelation.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>关系</div>
                </div>
                <ArrowRightOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                    {viewingRelation.targetEntity}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>目标实体</div>
                </div>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RelationManager;