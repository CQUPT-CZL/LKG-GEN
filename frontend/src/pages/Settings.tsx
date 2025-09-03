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
  Tabs,
  List,
  Tooltip
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  EditOutlined,
  NodeIndexOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { apiService, KnowledgeGraphConfig, Prompt, PromptCreate, PromptUpdate, PromptType, PromptTypesListResponse } from '../services/api';

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
  const [kgConfigs, setKgConfigs] = useState<KnowledgeGraphConfig[]>([]);
  const [selectedKgConfig, setSelectedKgConfig] = useState<string | null>(null);
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
  
  // 知识图谱配置相关状态
  const [kgConfig, setKgConfig] = useState<KnowledgeGraphConfig>({
    entity_types: [],
    relation_types: []
  });
  const [isKgConfigModalVisible, setIsKgConfigModalVisible] = useState(false);
  const [editingEntityType, setEditingEntityType] = useState<string | null>(null);
  const [editingRelationType, setEditingRelationType] = useState<string | null>(null);
  const [newEntityType, setNewEntityType] = useState('');
  const [newRelationType, setNewRelationType] = useState('');
  const [kgConfigForm] = Form.useForm();
  
  // Prompt管理相关状态
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [promptTypes, setPromptTypes] = useState<PromptType[]>([]);
  const [isPromptModalVisible, setIsPromptModalVisible] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [promptForm] = Form.useForm();
  const [selectedPromptType, setSelectedPromptType] = useState<string>('all');
  const [promptLoading, setPromptLoading] = useState(false);

  useEffect(() => {
    form.setFieldsValue(config);
    loadKnowledgeGraphConfig();
    loadPrompts();
    loadPromptTypes();
  }, []);
  
  // 加载知识图谱配置
  const loadKnowledgeGraphConfig = async () => {
    try {
      const config = await apiService.getKnowledgeGraphConfig();
      setKgConfig(config);
    } catch (error) {
      console.error('加载知识图谱配置失败:', error);
      message.error('加载知识图谱配置失败');
    }
  };
  
  // 保存知识图谱配置
  const saveKnowledgeGraphConfig = async () => {
    try {
      await apiService.updateKnowledgeGraphConfig(kgConfig);
      message.success('知识图谱配置保存成功');
    } catch (error) {
      console.error('保存知识图谱配置失败:', error);
      message.error('保存知识图谱配置失败');
    }
  };
  
  // 重置知识图谱配置为默认值
  const resetKnowledgeGraphConfig = async () => {
    try {
      await apiService.resetConfigToDefaults();
      await loadKnowledgeGraphConfig();
      message.success('知识图谱配置已重置为默认值');
    } catch (error) {
      console.error('重置知识图谱配置失败:', error);
      message.error('重置知识图谱配置失败');
    }
  };
  
  // 加载Prompt列表
  const loadPrompts = async () => {
    try {
      setPromptLoading(true);
      const params = selectedPromptType !== 'all' ? { prompt_type: selectedPromptType } : {};
      const response = await apiService.getPrompts(params);
      setPrompts(response.prompts);
    } catch (error) {
      console.error('加载Prompt列表失败:', error);
      message.error('加载Prompt列表失败');
    } finally {
      setPromptLoading(false);
    }
  };
  
  // 加载Prompt类型列表
  const loadPromptTypes = async () => {
    try {
      const response: PromptTypesListResponse = await apiService.getPromptTypes();
      // 后端返回的是 {types: [...]} 格式，需要提取 types 字段
      setPromptTypes(response.types || []);
    } catch (error) {
      console.error('加载Prompt类型失败:', error);
      message.error('加载Prompt类型失败');
      setPromptTypes([]); // 确保在错误情况下设置为空数组
    }
  };
  
  // 创建或更新Prompt
  const handlePromptSubmit = async () => {
    try {
      const values = await promptForm.validateFields();
      if (editingPrompt) {
        await apiService.updatePrompt(editingPrompt.id, values);
        message.success('Prompt更新成功');
      } else {
        await apiService.createPrompt(values);
        message.success('Prompt创建成功');
      }
      setIsPromptModalVisible(false);
      setEditingPrompt(null);
      promptForm.resetFields();
      loadPrompts();
    } catch (error) {
      console.error('保存Prompt失败:', error);
      message.error('保存Prompt失败');
    }
  };
  
  // 删除Prompt
  const handleDeletePrompt = async (promptId: number) => {
    try {
      await apiService.deletePrompt(promptId);
      message.success('Prompt删除成功');
      loadPrompts();
    } catch (error) {
      console.error('删除Prompt失败:', error);
      message.error('删除Prompt失败');
    }
  };
  
  // 设置默认Prompt
  const handleSetDefaultPrompt = async (promptId: number) => {
    try {
      await apiService.setDefaultPrompt(promptId);
      message.success('默认Prompt设置成功');
      loadPrompts();
    } catch (error) {
      console.error('设置默认Prompt失败:', error);
      message.error('设置默认Prompt失败');
    }
  };
  
  // 编辑Prompt
  const handleEditPrompt = (prompt: Prompt) => {
    setEditingPrompt(prompt);
    promptForm.setFieldsValue({
      name: prompt.name,
      prompt_type: prompt.prompt_type,
      content: prompt.content,
      description: prompt.description,
      version: prompt.version,
      is_active: prompt.is_active
    });
    setIsPromptModalVisible(true);
  };
  
  // 新建Prompt
  const handleCreatePrompt = () => {
    setEditingPrompt(null);
    promptForm.resetFields();
    promptForm.setFieldsValue({
      is_active: true,
      version: '1.0.0'
    });
    setIsPromptModalVisible(true);
  };
  
  // Prompt类型筛选变化
  const handlePromptTypeChange = (type: string) => {
    setSelectedPromptType(type);
    // 重新加载数据会在useEffect中处理
  };
  
  // 监听Prompt类型筛选变化
  useEffect(() => {
    if (promptTypes.length > 0) {
      loadPrompts();
    }
  }, [selectedPromptType]);
  
  // 添加实体类型
  const handleAddEntityType = () => {
    if (newEntityType.trim() && !kgConfig.entity_types.includes(newEntityType.trim())) {
      setKgConfig({
        ...kgConfig,
        entity_types: [...kgConfig.entity_types, newEntityType.trim()]
      });
      setNewEntityType('');
    }
  };
  
  // 删除实体类型
  const handleDeleteEntityType = (type: string) => {
    setKgConfig({
      ...kgConfig,
      entity_types: kgConfig.entity_types.filter(t => t !== type)
    });
  };
  
  // 添加关系类型
  const handleAddRelationType = () => {
    if (newRelationType.trim() && !kgConfig.relation_types.includes(newRelationType.trim())) {
      setKgConfig({
        ...kgConfig,
        relation_types: [...kgConfig.relation_types, newRelationType.trim()]
      });
      setNewRelationType('');
    }
  };
  
  // 删除关系类型
  const handleDeleteRelationType = (type: string) => {
    setKgConfig({
      ...kgConfig,
      relation_types: kgConfig.relation_types.filter(t => t !== type)
    });
  };
  
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

          {/* 知识图谱配置 */}
          <TabPane tab={<span><NodeIndexOutlined /> 知识图谱配置</span>} key="knowledge-graph">
            <Card title="实体类型配置">
              <div style={{ marginBottom: 16 }}>
                <Space.Compact style={{ width: '100%' }}>
                  <Input
                    placeholder="输入新的实体类型"
                    value={newEntityType}
                    onChange={(e) => setNewEntityType(e.target.value)}
                    onPressEnter={handleAddEntityType}
                  />
                  <Button type="primary" onClick={handleAddEntityType}>
                    添加
                  </Button>
                </Space.Compact>
              </div>
              <List
                size="small"
                bordered
                dataSource={kgConfig.entity_types}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Popconfirm
                        title="确定要删除这个实体类型吗？"
                        onConfirm={() => handleDeleteEntityType(item)}
                        okText="确定"
                        cancelText="取消"
                      >
                        <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                      </Popconfirm>
                    ]}
                  >
                    <Tag color="blue">{item}</Tag>
                  </List.Item>
                )}
                locale={{ emptyText: '暂无实体类型' }}
              />
            </Card>

            <Card title="关系类型配置" style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <Space.Compact style={{ width: '100%' }}>
                  <Input
                    placeholder="输入新的关系类型"
                    value={newRelationType}
                    onChange={(e) => setNewRelationType(e.target.value)}
                    onPressEnter={handleAddRelationType}
                  />
                  <Button type="primary" onClick={handleAddRelationType}>
                    添加
                  </Button>
                </Space.Compact>
              </div>
              <List
                size="small"
                bordered
                dataSource={kgConfig.relation_types}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Popconfirm
                        title="确定要删除这个关系类型吗？"
                        onConfirm={() => handleDeleteRelationType(item)}
                        okText="确定"
                        cancelText="取消"
                      >
                        <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                      </Popconfirm>
                    ]}
                  >
                    <Tag color="green">{item}</Tag>
                  </List.Item>
                )}
                locale={{ emptyText: '暂无关系类型' }}
              />
            </Card>

            <Card title="配置操作" style={{ marginTop: 16 }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<SaveOutlined />}
                  onClick={saveKnowledgeGraphConfig}
                >
                  保存配置
                </Button>
                <Popconfirm
                  title="确定要重置为默认配置吗？这将清除所有自定义配置。"
                  onConfirm={resetKnowledgeGraphConfig}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button icon={<ReloadOutlined />}>
                    重置为默认
                  </Button>
                </Popconfirm>
              </Space>
              <Paragraph style={{ marginTop: 16, color: '#666' }}>
                <Text type="secondary">
                  💡 提示：实体类型用于标识知识图谱中的节点类型（如人物、地点、组织等），
                  关系类型用于标识节点之间的连接关系（如属于、位于、合作等）。
                  修改配置后请点击"保存配置"按钮使更改生效。
                </Text>
              </Paragraph>
            </Card>
          </TabPane>

          {/* Prompt管理 */}
          <TabPane tab={<span><FileTextOutlined /> Prompt管理</span>} key="prompt-management">
            <Card 
              title="Prompt模板管理" 
              extra={
                <Space>
                  <Select
                    value={selectedPromptType}
                    onChange={handlePromptTypeChange}
                    style={{ width: 150 }}
                    placeholder="选择类型"
                  >
                    <Option value="all">全部类型</Option>
                     {promptTypes.map(type => (
                       <Option key={type.type} value={type.type}>
                         {type.display_name}
                       </Option>
                     ))}
                  </Select>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={handleCreatePrompt}
                  >
                    新建Prompt
                  </Button>
                </Space>
              }
            >
              <Table
                dataSource={prompts}
                loading={promptLoading}
                rowKey="id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条记录`
                }}
                columns={[
                  {
                    title: '名称',
                    dataIndex: 'name',
                    key: 'name',
                    width: 200,
                    render: (text, record) => (
                      <Space>
                        <Text strong={record.is_default}>{text}</Text>
                        {record.is_default && <Tag color="gold">默认</Tag>}
                      </Space>
                    )
                  },
                  {
                    title: '类型',
                    dataIndex: 'prompt_type',
                    key: 'prompt_type',
                    width: 120,
                    render: (type) => {
                       const typeInfo = promptTypes.find(t => t.type === type);
                       return <Tag color="blue">{typeInfo?.display_name || type}</Tag>;
                     }
                  },
                  {
                    title: '描述',
                    dataIndex: 'description',
                    key: 'description',
                    ellipsis: true,
                    render: (text) => text || '-'
                  },
                  {
                    title: '版本',
                    dataIndex: 'version',
                    key: 'version',
                    width: 100
                  },
                  {
                    title: '状态',
                    dataIndex: 'is_active',
                    key: 'is_active',
                    width: 80,
                    render: (isActive) => (
                      <Tag color={isActive ? 'success' : 'default'}>
                        {isActive ? '启用' : '禁用'}
                      </Tag>
                    )
                  },
                  {
                    title: '更新时间',
                    dataIndex: 'updated_at',
                    key: 'updated_at',
                    width: 150,
                    render: (date) => date ? new Date(date).toLocaleString() : '-'
                  },
                  {
                    title: '操作',
                    key: 'action',
                    width: 200,
                    render: (_, record) => (
                      <Space size="small">
                        <Button 
                          type="text" 
                          size="small"
                          onClick={() => handleEditPrompt(record)}
                        >
                          编辑
                        </Button>
                        {!record.is_default && (
                          <Button 
                            type="text" 
                            size="small"
                            onClick={() => handleSetDefaultPrompt(record.id)}
                          >
                            设为默认
                          </Button>
                        )}
                        <Popconfirm
                          title="确定要删除这个Prompt吗？"
                          onConfirm={() => handleDeletePrompt(record.id)}
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
                ]}
              />
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

      {/* Prompt编辑/创建模态框 */}
      <Modal
        title={editingPrompt ? '编辑Prompt' : '新建Prompt'}
        open={isPromptModalVisible}
        onOk={handlePromptSubmit}
        onCancel={() => {
          setIsPromptModalVisible(false);
          setEditingPrompt(null);
          promptForm.resetFields();
        }}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={promptForm}
          layout="vertical"
          initialValues={{
            is_active: true,
            version: '1.0.0'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Prompt名称"
                rules={[{ required: true, message: '请输入Prompt名称' }]}
              >
                <Input placeholder="请输入Prompt名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="prompt_type"
                label="Prompt类型"
                rules={[{ required: true, message: '请选择Prompt类型' }]}
              >
                <Select placeholder="请选择Prompt类型">
                  {promptTypes.map(type => (
                    <Option key={type.type} value={type.type}>
                      {type.display_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="version"
                label="版本号"
                rules={[{ required: true, message: '请输入版本号' }]}
              >
                <Input placeholder="如: 1.0.0" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="启用状态"
                valuePropName="checked"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea 
              placeholder="请输入Prompt描述" 
              rows={2}
            />
          </Form.Item>
          <Form.Item
            name="content"
            label="Prompt内容"
            rules={[{ required: true, message: '请输入Prompt内容' }]}
          >
            <TextArea 
              placeholder="请输入Prompt模板内容" 
              rows={8}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>

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