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
  message,
  TreeSelect
} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  DatabaseOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { apiService, Graph, Category } from '../services/api';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

// 使用API中定义的Graph类型

const GraphManager: React.FC = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingGraph, setEditingGraph] = useState<Graph | null>(null);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [categoryTree, setCategoryTree] = useState<Category | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
    loadCategoryTree();
  }, []);

  const loadCategoryTree = async () => {
    try {
      const tree = await apiService.getCategoryTree();
      setCategoryTree(tree);
    } catch (error) {
      console.error('加载分类树失败:', error);
    }
  };

  const buildCategoryTreeData = (category: Category | null): any[] => {
    if (!category) return [];
    
    const buildNode = (node: Category): any => {
      return {
        title: `${node.name} (${node.graph_ids?.length || 0})`,
        value: node.id,
        key: node.id,
        children: node.children?.map(child => buildNode(child)) || []
      };
    };
    
    return [buildNode(category)];
  };

  const loadGraphs = async () => {
    setLoading(true);
    try {
      const graphsData = await apiService.getGraphs();
      setGraphs(graphsData);
    } catch (error) {
      console.error('加载图谱列表失败:', error);
      message.error('加载图谱列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleView = (record: Graph) => {
    message.info(`查看图谱: ${record.name}`);
    // 这里可以跳转到可视化页面
  };

  const handleEdit = (record: Graph) => {
    setEditingGraph(record);
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      domain: record.domain,
      status: record.status
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await apiService.deleteGraph(id);
      message.success('删除成功');
      loadGraphs(); // 重新加载列表
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的图谱');
      return;
    }

    try {
      // 批量删除API调用
      for (const id of selectedRowKeys) {
        await apiService.deleteGraph(id as string);
      }
      setSelectedRowKeys([]);
      message.success(`成功删除 ${selectedRowKeys.length} 个图谱`);
      loadGraphs(); // 重新加载列表
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  const handleExport = (record: Graph) => {
    message.info(`导出图谱: ${record.name}`);
    // 这里可以实现导出功能
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingGraph) {
        // 更新图谱
        await apiService.updateGraph(editingGraph.id, values);
        message.success('更新成功');
      } else {
        // 创建新图谱
        await apiService.createGraph(values);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      setEditingGraph(null);
      form.resetFields();
      loadGraphs(); // 重新加载列表
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
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

  const columns: ColumnsType<Graph> = [
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
      dataIndex: 'entity_count',
      key: 'entity_count',
      sorter: (a, b) => a.entity_count - b.entity_count,
      render: (value) => value.toLocaleString()
    },
    {
      title: '关系数',
      dataIndex: 'relation_count',
      key: 'relation_count',
      sorter: (a, b) => a.relation_count - b.relation_count,
      render: (value) => value.toLocaleString()
    },
    {
      title: '分类',
      dataIndex: 'category_name',
      key: 'category_name',
      filteredValue: categoryFilter ? [categoryFilter] : null,
      onFilter: (value, record) => record.category_id === value,
      render: (categoryName, record) => (
        <Space>
          <FolderOutlined style={{ color: '#52c41a' }} />
          <Text>{categoryName || '根目录'}</Text>
        </Space>
      )
    },
    {
      title: '领域',
      dataIndex: 'domain',
      key: 'domain',
      filters: [
        { text: '通用', value: '通用' },
        { text: '钢铁', value: '钢铁' },
        { text: '冶金', value: '冶金' },
        { text: '教育', value: '教育' },
        { text: '科技', value: '科技' }
      ],
      onFilter: (value, record) => record.domain === value,
      render: (domain) => (
        <Tag color={domain === '通用' ? 'default' : 'blue'}>
          {domain || '通用'}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (text: string) => new Date(text).toLocaleDateString()
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
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      sorter: (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
      render: (text: string) => new Date(text).toLocaleDateString()
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

  const totalEntities = graphs.reduce((sum, graph) => sum + graph.entity_count, 0);
  const totalRelations = graphs.reduce((sum, graph) => sum + graph.relation_count, 0);
  const totalGraphs = graphs.length;
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
              value={totalGraphs}
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
            <TreeSelect
              placeholder="分类筛选"
              allowClear
              style={{ width: 200 }}
              treeData={buildCategoryTreeData(categoryTree)}
              onChange={setCategoryFilter}
              showSearch
              treeDefaultExpandAll
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
            name="domain"
            label="领域"
          >
            <Select placeholder="选择领域" allowClear>
              <Option value="通用">通用</Option>
              <Option value="钢铁">钢铁</Option>
              <Option value="冶金">冶金</Option>
              <Option value="教育">教育</Option>
              <Option value="科技">科技</Option>
            </Select>
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