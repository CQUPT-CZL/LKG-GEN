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
  Statistic,
  Row,
  Col,
  Popconfirm,
  message
} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { apiService, Graph } from '../services/api';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph } = Typography;

const GraphManager: React.FC = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingGraph, setEditingGraph] = useState<Graph | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadGraphs();
  }, []);

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
      description: record.description
    });
    setIsModalVisible(true);
  };

  const handleDelete = async (record: Graph) => {
    try {
      await apiService.deleteGraph(record.id);
      message.success('删除成功');
      loadGraphs();
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  const handleAdd = () => {
    setEditingGraph(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingGraph) {
        // 新API没有更新接口，这里只是示例
        message.info('更新功能暂未实现');
      } else {
        await apiService.createGraph(values);
        message.success('创建成功');
      }
      
      setIsModalVisible(false);
      loadGraphs();
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

  const columns: ColumnsType<Graph> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      ellipsis: true
    },
    {
      title: '图谱名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      ellipsis: true
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text: string) => text || '暂无描述'
    },
    {
      title: '实体数量',
      dataIndex: 'entity_count',
      key: 'entity_count',
      width: 100,
      align: 'center',
      render: (count: number) => count || 0
    },
    {
      title: '关系数量',
      dataIndex: 'relation_count',
      key: 'relation_count',
      width: 100,
      align: 'center',
      render: (count: number) => count || 0
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
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
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个图谱吗？"
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

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>📊 知识图谱管理</Title>
        <Paragraph>管理您的知识图谱，包括创建、编辑、删除和查看图谱信息。</Paragraph>
      </div>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="图谱总数"
              value={graphs.length}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            新建图谱
          </Button>
          {selectedRowKeys.length > 0 && (
            <Popconfirm
              title={`确定要删除选中的 ${selectedRowKeys.length} 个图谱吗？`}
              onConfirm={() => {
                // 批量删除逻辑
                message.info('批量删除功能暂未实现');
              }}
              okText="确定"
              cancelText="取消"
            >
              <Button danger>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
      </Card>

      {/* 图谱列表 */}
      <Card>
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={graphs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
          pagination={{
            total: graphs.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 新建/编辑图谱模态框 */}
      <Modal
        title={editingGraph ? '编辑图谱' : '新建图谱'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          name="graphForm"
        >
          <Form.Item
            name="name"
            label="图谱名称"
            rules={[
              { required: true, message: '请输入图谱名称' },
              { max: 100, message: '图谱名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入图谱名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="图谱描述"
            rules={[
              { max: 500, message: '图谱描述不能超过500个字符' }
            ]}
          >
            <Input.TextArea
              rows={4}
              placeholder="请输入图谱描述（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GraphManager;