import React, { useState, useEffect } from 'react';
import {
  Card,
  Tree,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Tag,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  DatabaseOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { apiService, Category, Graph } from '../services/api';
import type { DataNode } from 'antd/es/tree';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface TreeNode extends DataNode {
  key: string;
  title: React.ReactNode;
  children?: TreeNode[];
  category: Category;
}

const CategoryManager: React.FC = () => {
  const [categoryTree, setCategoryTree] = useState<Category | null>(null);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [categoryGraphs, setCategoryGraphs] = useState<Graph[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();

  useEffect(() => {
    loadCategoryTree();
  }, []);

  const loadCategoryTree = async () => {
    setLoading(true);
    try {
      const tree = await apiService.getCategoryTree();
      setCategoryTree(tree);
      const treeNodes = buildTreeData(tree);
      setTreeData(treeNodes ? [treeNodes] : []);
      
      // 默认选中根分类
      if (tree) {
        setSelectedCategory(tree);
        loadCategoryGraphs(tree.id);
      }
    } catch (error) {
      console.error('加载分类树失败:', error);
      message.error('加载分类树失败');
    } finally {
      setLoading(false);
    }
  };

  const buildTreeData = (category: Category): TreeNode | null => {
    if (!category) return null;

    const node: TreeNode = {
      key: category.id,
      title: (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            {category.level === 0 ? (
              <FolderOpenOutlined style={{ color: '#1890ff' }} />
            ) : (
              <FolderOutlined style={{ color: '#52c41a' }} />
            )}
            <Text strong={category.level === 0}>{category.name}</Text>
            <Tag color="blue">{category.graph_ids?.length || 0}</Tag>
          </Space>
          <Space size="small">
            <Tooltip title="添加子分类">
              <Button
                type="text"
                size="small"
                icon={<PlusOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleAddCategory(category.id);
                }}
              />
            </Tooltip>
            {category.id !== 'root' && (
              <>
                <Tooltip title="编辑分类">
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditCategory(category);
                    }}
                  />
                </Tooltip>
                <Tooltip title="删除分类">
                  <Popconfirm
                    title="确定要删除这个分类吗？"
                    description="删除分类将同时删除其下所有子分类和图谱，此操作不可恢复！"
                    onConfirm={(e) => {
                      e?.stopPropagation();
                      handleDeleteCategory(category.id);
                    }}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      type="text"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </Popconfirm>
                </Tooltip>
              </>
            )}
          </Space>
        </div>
      ),
      category,
      children: category.children?.map(child => buildTreeData(child)).filter(Boolean) as TreeNode[]
    };

    return node;
  };

  const loadCategoryGraphs = async (categoryId: string) => {
    try {
      const graphs = await apiService.getCategoryGraphs(categoryId);
      setCategoryGraphs(graphs);
    } catch (error) {
      console.error('加载分类图谱失败:', error);
      message.error('加载分类图谱失败');
    }
  };

  const handleTreeSelect = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      const selectedNode = info.node as TreeNode;
      setSelectedCategory(selectedNode.category);
      loadCategoryGraphs(selectedNode.category.id);
    }
  };

  const handleAddCategory = (parentId: string) => {
    setEditingCategory(null);
    form.resetFields();
    form.setFieldsValue({ parent_id: parentId });
    setIsModalVisible(true);
  };

  const handleEditCategory = (category: Category) => {
    setEditingCategory(category);
    form.setFieldsValue({
      name: category.name,
      description: category.description
    });
    setIsModalVisible(true);
  };

  const handleDeleteCategory = async (categoryId: string) => {
    try {
      await apiService.deleteCategory(categoryId);
      message.success('分类删除成功');
      loadCategoryTree();
    } catch (error) {
      console.error('删除分类失败:', error);
      message.error('删除分类失败');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingCategory) {
        // 更新分类
        await apiService.updateCategory(editingCategory.id, {
          name: values.name,
          description: values.description
        });
        message.success('分类更新成功');
      } else {
        // 创建分类
        await apiService.createCategory({
          name: values.name,
          description: values.description,
          parent_id: values.parent_id
        });
        message.success('分类创建成功');
      }
      
      setIsModalVisible(false);
      loadCategoryTree();
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败');
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setEditingCategory(null);
    form.resetFields();
  };

  const getParentOptions = (tree: Category, currentId?: string): { label: string; value: string }[] => {
    const options: { label: string; value: string }[] = [];
    
    const traverse = (node: Category, prefix: string = '') => {
      if (node.id !== currentId) {
        options.push({
          label: `${prefix}${node.name}`,
          value: node.id
        });
        
        if (node.children) {
          node.children.forEach(child => {
            traverse(child, `${prefix}${node.name} / `);
          });
        }
      }
    };
    
    if (tree) {
      traverse(tree);
    }
    
    return options;
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>📁 分类管理</Title>
        <Paragraph>
          管理知识图谱的分类目录结构，支持多级分类，便于组织和查找图谱。
        </Paragraph>
      </div>

      <Row gutter={24}>
        <Col span={12}>
          <Card 
            title="分类树" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => handleAddCategory('root')}
              >
                添加分类
              </Button>
            }
          >
            {loading ? (
              <div style={{ textAlign: 'center', padding: '50px 0' }}>
                加载中...
              </div>
            ) : (
              <Tree
                treeData={treeData}
                onSelect={handleTreeSelect}
                defaultExpandAll
                showLine
                showIcon={false}
              />
            )}
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="分类详情">
            {selectedCategory ? (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic 
                        title="图谱数量" 
                        value={selectedCategory.graph_ids?.length || 0} 
                        prefix={<DatabaseOutlined />}
                      />
                    </Col>
                    <Col span={12}>
                      <Statistic 
                        title="分类层级" 
                        value={selectedCategory.level} 
                        prefix={<FolderOutlined />}
                      />
                    </Col>
                  </Row>
                </div>
                
                <div style={{ marginBottom: 16 }}>
                  <Text strong>分类名称：</Text>
                  <Text>{selectedCategory.name}</Text>
                </div>
                
                <div style={{ marginBottom: 16 }}>
                  <Text strong>分类路径：</Text>
                  <Text code>{selectedCategory.path}</Text>
                </div>
                
                <div style={{ marginBottom: 16 }}>
                  <Text strong>描述：</Text>
                  <Paragraph>{selectedCategory.description || '暂无描述'}</Paragraph>
                </div>
                
                <div style={{ marginBottom: 16 }}>
                  <Text strong>创建时间：</Text>
                  <Text>{new Date(selectedCategory.created_at).toLocaleString()}</Text>
                </div>
                
                {categoryGraphs.length > 0 && (
                  <div>
                    <Text strong>包含的图谱：</Text>
                    <div style={{ marginTop: 8 }}>
                      {categoryGraphs.map(graph => (
                        <Tag key={graph.id} color="blue" style={{ marginBottom: 4 }}>
                          {graph.name}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '50px 0', color: '#999' }}>
                <InfoCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>请选择一个分类查看详情</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Modal
        title={editingCategory ? '编辑分类' : '创建分类'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          {!editingCategory && (
            <Form.Item
              name="parent_id"
              label="父分类"
              rules={[{ required: true, message: '请选择父分类' }]}
            >
              <Select placeholder="选择父分类">
                {categoryTree && getParentOptions(categoryTree).map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}
          
          <Form.Item
            name="name"
            label="分类名称"
            rules={[{ required: true, message: '请输入分类名称' }]}
          >
            <Input placeholder="请输入分类名称" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="分类描述"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入分类描述（可选）" 
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CategoryManager;