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
  FileTextOutlined,
  FileOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { apiService, KnowledgeGraphConfig, Prompt, PromptCreate, PromptUpdate, PromptType, PromptTypesListResponse, AIConfig, AIConfigCreate, AIConfigUpdate, AIProvider, ChunkStrategyConfig, ChunkStrategyOption } from '../services/api';

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

// 移除旧的ApiKey接口，使用新的AIConfig接口

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
  
  const [aiConfigs, setAiConfigs] = useState<AIConfig[]>([]);
  const [aiProviders, setAiProviders] = useState<AIProvider[]>([]);
  
  const [isAiConfigModalVisible, setIsAiConfigModalVisible] = useState(false);
  const [editingAiConfig, setEditingAiConfig] = useState<AIConfig | null>(null);
  const [aiConfigForm] = Form.useForm();
  
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

  // 分块策略配置相关状态
  const [chunkStrategy, setChunkStrategy] = useState<ChunkStrategyConfig>({
    strategy: 'paragraph'
  });
  const [chunkStrategyOptions, setChunkStrategyOptions] = useState<ChunkStrategyOption[]>([]);
  const [chunkStrategyLoading, setChunkStrategyLoading] = useState(false);

  useEffect(() => {
    form.setFieldsValue(config);
    loadKnowledgeGraphConfig();
    loadPrompts();
    loadPromptTypes();
    loadAiConfigs();
    loadAiProviders();
    loadChunkStrategy();
    loadChunkStrategyOptions();
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

  // 加载AI配置列表
  const loadAiConfigs = async () => {
    try {
      const response = await apiService.getAIConfigs();
      setAiConfigs(response.configs || []);
    } catch (error) {
      console.error('加载AI配置失败:', error);
      message.error('加载AI配置失败');
    }
  };

  // 加载AI提供商列表
  const loadAiProviders = async () => {
    try {
      const response = await apiService.getAIProviders();
      setAiProviders(response.providers || []);
    } catch (error) {
      console.error('加载AI提供商失败:', error);
      message.error('加载AI提供商失败');
    }
  };

  // 加载分块策略配置
  const loadChunkStrategy = async () => {
    try {
      setChunkStrategyLoading(true);
      const config = await apiService.getChunkStrategy();
      setChunkStrategy(config);
    } catch (error) {
      console.error('加载分块策略配置失败:', error);
      message.error('加载分块策略配置失败');
    } finally {
      setChunkStrategyLoading(false);
    }
  };

  // 加载分块策略选项
  const loadChunkStrategyOptions = async () => {
    try {
      const response = await apiService.getChunkStrategyOptions();
      // 后端返回的是 {strategies: [...]} 格式
      const options = response.strategies || [];
      setChunkStrategyOptions(options);
    } catch (error) {
      console.error('加载分块策略选项失败:', error);
      // 设置默认选项
      setChunkStrategyOptions([
        { value: 'full_document', label: '全文档', description: '将整个文档作为一个块处理' },
        { value: 'paragraph', label: '段落', description: '按段落分割文档（默认策略）' },
        { value: 'sentence', label: '句子', description: '按句子分割文档' }
      ]);
    }
  };

  // 保存分块策略配置
  const saveChunkStrategy = async () => {
    try {
      setChunkStrategyLoading(true);
      await apiService.updateChunkStrategy(chunkStrategy);
      message.success('分块策略配置保存成功 ✅');
    } catch (error) {
      console.error('保存分块策略配置失败:', error);
      message.error('保存分块策略配置失败');
    } finally {
      setChunkStrategyLoading(false);
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
  const handleSetDefaultPrompt = async (promptId: number, promptType: string) => {
    try {
      await apiService.setDefaultPrompt(promptId, promptType);
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

  const handleAddAiConfig = () => {
    setEditingAiConfig(null);
    aiConfigForm.resetFields();
    setIsAiConfigModalVisible(true);
  };

  const handleEditAiConfig = (aiConfig: AIConfig) => {
    setEditingAiConfig(aiConfig);
    aiConfigForm.setFieldsValue(aiConfig);
    setIsAiConfigModalVisible(true);
  };

  const handleDeleteAiConfig = async (id: number) => {
    try {
      await apiService.deleteAIConfig(id);
      message.success('AI配置删除成功');
      loadAiConfigs();
    } catch (error) {
      console.error('删除AI配置失败:', error);
      message.error('删除AI配置失败');
    }
  };

  const handleAiConfigModalOk = async () => {
    try {
      const values = await aiConfigForm.validateFields();
      
      if (editingAiConfig) {
        await apiService.updateAIConfig(editingAiConfig.id, values);
        message.success('AI配置更新成功');
      } else {
        await apiService.createAIConfig(values);
        message.success('AI配置添加成功');
      }
      
      setIsAiConfigModalVisible(false);
      setEditingAiConfig(null);
      aiConfigForm.resetFields();
      loadAiConfigs();
    } catch (error) {
      console.error('保存AI配置失败:', error);
      message.error('保存AI配置失败');
    }
  };

  // 设置默认AI配置
  const handleSetDefaultAiConfig = async (configId: number) => {
    try {
      await apiService.setDefaultAIConfig(configId);
      message.success('默认AI配置设置成功');
      loadAiConfigs();
    } catch (error) {
      console.error('设置默认AI配置失败:', error);
      message.error('设置默认AI配置失败');
    }
  };

  // 激活/停用AI配置
  const handleToggleAiConfigStatus = async (configId: number, isActive: boolean) => {
    try {
      if (isActive) {
        await apiService.activateAIConfig(configId);
        message.success('AI配置已激活');
      } else {
        await apiService.deactivateAIConfig(configId);
        message.success('AI配置已停用');
      }
      loadAiConfigs();
    } catch (error) {
      console.error('切换AI配置状态失败:', error);
      message.error('切换AI配置状态失败');
    }
  };

  const aiConfigColumns: ColumnsType<AIConfig> = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          {name}
          {record.is_default && <Tag color="gold">默认</Tag>}
        </Space>
      )
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider) => {
        const providerColors: Record<string, string> = {
          openai: 'green',
          anthropic: 'blue',
          azure: 'cyan',
          google: 'orange',
          ollama: 'purple',
          custom: 'default'
        };
        return <Tag color={providerColors[provider] || 'default'}>{provider.toUpperCase()}</Tag>;
      }
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name'
    },
    {
      title: 'API密钥',
      dataIndex: 'api_key',
      key: 'api_key',
      render: (key) => (
        <Text code style={{ fontSize: '12px' }}>
          {key ? `${key.substring(0, 8)}...${key.substring(key.length - 4)}` : '-'}
        </Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive, record) => (
        <Switch
          checked={isActive}
          onChange={(checked) => handleToggleAiConfigStatus(record.id, checked)}
          checkedChildren="启用"
          unCheckedChildren="停用"
        />
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          {!record.is_default && (
            <Button 
              type="text" 
              size="small"
              onClick={() => handleSetDefaultAiConfig(record.id)}
            >
              设为默认
            </Button>
          )}
          <Button 
            type="text" 
            size="small"
            onClick={() => handleEditAiConfig(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个AI配置吗？"
            onConfirm={() => handleDeleteAiConfig(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="text" 
              size="small"
              danger
              disabled={record.is_default}
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
        <Tabs defaultActiveKey="ai">

          {/* AI设置 */}
          <TabPane tab="AI设置" key="ai">

            <Card title="AI配置管理" style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={handleAddAiConfig}
                >
                  添加AI配置
                </Button>
              </div>
              <Table
                columns={aiConfigColumns}
                dataSource={aiConfigs}
                rowKey="id"
                size="small"
                pagination={false}
              />
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

            <Paragraph style={{ marginTop: 16, color: '#666' }}>
              <Text type="secondary">
                💡 提示：实体类型用于标识知识图谱中的节点类型（如人物、地点、组织等），
                关系类型用于标识节点之间的连接关系（如属于、位于、合作等）。
              </Text>
            </Paragraph>
            
            {/* 保存和重置按钮 */}
            <div style={{ marginTop: 24, textAlign: 'center' }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<SaveOutlined />}
                  onClick={saveKnowledgeGraphConfig}
                  size="large"
                >
                  保存配置
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={resetKnowledgeGraphConfig}
                  size="large"
                >
                  重置为默认
                </Button>
              </Space>
            </div>
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
                            onClick={() => handleSetDefaultPrompt(record.id, record.prompt_type)}
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

          {/* 文档处理配置 */}
          <TabPane tab={<span><FileOutlined /> 文档处理</span>} key="document-processing">
            <Card title="分块策略配置" loading={chunkStrategyLoading}>
              <Row gutter={24}>
                <Col span={24}>
                  <Form.Item label="分块策略">
                    <Select
                      value={chunkStrategy.strategy}
                      onChange={(value) => setChunkStrategy({...chunkStrategy, strategy: value})}
                      placeholder="选择分块策略"
                    >
                      {chunkStrategyOptions && chunkStrategyOptions.length > 0 ? 
                        chunkStrategyOptions.map(option => (
                          <Option key={option.value} value={option.value}>
                            {option.label}
                          </Option>
                        )) : (
                          <Option value="paragraph">按段落分块</Option>
                        )
                      }
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Paragraph style={{ marginTop: 16, color: '#666' }}>
                <Text type="secondary">
                  💡 提示：
                  <br />
                  • <strong>全文档</strong>：将整个文档作为一个块处理，适合短文档
                  <br />
                  • <strong>段落</strong>：按段落分割文档，平衡处理效率和语义完整性（推荐）
                  <br />
                  • <strong>句子</strong>：按句子分割文档，提供最细粒度的分块
                </Text>
              </Paragraph>

              <div style={{ marginTop: 24, textAlign: 'center' }}>
                <Button 
                  type="primary" 
                  icon={<SaveOutlined />}
                  onClick={saveChunkStrategy}
                  loading={chunkStrategyLoading}
                  size="large"
                >
                  保存配置
                </Button>
              </div>
            </Card>
          </TabPane>
        </Tabs>


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

      {/* AI配置编辑模态框 */}
      <Modal
        title={editingAiConfig ? '编辑AI配置' : '添加AI配置'}
        open={isAiConfigModalVisible}
        onOk={handleAiConfigModalOk}
        onCancel={() => {
          setIsAiConfigModalVisible(false);
          setEditingAiConfig(null);
          aiConfigForm.resetFields();
        }}
        width={600}
      >
        <Form
          form={aiConfigForm}
          layout="vertical"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="配置名称"
                rules={[{ required: true, message: '请输入配置名称' }]}
              >
                <Input placeholder="请输入AI配置名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="provider"
                label="AI提供商"
                rules={[{ required: true, message: '请选择AI提供商' }]}
              >
                <Select placeholder="请选择AI提供商">
                  {aiProviders.map(provider => (
                    <Option key={provider.provider} value={provider.provider}>
                      {provider.display_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="model_name"
                label="模型名称"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input placeholder="如: gpt-3.5-turbo" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="api_key"
                label="API密钥"
                rules={[{ required: true, message: '请输入API密钥' }]}
              >
                <Input.Password placeholder="请输入API密钥" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="base_url"
            label="Base URL（可选）"
          >
            <Input placeholder="如: https://api.openai.com/v1" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="temperature"
                label="Temperature"
              >
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  placeholder="0.7"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_tokens"
                label="最大Token数"
              >
                <InputNumber
                  min={1}
                  max={32000}
                  placeholder="4000"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="is_default"
                label="设为默认配置"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="启用配置"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;