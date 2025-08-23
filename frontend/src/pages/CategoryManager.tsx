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
  Popconfirm,
  Row,
  Col,
  Tag,
  Select
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { apiService, Category, Graph, SourceResource, Subgraph } from '../services/api';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const CategoryManager: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [subgraph, setSubgraph] = useState<Subgraph | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 注意：新API中没有获取所有分类的接口，这里只能获取图谱列表
      const graphsData = await apiService.getGraphs();
      setGraphs(graphsData);
      // 暂时设置空的分类列表，因为API不支持获取所有分类
      setCategories([]);
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
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

  const handleView = (category: Category) => {
    setSelectedCategory(category);
    loadCategorySubgraph(category.id);
  };

  const handleAdd = () => {
    setEditingCategory(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (category: Category) => {
    setEditingCategory(category);
    form.setFieldsValue({
      name: category.name
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (categoryId: string) => {
    try {
      await apiService.deleteCategory(categoryId);
      message.success('分类删除成功');
      loadData();
      if (selectedCategory?.id === categoryId) {
        setSelectedCategory(null);
        setSubgraph(null);
      }
    } catch (error) {
      console.error('删除分类失败:', error);
      message.error('删除分类失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingCategory) {
        // 注意：新API中没有更新分类的接口，这里只是示例
        message.info('当前API不支持更新分类功能');
      } else {
        await apiService.createCategory({
          name: values.name,
          parent_id: 'root'
        });
        message.success('分类创建成功');
        loadData();
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
      width: 80,
    },
    {
      title: '分类名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Category) => (
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
             title="确定要删除这个分类吗？"
             onConfirm={() => handleDelete(record.id)}
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
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={<Title level={3}>📁 分类管理</Title>}
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleAdd}
              >
                新建分类
              </Button>
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
        
        {selectedCategory && (
          <Col span={24}>
            <Card title={`📊 分类详情: ${selectedCategory.name}`}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card size="small" title="基本信息">
                    <p><strong>ID:</strong> {selectedCategory.id}</p>
                    <p><strong>名称:</strong> {selectedCategory.name}</p>
                    <p><strong>名称:</strong> {selectedCategory.name}</p>
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
                            {Array.from(new Set(subgraph.entities.map(e => e.type))).map(type => (
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

      <Modal
        title={editingCategory ? '编辑分类' : '新建分类'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          name="categoryForm"
        >
          <Form.Item
            name="name"
            label="分类名称"
            rules={[
              { required: true, message: '请输入分类名称' },
              { max: 100, message: '分类名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入分类名称" />
          </Form.Item>
          

        </Form>
      </Modal>
    </div>
  );
};

export default CategoryManager;