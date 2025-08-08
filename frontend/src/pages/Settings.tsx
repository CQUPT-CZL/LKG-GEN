import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  Select,
  Slider,
  Typography,
  Row,
  Col,
  Divider,
  message,
  Space,
  Upload,
  Modal,
  Table,
  Tag,
  Popconfirm,
  InputNumber,
  Radio,
  Tabs
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PlusOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

interface SystemConfig {
  general: {
    systemName: string;
    language: string;
    theme: string;
    autoSave: boolean;
    autoSaveInterval: number;
  };
  processing: {
    maxFileSize: number;
    batchSize: number;
    enableParallel: boolean;
    maxConcurrency: number;
    timeout: number;
  };
  ai: {
    model: string;
    apiKey: string;
    temperature: number;
    maxTokens: number;
    enableCache: boolean;
  };
  visualization: {
    defaultLayout: string;
    nodeSize: number;
    edgeWidth: number;
    enablePhysics: boolean;
    animationSpeed: number;
  };
}

interface ApiKey {
  id: string;
  name: string;
  key: string;
  provider: string;
  status: 'active' | 'inactive';
  createdAt: string;
  lastUsed?: string;
}

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<SystemConfig>({
    general: {
      systemName: 'LKG-GEN 知识图谱生成系统',
      language: 'zh-CN',
      theme: 'light',
      autoSave: true,
      autoSaveInterval: 5
    },
    processing: {
      maxFileSize: 100,
      batchSize: 50,
      enableParallel: true,
      maxConcurrency: 4,
      timeout: 300
    },
    ai: {
      model: 'gpt-3.5-turbo',
      apiKey: '',
      temperature: 0.7,
      maxTokens: 2048,
      enableCache: true
    },
    visualization: {
      defaultLayout: 'hierarchical',
      nodeSize: 25,
      edgeWidth: 2,
      enablePhysics: true,
      animationSpeed: 1000
    }
  });
  
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: '1',
      name: 'OpenAI GPT',
      key: 'sk-*********************',
      provider: 'OpenAI',
      status: 'active',
      createdAt: '2024-01-15',
      lastUsed: '2024-01-20'
    },
    {
      id: '2',
      name: 'Claude API',
      key: 'sk-ant-*********************',
      provider: 'Anthropic',
      status: 'inactive',
      createdAt: '2024-01-18'
    }
  ]);
  
  const [isApiKeyModalVisible, setIsApiKeyModalVisible] = useState(false);
  const [editingApiKey, setEditingApiKey] = useState<ApiKey | null>(null);
  const [apiKeyForm] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(config);
  }, [config, form]);

  const handleSave = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      setConfig(values);
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      message.success('设置保存成功');
    } catch (error) {
      message.error('设置保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    Modal.confirm({
      title: '确认重置',
      icon: <ExclamationCircleOutlined />,
      content: '确定要重置所有设置到默认值吗？此操作不可撤销。',
      onOk: () => {
        form.resetFields();
        message.success('设置已重置');
      }
    });
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'lkg-gen-settings.json';
    link.click();
    URL.revokeObjectURL(url);
    message.success('设置已导出');
  };

  const uploadProps: UploadProps = {
    name: 'file',
    accept: '.json',
    beforeUpload: (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedConfig = JSON.parse(e.target?.result as string);
          setConfig(importedConfig);
          form.setFieldsValue(importedConfig);
          message.success('设置导入成功');
        } catch (error) {
          message.error('设置文件格式错误');
        }
      };
      reader.readAsText(file);
      return false;
    },
    showUploadList: false
  };

  const handleAddApiKey = () => {
    setEditingApiKey(null);
    apiKeyForm.resetFields();
    setIsApiKeyModalVisible(true);
  };

  const handleEditApiKey = (apiKey: ApiKey) => {
    setEditingApiKey(apiKey);
    apiKeyForm.setFieldsValue(apiKey);
    setIsApiKeyModalVisible(true);
  };

  const handleDeleteApiKey = (id: string) => {
    setApiKeys(apiKeys.filter(key => key.id !== id));
    message.success('API密钥删除成功');
  };

  const handleApiKeyModalOk = async () => {
    try {
      const values = await apiKeyForm.validateFields();
      
      if (editingApiKey) {
        setApiKeys(apiKeys.map(key => 
          key.id === editingApiKey.id 
            ? { ...key, ...values }
            : key
        ));
        message.success('API密钥更新成功');
      } else {
        const newApiKey: ApiKey = {
          id: Date.now().toString(),
          ...values,
          status: 'active',
          createdAt: new Date().toISOString().split('T')[0]
        };
        setApiKeys([...apiKeys, newApiKey]);
        message.success('API密钥添加成功');
      }
      
      setIsApiKeyModalVisible(false);
      setEditingApiKey(null);
      apiKeyForm.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const apiKeyColumns: ColumnsType<ApiKey> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider) => (
        <Tag color={provider === 'OpenAI' ? 'green' : 'blue'}>{provider}</Tag>
      )
    },
    {
      title: 'API密钥',
      dataIndex: 'key',
      key: 'key',
      render: (key) => (
        <Text code style={{ fontSize: '12px' }}>{key}</Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '活跃' : '未激活'}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '最后使用',
      dataIndex: 'lastUsed',
      key: 'lastUsed',
      render: (lastUsed) => lastUsed || '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="text" 
            size="small"
            onClick={() => handleEditApiKey(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个API密钥吗？"
            onConfirm={() => handleDeleteApiKey(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="text" 
              size="small"
              danger
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">⚙️ 系统设置</Title>
        <Paragraph className="page-description">
          配置系统参数、AI模型设置、可视化选项等。
        </Paragraph>
      </div>

      <Form
        form={form}
        layout="vertical"
        initialValues={config}
      >
        <Tabs defaultActiveKey="general">
          {/* 通用设置 */}
          <TabPane tab="通用设置" key="general">
            <Card title="基本配置">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['general', 'systemName']}
                    label="系统名称"
                    rules={[{ required: true, message: '请输入系统名称' }]}
                  >
                    <Input placeholder="请输入系统名称" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['general', 'language']}
                    label="界面语言"
                  >
                    <Select>
                      <Option value="zh-CN">简体中文</Option>
                      <Option value="en-US">English</Option>
                      <Option value="ja-JP">日本語</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['general', 'theme']}
                    label="主题模式"
                  >
                    <Radio.Group>
                      <Radio value="light">浅色</Radio>
                      <Radio value="dark">深色</Radio>
                      <Radio value="auto">跟随系统</Radio>
                    </Radio.Group>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['general', 'autoSave']}
                    label="自动保存"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['general', 'autoSaveInterval']}
                    label="自动保存间隔（分钟）"
                  >
                    <InputNumber min={1} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>

          {/* 处理设置 */}
          <TabPane tab="处理设置" key="processing">
            <Card title="文档处理配置">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['processing', 'maxFileSize']}
                    label="最大文件大小（MB）"
                  >
                    <Slider
                      min={10}
                      max={500}
                      marks={{
                        10: '10MB',
                        100: '100MB',
                        250: '250MB',
                        500: '500MB'
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['processing', 'batchSize']}
                    label="批处理大小"
                  >
                    <InputNumber min={10} max={200} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['processing', 'enableParallel']}
                    label="启用并行处理"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['processing', 'maxConcurrency']}
                    label="最大并发数"
                  >
                    <InputNumber min={1} max={16} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['processing', 'timeout']}
                    label="处理超时（秒）"
                  >
                    <InputNumber min={60} max={3600} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>

          {/* AI设置 */}
          <TabPane tab="AI设置" key="ai">
            <Card title="AI模型配置">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['ai', 'model']}
                    label="AI模型"
                  >
                    <Select>
                      <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
                      <Option value="gpt-4">GPT-4</Option>
                      <Option value="claude-3-sonnet">Claude 3 Sonnet</Option>
                      <Option value="claude-3-opus">Claude 3 Opus</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['ai', 'temperature']}
                    label="创造性（Temperature）"
                  >
                    <Slider
                      min={0}
                      max={2}
                      step={0.1}
                      marks={{
                        0: '保守',
                        1: '平衡',
                        2: '创新'
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['ai', 'maxTokens']}
                    label="最大Token数"
                  >
                    <InputNumber min={512} max={8192} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['ai', 'enableCache']}
                    label="启用缓存"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
            
            <Card title="API密钥管理" style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={handleAddApiKey}
                >
                  添加API密钥
                </Button>
              </div>
              <Table
                columns={apiKeyColumns}
                dataSource={apiKeys}
                rowKey="id"
                size="small"
                pagination={false}
              />
            </Card>
          </TabPane>

          {/* 可视化设置 */}
          <TabPane tab="可视化设置" key="visualization">
            <Card title="图谱可视化配置">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['visualization', 'defaultLayout']}
                    label="默认布局"
                  >
                    <Select>
                      <Option value="hierarchical">层次布局</Option>
                      <Option value="force">力导向布局</Option>
                      <Option value="circular">环形布局</Option>
                      <Option value="grid">网格布局</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['visualization', 'nodeSize']}
                    label="节点大小"
                  >
                    <Slider
                      min={10}
                      max={50}
                      marks={{
                        10: '小',
                        25: '中',
                        50: '大'
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['visualization', 'edgeWidth']}
                    label="边线宽度"
                  >
                    <Slider
                      min={1}
                      max={10}
                      marks={{
                        1: '细',
                        5: '中',
                        10: '粗'
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['visualization', 'enablePhysics']}
                    label="启用物理引擎"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={['visualization', 'animationSpeed']}
                    label="动画速度（毫秒）"
                  >
                    <InputNumber min={100} max={5000} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>
        </Tabs>

        {/* 操作按钮 */}
        <Card style={{ marginTop: 24 }}>
          <Space>
            <Button 
              type="primary" 
              icon={<SaveOutlined />}
              loading={loading}
              onClick={handleSave}
            >
              保存设置
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              重置设置
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={handleExport}
            >
              导出设置
            </Button>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>
                导入设置
              </Button>
            </Upload>
          </Space>
        </Card>
      </Form>

      {/* API密钥编辑模态框 */}
      <Modal
        title={editingApiKey ? '编辑API密钥' : '添加API密钥'}
        open={isApiKeyModalVisible}
        onOk={handleApiKeyModalOk}
        onCancel={() => {
          setIsApiKeyModalVisible(false);
          setEditingApiKey(null);
          apiKeyForm.resetFields();
        }}
        width={500}
      >
        <Form
          form={apiKeyForm}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入API密钥名称" />
          </Form.Item>
          
          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select placeholder="请选择API提供商">
              <Option value="OpenAI">OpenAI</Option>
              <Option value="Anthropic">Anthropic</Option>
              <Option value="Google">Google</Option>
              <Option value="Azure">Azure</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="key"
            label="API密钥"
            rules={[{ required: true, message: '请输入API密钥' }]}
          >
            <Input.Password placeholder="请输入API密钥" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;