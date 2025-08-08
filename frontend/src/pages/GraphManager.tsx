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
  DatePicker,
  Statistic,
  Row,
  Col,
  Tooltip,
  Popconfirm,
  message
} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface GraphData {
  id: string;
  name: string;
  description: string;
  entities: number;
  relations: number;
  documents: number;
  status: 'active' | 'inactive' | 'processing';
  createdAt: string;
  updatedAt: string;
  size: string;
}

const GraphManager: React.FC = () => {
  const [graphs, setGraphs] = useState<GraphData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingGraph, setEditingGraph] = useState<GraphData | null>(null);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

  const loadGraphs = async () => {
    setLoading(true);
    // 模拟API调用
    setTimeout(() => {
      const mockData: GraphData[] = [
        {
          id: '1',
          name: 'AI技术知识图谱',
          description: '人工智能相关技术和概念的知识图谱',
          entities: 1248,
          relations: 3567,
          documents: 15,
          status: 'active',
          createdAt: '2024-01-15',
          updatedAt: '2024-01-20',
          size: '12.5 MB'
        },
        {
          id: '2',
          name: '医学文献图谱',
          description: '医学研究文献构建的知识图谱',
          entities: 2156,
          relations: 4892,
          documents: 28,
          status: 'active',
          createdAt: '2024-01-10',
          updatedAt: '2024-01-18',
          size: '18.7 MB'
        },
        {
          id: '3',
          name: '法律条文图谱',
          description: '法律法规相关的知识图谱',
          entities: 856,
          relations: 1923,
          documents: 8,
          status: 'processing',
          createdAt: '2024-01-22',
          updatedAt: '2024-01-22',
          size: '6.3 MB'
        },
        {
          id: '4',
          name: '企业管理图谱',
          description: '企业管理理论和实践的知识图谱',
          entities: 634,
          relations: 1245,
          documents: 12,
          status: 'inactive',
          createdAt: '2024-01-05',
          updatedAt: '2024-01-12',
          size: '4.8 MB'
        }
      ];
      setGraphs(mockData);
      setLoading(false);
    }, 1000);
  };

  const handleView = (record: GraphData) => {
    message.info(`查看图谱: ${record.name}`);
    // 这里可以跳转到可视化页面
  };

  const handleEdit = (record: GraphData) => {
    setEditingGraph(record);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      // 模拟删除API调用
      setGraphs(graphs.filter(g => g.id !== id));
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleBatchDelete = async () => {
    try {
      setGraphs(graphs.filter(g => !selectedRowKeys.includes(g.id)));
      setSelectedRowKeys([]);
      message.success(`批量删除 ${selectedRowKeys.length} 个图谱`);
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  const handleExport = (record: GraphData) => {
    message.info(`导出图谱: ${record.name}`);
    // 这里可以实现导出功能
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingGraph) {
        // 更新图谱
        setGraphs(graphs.map(g => 
          g.id === editingGraph.id 
            ? { ...g, ...values, updatedAt: new Date().toISOString().split('T')[0] }
            : g
        ));
        message.success('更新成功');
      } else {
        // 创建新图谱
        const newGraph: GraphData = {
          id: Date.now().toString(),
          ...values,
          entities: 0,
          relations: 0,
          documents: 0,
          status: 'inactive' as const,
          createdAt: new Date().toISOString().split('T')[0],
          updatedAt: new Date().toISOString().split('T')[0],
          size: '0 MB'
        };
        setGraphs([...graphs, newGraph]);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      setEditingGraph(null);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingGraph(null);
    form.resetFields();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'processing': return 'blue';
      case 'inactive': return 'default';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '活跃';
      case 'processing': return '处理中';
      case 'inactive': return '未激活';
      default: return '未知';
    }
  };

  const columns: ColumnsType<GraphData> = [
    {
      title: '图谱名称',
      dataIndex: 'name',
      key: 'name',
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => 
        record.name.toLowerCase().includes(value.toString().toLowerCase()) ||
        record.description.toLowerCase().includes(value.toString().toLowerCase()),
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ color: '#666', fontSize: '12px' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: '实体数',
      dataIndex: 'entities',
      key: 'entities',
      sorter: (a, b) => a.entities - b.entities,
      render: (value) => value.toLocaleString()
    },
    {
      title: '关系数',
      dataIndex: 'relations',
      key: 'relations',
      sorter: (a, b) => a.relations - b.relations,
      render: (value) => value.toLocaleString()
    },
    {
      title: '文档数',
      dataIndex: 'documents',
      key: 'documents',
      sorter: (a, b) => a.documents - b.documents
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      filters: [
        { text: '活跃', value: 'active' },
        { text: '处理中', value: 'processing' },
        { text: '未激活', value: 'inactive' }
      ],
      filteredValue: statusFilter ? [statusFilter] : null,
      onFilter: (value, record) => record.status === value,
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      )
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      sorter: (a, b) => {
        const aSize = parseFloat(a.size.replace(' MB', ''));
        const bSize = parseFloat(b.size.replace(' MB', ''));
        return aSize - bSize;
      }
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
          <Tooltip title="查看">
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
          <Tooltip title="导出">
            <Button 
              type="text" 
              icon={<DownloadOutlined />} 
              onClick={() => handleExport(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个图谱吗？"
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

  const totalEntities = graphs.reduce((sum, graph) => sum + graph.entities, 0);
  const totalRelations = graphs.reduce((sum, graph) => sum + graph.relations, 0);
  const totalDocuments = graphs.reduce((sum, graph) => sum + graph.documents, 0);
  const activeGraphs = graphs.filter(g => g.status === 'active').length;

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">🗂️ 知识图谱管理</Title>
        <Paragraph className="page-description">
          管理和维护已构建的知识图谱，查看图谱统计信息，编辑图谱属性。
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="图谱总数"
              value={graphs.length}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃图谱"
              value={activeGraphs}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总实体数"
              value={totalEntities}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总关系数"
              value={totalRelations}
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
              新建图谱
            </Button>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个图谱吗？`}
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
              placeholder="搜索图谱名称或描述"
              allowClear
              style={{ width: 250 }}
              onSearch={setSearchText}
              onChange={(e) => !e.target.value && setSearchText('')}
            />
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: 120 }}
              onChange={setStatusFilter}
            >
              <Option value="active">活跃</Option>
              <Option value="processing">处理中</Option>
              <Option value="inactive">未激活</Option>
            </Select>
          </Space>
        </div>

        {/* 表格 */}
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={graphs}
          rowKey="id"
          loading={loading}
          pagination={{
            total: graphs.length,
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
        title={editingGraph ? '编辑图谱' : '新建图谱'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ status: 'inactive' }}
        >
          <Form.Item
            name="name"
            label="图谱名称"
            rules={[{ required: true, message: '请输入图谱名称' }]}
          >
            <Input placeholder="请输入图谱名称" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="图谱描述"
            rules={[{ required: true, message: '请输入图谱描述' }]}
          >
            <Input.TextArea 
              rows={3} 
              placeholder="请输入图谱描述" 
            />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Option value="active">活跃</Option>
              <Option value="inactive">未激活</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GraphManager;