import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  message,
  Row,
  Col,
  Tag,
  Select
} from 'antd';
import {
  PlusOutlined
} from '@ant-design/icons';
import { apiService, Category, Graph, Subgraph } from '../services/api';

const { Title } = Typography;
const { Option } = Select;

const CategoryManager: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<Graph | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [subgraph, setSubgraph] = useState<Subgraph | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedGraph) {
      loadCategoriesByGraph(selectedGraph.id);
    } else {
      setCategories([]);
    }
  }, [selectedGraph]);

  const loadData = async () => {
    setLoading(true);
    try {
      const graphsData = await apiService.getGraphs();
      setGraphs(graphsData);
      setSelectedGraph(graphsData.length > 0 ? graphsData[0] : null);
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const loadCategoriesByGraph = async (graphId: string) => {
    try {
      const list = await apiService.getGraphCategories(graphId);
      setCategories(list);
    } catch (error) {
      console.error('加载分类失败:', error);
      message.error('加载分类失败');
    }
  };

  const loadCategorySubgraph = async (categoryId: string) => {
    try {
      const subgraphData = await apiService.getCategorySubgraph(categoryId);
      setSubgraph(subgraphData);
    } catch (error) {
      console.error('加载分类子图谱失败:', error);
      message.error('加载分类子图谱失败');
    }
  };

  const handleAdd = () => {
    setEditingCategory(null);
    form.resetFields();
    // 默认父节点为当前选择的图谱
    form.setFieldsValue({ parent_id: selectedGraph?.id });
    setIsModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (!editingCategory) {
        if (!values.parent_id) {
          message.warning('请选择父节点（图谱或分类）');
          return;
        }
        await apiService.createCategory({
          name: values.name,
          parent_id: values.parent_id,
        });
        message.success('分类创建成功');
        if (selectedGraph) {
          await loadCategoriesByGraph(selectedGraph.id);
        }
      } else {
        message.info('当前API不支持更新分类功能');
      }
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
    },
    {
      title: '分类名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '父节点',
      dataIndex: 'parent_id',
      key: 'parent_id',
      width: 180,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={<Title level={3}>📁 分类管理</Title>}
            extra={
              <Space>
                <Select
                  style={{ minWidth: 220 }}
                  placeholder="选择图谱以查看分类"
                  value={selectedGraph?.id}
                  onChange={(val) => {
                    const g = graphs.find(x => x.id === val) || null;
                    setSelectedGraph(g);
                  }}
                >
                  {graphs.map(g => (
                    <Option key={g.id} value={g.id}>{g.name}</Option>
                  ))}
                </Select>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAdd}
                  disabled={!selectedGraph}
                >
                  新建分类
                </Button>
              </Space>
            }
          >
            <Table
              columns={columns}
              dataSource={categories}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
            />
          </Card>
        </Col>

        {/* 新建/编辑分类弹窗 */}
        <Modal
          title={editingCategory ? '编辑分类' : '新建分类'}
          open={isModalVisible}
          onOk={handleModalOk}
          onCancel={() => setIsModalVisible(false)}
          okText="保存"
          cancelText="取消"
          destroyOnClose
        >
          <Form form={form} layout="vertical" preserve={false}>
            <Form.Item
              label="分类名称"
              name="name"
              rules={[{ required: true, message: '请输入分类名称' }]}
            >
              <Input placeholder="请输入分类名称" />
            </Form.Item>
            <Form.Item
              label="父节点（图谱或分类）"
              name="parent_id"
              rules={[{ required: true, message: '请选择父节点' }]}
            >
              <Select placeholder="请选择父节点">
                {selectedGraph && (
                  <Option key={`graph-${selectedGraph.id}`} value={selectedGraph.id}>
                    图谱：{selectedGraph.name}
                  </Option>
                )}
                {categories.map(c => (
                  <Option key={c.id} value={c.id}>分类：{c.name}</Option>
                ))}
              </Select>
            </Form.Item>
          </Form>
        </Modal>

        {selectedCategory && (
          <Col span={24}>
            <Card title={`📊 分类详情: ${selectedCategory.name}`}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card size="small" title="基本信息">
                    <p><strong>ID:</strong> {selectedCategory.id}</p>
                    <p><strong>名称:</strong> {selectedCategory.name}</p>
                    <p><strong>父节点:</strong> {selectedCategory.parent_id}</p>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small" title="子图谱信息">
                    {subgraph ? (
                      <>
                        <p><strong>实体数量:</strong> {subgraph.entities.length}</p>
                        <p><strong>关系数量:</strong> {subgraph.relationships.length}</p>
                        <div>
                          <strong>实体类型:</strong>
                          <div style={{ marginTop: 8 }}>
                            {Array.from(new Set(subgraph.entities.map(e => e.entity_type))).map(type => (
                              <Tag key={type} color="blue">{type}</Tag>
                            ))}
                          </div>
                        </div>
                      </>
                    ) : (
                      <p>暂无子图谱数据</p>
                    )}
                  </Card>
                </Col>
              </Row>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default CategoryManager;