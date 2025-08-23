import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Upload, 
  message, 
  Space, 
  Tag, 
  Popconfirm,
  Alert,
  Typography,
  Progress,
  Badge,
  Tooltip,
  Row,
  Col,
  Card,
  Empty,
  List,
  Divider,
  Descriptions
} from 'antd';
import { 
  PlusOutlined, 
  UploadOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  InboxOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { apiService, Graph, Task, TaskStatus, TaskType, CreateTaskRequest } from '../services/api';
import type { UploadProps, TableColumnsType } from 'antd';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

interface CreateTaskForm {
  name: string;
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
  const [availableGraphs, setAvailableGraphs] = useState<Graph[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null);
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
      if (!selectedGraphId) {
        message.error('请选择目标图谱');
        return;
      }

      if (uploadedFiles.length === 0) {
        message.error('请上传至少一个文档');
        return;
      }

      const taskData: CreateTaskRequest = {
        name: values.name,
        type: TaskType.KNOWLEDGE_GRAPH_BUILD,
        target_graph_id: selectedGraphId,
        description: values.description,
        files: uploadedFiles.map(file => file.response?.file_id || file.uid)
      };

      await apiService.createTask(taskData);
      message.success('任务创建成功');
      setCreateModalVisible(false);
      form.resetFields();
      setUploadedFiles([]);
      setSelectedGraphId(null);
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
  const handleViewTask = async (task: Task) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  };

  // 执行任务
  const handleExecuteTask = async (taskId: string) => {
    try {
      // 对于已创建的任务，这里可以添加重新执行的逻辑
      // 目前任务创建后会自动开始处理
      message.success('任务重新启动');
      fetchTasks();
    } catch (error) {
      message.error('执行任务失败');
      console.error('执行任务失败:', error);
    }
  };

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/v1/documents/upload',
    onChange(info) {
      const { status } = info.file;
      if (status === 'done') {
        message.success(`${info.file.name} 文件上传成功`);
        setUploadedFiles(prev => [...prev, info.file]);
      } else if (status === 'error') {
        message.error(`${info.file.name} 文件上传失败`);
      }
    },
    onRemove(file) {
      setUploadedFiles(prev => prev.filter(f => f.uid !== file.uid));
    },
    fileList: uploadedFiles
  };

  // 获取任务状态标签
  const getStatusTag = (status: TaskStatus) => {
    const statusConfig = {
      [TaskStatus.PENDING]: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
      [TaskStatus.PROCESSING]: { color: 'processing', icon: <LoadingOutlined />, text: '执行中' },
      [TaskStatus.COMPLETED]: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      [TaskStatus.FAILED]: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
      [TaskStatus.CANCELLED]: { color: 'default', icon: <CloseCircleOutlined />, text: '已取消' }
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
      render: (text: string, record: Task) => (
        <Space>
          <Text strong>{text}</Text>
          {record.description && (
            <Tooltip title={record.description}>
              <Text type="secondary" ellipsis style={{ maxWidth: 200 }}>
                {record.description}
              </Text>
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: '目标图谱',
      dataIndex: 'target_graph_id',
      key: 'target_graph_id',
      render: (graphId: string) => {
        const graph = availableGraphs.find(g => g.id === graphId);
        return graph ? graph.name : graphId;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: TaskStatus) => getStatusTag(status)
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Task) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewTask(record)}
            />
          </Tooltip>
          {record.status === TaskStatus.PENDING && (
            <Tooltip title="执行任务">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => handleExecuteTask(record.id)}
              />
            </Tooltip>
          )}
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
        </Space>
      )
    }
  ];

  useEffect(() => {
    fetchTasks();
    fetchAvailableGraphs();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={<Title level={3}>📋 任务管理</Title>}
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                创建任务
              </Button>
            }
          >
            <Table
              columns={columns}
              dataSource={tasks}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 创建任务模态框 */}
      <Modal
        title="创建新任务"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
          setUploadedFiles([]);
          setSelectedGraphId(null);
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
            label="目标图谱"
            required
          >
            <Select
              placeholder="请选择目标图谱"
              value={selectedGraphId}
              onChange={setSelectedGraphId}
            >
              {availableGraphs.map(graph => (
                <Option key={graph.id} value={graph.id}>
                  {graph.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入任务描述（可选）"
            />
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
                支持单个或批量上传。支持 PDF、DOC、DOCX、TXT 等格式
              </p>
            </Dragger>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建任务
              </Button>
              <Button onClick={() => {
                setCreateModalVisible(false);
                form.resetFields();
                setUploadedFiles([]);
                setSelectedGraphId(null);
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务详情模态框 */}
      <Modal
        title="任务详情"
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
          <div>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="任务名称">
                {selectedTask.name}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {getStatusTag(selectedTask.status)}
              </Descriptions.Item>
              <Descriptions.Item label="进度">
                <Progress percent={selectedTask.progress} />
              </Descriptions.Item>
              <Descriptions.Item label="目标图谱">
                {availableGraphs.find(g => g.id === selectedTask.target_graph_id)?.name || selectedTask.target_graph_id}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedTask.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {new Date(selectedTask.updated_at).toLocaleString()}
              </Descriptions.Item>
              {selectedTask.description && (
                <Descriptions.Item label="描述">
                  {selectedTask.description}
                </Descriptions.Item>
              )}
              {selectedTask.status === TaskStatus.FAILED && selectedTask.message && (
                <Descriptions.Item label="错误信息">
                  <Alert
                    message={selectedTask.message}
                    type="error"
                    showIcon
                  />
                </Descriptions.Item>
              )}
            </Descriptions>

            {selectedTask.result && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>执行结果</Title>
                <Card size="small">
                  <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                    {JSON.stringify(selectedTask.result, null, 2)}
                  </pre>
                </Card>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TaskManager;