import React, { useState, useEffect } from 'react';
import {
  Card,
  Upload,
  Button,
  Progress,
  Typography,
  Alert,
  Space,
  Divider,
  List,
  Tag,
  message,
  Row,
  Col,
  Form,
  Input,
  Select,
  Modal,
  Table,
  Tooltip,
  Badge,
  Empty,
  Popconfirm
} from 'antd';
import {
  InboxOutlined,
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import type { UploadProps, TableColumnsType } from 'antd';
import { apiService, TaskStatus, Task, CreateTaskRequest } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

// Task interface is now imported from api.ts

interface CreateTaskForm {
  name: string;
  build_mode: 'standalone' | 'append';
  target_graph_id?: string;
  description?: string;
}

const TaskManager: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [availableGraphs, setAvailableGraphs] = useState<any[]>([]);
  const [form] = Form.useForm<CreateTaskForm>();

  // 获取任务列表
  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await apiService.getTasks();
      setTasks(response);
    } catch (error) {
      message.error('获取任务列表失败');
      console.error('获取任务列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取可用图谱列表
  const fetchAvailableGraphs = async () => {
    try {
      const graphs = await apiService.getGraphs();
      setAvailableGraphs(graphs);
    } catch (error) {
      console.error('获取图谱列表失败:', error);
    }
  };

  // 创建新任务
  const handleCreateTask = async (values: CreateTaskForm) => {
    try {
      if (uploadedFiles.length === 0) {
        message.error('请先上传文件');
        return;
      }

      const taskData: CreateTaskRequest = {
        name: values.name,
        type: 'knowledge_graph_build',
        build_mode: values.build_mode,
        target_graph_id: values.target_graph_id,
        description: values.description,
        files: uploadedFiles.map(f => f.name)
      };
      
      await apiService.createTask(taskData);
      message.success('任务创建成功！');
      setCreateModalVisible(false);
      form.resetFields();
      setUploadedFiles([]);
      fetchTasks();
    } catch (error) {
      message.error('创建任务失败');
      console.error('创建任务失败:', error);
    }
  };

  // 删除任务
  const handleDeleteTask = async (taskId: string) => {
    try {
      await apiService.deleteTask(taskId);
      message.success('任务删除成功');
      fetchTasks();
    } catch (error) {
      message.error('删除任务失败');
      console.error('删除任务失败:', error);
    }
  };

  // 查看任务详情
  const handleViewTask = (task: Task) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  };

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.md,.txt,.pdf,.doc,.docx',
    beforeUpload: (file) => {
      const isValidType = file.type === 'text/markdown' || 
                         file.type === 'text/plain' || 
                         file.type === 'application/pdf' ||
                         file.type === 'application/msword' ||
                         file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      
      if (!isValidType) {
        message.error('只支持 MD、TXT、PDF、DOC、DOCX 格式的文件');
        return false;
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('文件大小不能超过 10MB');
        return false;
      }
      
      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setUploadedFiles(info.fileList);
    },
    onRemove: (file) => {
      setUploadedFiles(prev => prev.filter(f => f.uid !== file.uid));
    }
  };

  // 获取状态标签
  const getStatusTag = (status: Task['status']) => {
    const statusConfig = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
      processing: { color: 'processing', icon: <LoadingOutlined />, text: '处理中' },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' }
    };
    
    const config = statusConfig[status];
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 表格列定义
  const columns: TableColumnsType<Task> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (text: string, record: Task) => (
        <Space>
          <Text strong>{text}</Text>
          {record.status === 'processing' && <Badge status="processing" />}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: Task['status']) => getStatusTag(status)
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: Task) => (
        <Space direction="vertical" size={0} style={{ width: '100%' }}>
          <Progress 
            percent={progress} 
            size="small" 
            status={record.status === 'failed' ? 'exception' : 'normal'}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.message}
          </Text>
        </Space>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => <Text type="secondary">{time}</Text>
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: Task) => (
        <Space>
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handleViewTask(record)}
            />
          </Tooltip>
          {record.status !== 'processing' && (
            <Popconfirm
              title="确定要删除这个任务吗？"
              onConfirm={() => handleDeleteTask(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除任务">
                <Button 
                  type="text" 
                  danger 
                  icon={<DeleteOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  useEffect(() => {
    fetchTasks();
    fetchAvailableGraphs();
    
    // 设置定时刷新
    const interval = setInterval(() => {
      fetchTasks();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card>
            <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
              <div>
                <Title level={3} style={{ margin: 0 }}>📋 任务管理</Title>
                <Paragraph type="secondary" style={{ margin: 0 }}>
                  管理知识图谱构建任务，支持异步处理和进度监控
                </Paragraph>
              </div>
              <Space>
                <Button 
                  icon={<ReloadOutlined />} 
                  onClick={fetchTasks}
                  loading={loading}
                >
                  刷新
                </Button>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => setCreateModalVisible(true)}
                >
                  创建任务
                </Button>
              </Space>
            </Space>
            
            <Table
              columns={columns}
              dataSource={tasks}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 个任务`
              }}
              locale={{
                emptyText: (
                  <Empty 
                    description="暂无任务" 
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 创建任务模态框 */}
      <Modal
        title="🚀 创建新任务"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
          setUploadedFiles([]);
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateTask}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="任务描述"
          >
            <Input.TextArea 
              placeholder="请输入任务描述（可选）" 
              rows={3}
            />
          </Form.Item>
          
          <Form.Item
            name="build_mode"
            label="构建模式"
            initialValue="standalone"
            rules={[{ required: true, message: '请选择构建模式' }]}
          >
            <Select>
              <Option value="standalone">🆕 独立构建（创建新图谱）</Option>
              <Option value="append">➕ 追加构建（扩展现有图谱）</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.build_mode !== currentValues.build_mode
            }
          >
            {({ getFieldValue }) => {
              return getFieldValue('build_mode') === 'append' ? (
                <Form.Item
                  name="target_graph_id"
                  label="目标图谱"
                  rules={[{ required: true, message: '请选择目标图谱' }]}
                >
                  <Select placeholder="请选择要扩展的图谱">
                    {availableGraphs.map(graph => (
                      <Option key={graph.id} value={graph.id}>
                        {graph.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              ) : null;
            }}
          </Form.Item>
          
          <Form.Item
            label="上传文档"
            required
          >
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 MD、TXT、PDF、DOC、DOCX 格式，单个文件不超过 10MB
              </p>
            </Dragger>
            
            {uploadedFiles.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>已选择文件：</Text>
                <List
                  size="small"
                  dataSource={uploadedFiles}
                  renderItem={(file) => (
                    <List.Item>
                      <Text>{file.name}</Text>
                      <Text type="secondary">({(file.size / 1024 / 1024).toFixed(2)} MB)</Text>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </Form.Item>
          
          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setCreateModalVisible(false);
                form.resetFields();
                setUploadedFiles([]);
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建任务
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务详情模态框 */}
      <Modal
        title={`📊 任务详情 - ${selectedTask?.name}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {selectedTask && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card size="small" title="基本信息">
              <Row gutter={[16, 8]}>
                <Col span={8}><Text strong>任务ID:</Text></Col>
                <Col span={16}><Text code>{selectedTask.id}</Text></Col>
                
                <Col span={8}><Text strong>状态:</Text></Col>
                <Col span={16}>{getStatusTag(selectedTask.status)}</Col>
                
                <Col span={8}><Text strong>进度:</Text></Col>
                <Col span={16}>
                  <Progress percent={selectedTask.progress} size="small" />
                </Col>
                
                <Col span={8}><Text strong>消息:</Text></Col>
                <Col span={16}><Text>{selectedTask.message}</Text></Col>
                
                <Col span={8}><Text strong>创建时间:</Text></Col>
                <Col span={16}><Text>{selectedTask.created_at}</Text></Col>
                
                <Col span={8}><Text strong>更新时间:</Text></Col>
                <Col span={16}><Text>{selectedTask.updated_at}</Text></Col>
              </Row>
            </Card>
            
            <Card size="small" title="文件列表">
              <List
                size="small"
                dataSource={selectedTask.files}
                renderItem={(file) => (
                  <List.Item>
                    <Text>{file}</Text>
                  </List.Item>
                )}
              />
            </Card>
            
            {selectedTask.result && (
              <Card size="small" title="处理结果">
                <Row gutter={[16, 8]}>
                  <Col span={8}><Text strong>实体数量:</Text></Col>
                  <Col span={16}><Text>{selectedTask.result.entities}</Text></Col>
                  
                  <Col span={8}><Text strong>关系数量:</Text></Col>
                  <Col span={16}><Text>{selectedTask.result.relations}</Text></Col>
                  
                  {selectedTask.result.graph_id && (
                    <>
                      <Col span={8}><Text strong>图谱ID:</Text></Col>
                      <Col span={16}><Text code>{selectedTask.result.graph_id}</Text></Col>
                    </>
                  )}
                </Row>
              </Card>
            )}
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default TaskManager;