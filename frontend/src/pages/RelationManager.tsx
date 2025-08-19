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
import { apiService, Relation, Graph } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

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
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

  // 当graphs数组更新时，重新加载关系
  useEffect(() => {
    if (graphs.length > 0) {
      loadRelations();
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

  const loadRelations = async () => {
    setLoading(true);
    try {
      // 如果有选中的图谱，加载该图谱的关系
      if (graphFilter) {
        const relationList = await apiService.getRelations(graphFilter);
        const selectedGraph = graphs.find(g => g.id === graphFilter);
        const relationsWithGraphName = relationList.map(relation => ({
          ...relation,
          graphName: selectedGraph?.name || '未知图谱'
        }));
        setRelations(relationsWithGraphName);
      } else {
        // 否则加载所有图谱的关系
        const allRelations: Relation[] = [];
        for (const graph of graphs) {
          try {
            const relationList = await apiService.getRelations(graph.id);
            const relationsWithGraphName = relationList.map(relation => ({
              ...relation,
              graphName: graph.name
            }));
            allRelations.push(...relationsWithGraphName);
          } catch (error) {
            console.error(`加载图谱 ${graph.name} 的关系失败:`, error);
          }
        }
        setRelations(allRelations);
      }
    } catch (error) {
      console.error('加载关系失败:', error);
      message.error('加载关系失败');
    } finally {
      setLoading(false);
    }
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
      await apiService.deleteRelation(id);
      message.success('删除成功');
      loadRelations(); // 重新加载关系列表
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleBatchDelete = async () => {
    try {
      await Promise.all(selectedRowKeys.map(id => apiService.deleteRelation(id as string)));
      setSelectedRowKeys([]);
      message.success(`批量删除 ${selectedRowKeys.length} 个关系`);
      loadRelations(); // 重新加载关系列表
    } catch (error) {
      console.error('批量删除失败:', error);
      message.error('批量删除失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRelation) {
        // 更新关系 - 暂时使用前端更新，等待后端API实现
        setRelations(relations.map(r => 
          r.id === editingRelation.id 
            ? { ...r, ...values, updated_at: new Date().toISOString() }
            : r
        ));
        message.success('更新成功');
      } else {
        // 创建新关系 - 暂时使用前端创建，等待后端API实现
        const newRelation: Relation = {
          id: Date.now().toString(),
          source_entity_name: '',
          target_entity_name: '',
          ...values,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        setRelations([...relations, newRelation]);
        message.success('创建成功');
      }
      setIsModalVisible(false);
      setEditingRelation(null);
      form.resetFields();
    } catch (error) {
      console.error('操作失败:', error);
      message.error(editingRelation ? '更新失败' : '创建失败');
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



  const columns: ColumnsType<Relation> = [
    {
      title: '关系名称',
      dataIndex: 'name',
      key: 'name',
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => {
        const searchValue = value.toString().toLowerCase();
        return (record.source_entity_name || record.source_entity_id || '').toLowerCase().includes(searchValue) ||
          (record.description?.toLowerCase().includes(searchValue) || false) ||
          (record.target_entity_name || record.target_entity_id || '').toLowerCase().includes(searchValue) ||
          (record.relation_type || '').toLowerCase().includes(searchValue);
      },
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            <Text>{record.source_entity_name || record.source_entity_id}</Text>
            <ArrowRightOutlined style={{ margin: '0 8px', color: '#1890ff' }} />
            <Text>{record.target_entity_name || record.target_entity_id}</Text>
          </div>
        </div>
      )
    },
    {
      title: '关系类型',
      dataIndex: 'relation_type',
      key: 'relation_type',
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
      onFilter: (value, record) => record.relation_type === value,
      render: (type) => (
        <Tag color={getTypeColor(type)}>{type}</Tag>
      )
    },


    {
      title: '所属图谱',
      dataIndex: 'graphName',
      key: 'graphName',
      filters: graphs.map(graph => ({
        text: graph.name,
        value: graph.id
      })),
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

  const relationTypes = Array.from(new Set(relations.map(r => r.relation_type)));

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">🔗 关系管理</Title>
        <Paragraph className="page-description">
          管理知识图谱中的关系，包括查看、编辑、删除和创建新关系。
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }} justify="center">
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="关系总数"
              value={relations.length}
              prefix={<BranchesOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="关系类型"
              value={relationTypes.length}
              valueStyle={{ color: '#52c41a' }}
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
              onChange={(value) => {
                setGraphFilter(value || '');
                // 当图谱筛选改变时，重新加载关系
                setTimeout(() => loadRelations(), 100);
              }}
            >
              {graphs.map(graph => (
                <Option key={graph.id} value={graph.id}>{graph.name}</Option>
              ))}
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
              name="relation_type"
              label="关系类型"
              rules={[{ required: true, message: '请输入关系类型' }]}
            >
              <Input placeholder="请输入关系类型" />
            </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="source_entity_id"
                label="源实体ID"
                rules={[{ required: true, message: '请输入源实体ID' }]}
              >
                <Input placeholder="请输入源实体ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="target_entity_id"
                label="目标实体ID"
                rules={[{ required: true, message: '请输入目标实体ID' }]}
              >
                <Input placeholder="请输入目标实体ID" />
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
                name="graphId"
                label="所属图谱"
                rules={[{ required: true, message: '请选择所属图谱' }]}
              >
                <Select placeholder="请选择所属图谱">
                  {graphs.map(graph => (
                    <Option key={graph.id} value={graph.id}>{graph.name}</Option>
                  ))}
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
              <Descriptions.Item label="关系类型" span={2}>
                <Tag color={getTypeColor(viewingRelation.relation_type)}>{viewingRelation.relation_type}</Tag>
              </Descriptions.Item>

              <Descriptions.Item label="源实体">
                <Text strong>{viewingRelation.source_entity_name || viewingRelation.source_entity_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="目标实体">
                <Text strong>{viewingRelation.target_entity_name || viewingRelation.target_entity_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="所属图谱">
                {graphs.find(g => g.id === viewingRelation.graph_id)?.name || viewingRelation.graph_id}
              </Descriptions.Item>
              {viewingRelation.description && (
                <Descriptions.Item label="描述" span={2}>
                  {viewingRelation.description}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="创建时间">
                {(() => {
                  const date = new Date(viewingRelation.created_at);
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
            

            
            <Divider />
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <Space size="large" align="center">
                <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                  {viewingRelation.source_entity_name || viewingRelation.source_entity_id}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>源实体</div>
              </div>
              <ArrowRightOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#722ed1' }}>
                  {viewingRelation.relation_type}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>关系</div>
              </div>
              <ArrowRightOutlined style={{ fontSize: '24px', color: '#52c41a' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
                  {viewingRelation.target_entity_name || viewingRelation.target_entity_id}
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