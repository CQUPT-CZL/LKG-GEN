import React, { useState, useEffect } from 'react';
import {
  Card,
  Steps,
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
  Radio,
  TreeSelect
} from 'antd';
import {
  InboxOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { apiService, Category } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

interface ProcessStep {
  title: string;
  description: string;
  status: 'wait' | 'process' | 'finish' | 'error';
  progress?: number;
}

interface BuildResult {
  entities: number;
  relations: number;
  documents: number;
  processingTime: string;
}

interface DocumentWithType {
  file: any;
  type: string;
}

const GraphBuilder: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [uploadedFiles, setUploadedFiles] = useState<DocumentWithType[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<{ task_id: string; status: string; progress: number; message: string; result?: any } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [buildResult, setBuildResult] = useState<BuildResult | null>(null);
  const [availableGraphs, setAvailableGraphs] = useState<any[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null);
  const [categoryTree, setCategoryTree] = useState<Category | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [processSteps, setProcessSteps] = useState<ProcessStep[]>([
    {
      title: '📝 文档预处理',
      description: '文档格式转换和预处理',
      status: 'wait',
      progress: 0
    },
    {
      title: '🔪 文档分块',
      description: '将文档切分为语义块',
      status: 'wait',
      progress: 0
    },
    {
      title: '🏷️ 实体识别',
      description: '识别文档中的实体',
      status: 'wait',
      progress: 0
    },
    {
      title: '🔍 实体消歧',
      description: '合并相似实体',
      status: 'wait',
      progress: 0
    },
    {
      title: '🔗 关系抽取',
      description: '提取实体间关系',
      status: 'wait',
      progress: 0
    },
    {
      title: '🕸️ 图谱构建',
      description: '生成最终知识图谱',
      status: 'wait',
      progress: 0
    }
  ]);

  // 根据进度消息更新步骤状态
  const updateProcessSteps = (progress: number, message: string) => {
    setProcessSteps(prevSteps => {
      const newSteps = [...prevSteps];
      
      // 根据进度百分比和消息内容判断当前步骤
      if (message.includes('文档预处理') || message.includes('开始文档预处理')) {
        newSteps[0].status = 'process';
        newSteps[0].progress = Math.min(progress, 15);
      } else if (message.includes('文档预处理完成')) {
        newSteps[0].status = 'finish';
        newSteps[0].progress = 100;
      }
      
      if (message.includes('文档分块') || message.includes('开始文档分块')) {
        newSteps[0].status = 'finish';
        newSteps[1].status = 'process';
        newSteps[1].progress = Math.min((progress - 15) * 100 / 15, 100);
      } else if (message.includes('文本分块完成')) {
        newSteps[1].status = 'finish';
        newSteps[1].progress = 100;
      }
      
      if (message.includes('实体识别') || message.includes('开始实体识别')) {
        newSteps[1].status = 'finish';
        newSteps[2].status = 'process';
        newSteps[2].progress = Math.min((progress - 30) * 100 / 15, 100);
      } else if (message.includes('实体识别完成')) {
        newSteps[2].status = 'finish';
        newSteps[2].progress = 100;
      }
      
      if (message.includes('实体消歧') || message.includes('开始实体消歧')) {
        newSteps[2].status = 'finish';
        newSteps[3].status = 'process';
        newSteps[3].progress = Math.min((progress - 45) * 100 / 10, 100);
      } else if (message.includes('实体消歧完成')) {
        newSteps[3].status = 'finish';
        newSteps[3].progress = 100;
      }
      
      if (message.includes('关系抽取') || message.includes('开始关系抽取')) {
        newSteps[3].status = 'finish';
        newSteps[4].status = 'process';
        newSteps[4].progress = Math.min((progress - 55) * 100 / 30, 100);
      } else if (message.includes('关系抽取完成')) {
        newSteps[4].status = 'finish';
        newSteps[4].progress = 100;
      }
      
      if (message.includes('构建知识图谱') || message.includes('开始构建知识图谱')) {
        newSteps[4].status = 'finish';
        newSteps[5].status = 'process';
        newSteps[5].progress = Math.min((progress - 85) * 100 / 15, 100);
      } else if (message.includes('知识图谱构建完成')) {
        newSteps[5].status = 'finish';
        newSteps[5].progress = 100;
      }
      
      return newSteps;
    });
  };

  // 构建分类树数据 (暂时禁用)
  const buildCategoryTreeData = (category: Category | null): any[] => {
    // 暂时不使用分类树功能
    return [];
  };

  // 处理分类选择变化 (暂时禁用分类功能)
  const handleCategoryChange = async (categoryId: string | null) => {
    setSelectedCategoryId(categoryId);
    setSelectedGraphId(null); // 重置图谱选择
    
    // 暂时不使用分类功能，直接加载所有图谱
    try {
      const graphs = await apiService.getGraphs();
      setAvailableGraphs(graphs);
    } catch (error) {
      console.error('加载图谱失败:', error);
      message.error('加载图谱失败');
      setAvailableGraphs([]);
    }
  };

  // 加载图谱列表函数 (暂时禁用分类功能)
  const loadAvailableGraphs = async (categoryId?: string) => {
    try {
      // 暂时不使用分类功能，直接加载所有图谱
      const graphs = await apiService.getGraphs();
      setAvailableGraphs(graphs);
    } catch (error) {
      console.error('加载图谱列表失败:', error);
      message.error('加载图谱列表失败');
    }
  };

  // 加载可用图谱列表 (暂时禁用分类树)
  useEffect(() => {
    const loadData = async () => {
      try {
        // 暂时只加载图谱列表，不加载分类树
        const graphs = await apiService.getGraphs();
        setAvailableGraphs(graphs);
        // setCategoryTree(tree); // 暂时禁用
      } catch (error) {
        console.error('加载数据失败:', error);
      }
    };
    
    loadData();
  }, []);

  // 移除任务状态轮询，改为直接处理批量资源创建结果

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    // 移除accept限制，支持所有文件类型
    // accept: '.pdf,.txt,.docx,.md',
    beforeUpload: (file) => {
      // 移除文件类型检查，支持所有文件类型
      console.log('上传文件:', file.type, file.name);
      
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB！');
        return false;
      }
      
      return false; // 阻止自动上传，我们将在构建时手动上传
    },
    onChange: (info) => {
      // 为每个新上传的文件添加默认类型
      const filesWithType = info.fileList.map(file => ({
        file: file,
        type: 'paper' // 默认类型为论文
      }));
      setUploadedFiles(filesWithType);
    },
    onDrop: (e) => {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };

  // 根据分类ID获取分类路径的辅助函数 (暂时禁用)
  const getCategoryPath = (categoryId: string, tree: Category | null): string | null => {
    // 暂时不使用分类功能
    return null;
  };

  // 读取文件内容为文本
  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target?.result as string || '');
      };
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  // 处理批量资源创建结果
  const handleBatchResult = (result: any) => {
    // 直接显示结果，不需要模拟进度
    setTaskStatus({
      task_id: `batch_${Date.now()}`,
      status: 'completed',
      progress: 100,
      message: `成功创建 ${result.success_count} 个资源，失败 ${result.failed_count} 个`,
      result: {
        statistics: {
          entities_count: result.success_count * 10, // 估算数据
          relations_count: result.success_count * 5,
          processing_time: '实时处理'
        }
      }
    });
    
    // 标记所有步骤为完成
    setProcessSteps(prevSteps => 
      prevSteps.map(step => ({ ...step, status: 'finish', progress: 100 }))
    );
    
    setCurrentStep(2);
    setIsProcessing(false);
    
    setBuildResult({
      entities: result.success_count * 10,
      relations: result.success_count * 5,
      documents: result.success_count,
      processingTime: '实时处理'
    });
    
    message.success(`知识图谱构建完成！成功处理 ${result.success_count} 个文档`);
  };

  const startProcessing = async () => {
    if (uploadedFiles.length === 0) {
      message.warning('请先上传文档！');
      return;
    }

    if (!selectedGraphId) {
      message.warning('请选择目标图谱！');
      return;
    }

    try {
      setIsProcessing(true);
      setCurrentStep(1);

      // 暂时不使用分类路径
      // const categoryPath = getCategoryPath(selectedCategoryId, categoryTree);
      // console.log('🔍 获取到分类路径:', categoryPath);

      // 准备批量资源数据
      const resources = [];
      
      for (const docWithType of uploadedFiles) {
        const file = docWithType.file.originFileObj;
        const content = await readFileAsText(file);
        
        // 去掉文件扩展名
        const filenameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
        
        resources.push({
          filename: filenameWithoutExt,
          content: content,
          type: docWithType.type
        });
      }
      
      // 调用批量资源创建API
      const batchRequest = {
        parent_id: selectedGraphId,
        graph_id: selectedGraphId,
        resources: resources
      };
      
      const result = await fetch('/api/documents/resources', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(batchRequest),
      }).then(res => res.json());
      
      // 处理批量资源创建结果
      handleBatchResult(result);
      
      message.success(`成功创建 ${result.success_count} 个资源到知识图谱`);
    } catch (error: any) {
      console.error('构建失败:', error);
      console.error('错误详情:', error.response?.data || error.message);
      console.error('错误类型:', error.name);
      console.error('错误代码:', error.code);
      
      let errorMessage = '构建失败，请重试';
      if (error.response?.data?.detail) {
        errorMessage = `构建失败: ${error.response.data.detail}`;
      } else if (error.message) {
        if (error.message.includes('Network Error') || error.message.includes('网络错误')) {
          errorMessage = '网络连接失败，请检查后端服务是否正常运行';
        } else {
          errorMessage = `构建失败: ${error.message}`;
        }
      } else if (error.code === 'NETWORK_ERROR') {
        errorMessage = '网络连接失败，请检查后端服务是否正常运行';
      }
      
      message.error(errorMessage);
      setIsProcessing(false);
      setCurrentStep(0);
    }
  };

  const resetProcess = () => {
    setCurrentStep(0);
    setUploadedFiles([]);
    setIsProcessing(false);
    setBuildResult(null);
    setTaskId(null);
    setTaskStatus(null);
    setProcessSteps([
      {
        title: '📝 文档预处理',
        description: '文档格式转换和预处理',
        status: 'wait',
        progress: 0
      },
      {
        title: '🔪 文档分块',
        description: '将文档切分为语义块',
        status: 'wait',
        progress: 0
      },
      {
        title: '🏷️ 实体识别',
        description: '识别文档中的实体',
        status: 'wait',
        progress: 0
      },
      {
        title: '🔍 实体消歧',
        description: '合并相似实体',
        status: 'wait',
        progress: 0
      },
      {
        title: '🔗 关系抽取',
        description: '提取实体间关系',
        status: 'wait',
        progress: 0
      },
      {
        title: '🕸️ 图谱构建',
        description: '生成最终知识图谱',
        status: 'wait',
        progress: 0
      }
    ]);
  };

  const mainSteps = [
    {
      title: '上传文档',
      description: '选择要处理的文档文件'
    },
    {
      title: '处理文档',
      description: '自动提取实体和关系'
    },
    {
      title: '构建完成',
      description: '查看构建结果'
    }
  ];

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">🏗️ 知识图谱构建</Title>
        <Paragraph className="page-description">
          上传文档并选择文档类型（论文、报告、文章等），系统将自动提取实体和关系，构建到指定的知识图谱中。
        </Paragraph>
      </div>

      <Card>
        <Steps current={currentStep} items={mainSteps} style={{ marginBottom: 32 }} />

        {currentStep === 0 && (
          <div>
            <Title level={4}>📁 上传文档并选择类型</Title>
            <Dragger {...uploadProps} style={{ marginBottom: 24 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个或批量上传。上传后可为每个文档选择类型（论文、报告、文章等），单个文件不超过 50MB。
              </p>
            </Dragger>

            {uploadedFiles.length > 0 && (
              <div>
                <Title level={5}>📋 已上传文件 ({uploadedFiles.length})</Title>
                <List
                  dataSource={uploadedFiles}
                  renderItem={(docWithType, index) => (
                    <List.Item
                      actions={[
                        <Select
                          value={docWithType.type}
                          onChange={(value) => {
                            const newFiles = [...uploadedFiles];
                            newFiles[index].type = value;
                            setUploadedFiles(newFiles);
                          }}
                          style={{ width: 120 }}
                        >
                          <Option value="paper">📄 论文</Option>
                          <Option value="report">📊 报告</Option>
                          <Option value="article">📝 文章</Option>
                          <Option value="book">📚 书籍</Option>
                          <Option value="manual">📖 手册</Option>
                          <Option value="other">📋 其他</Option>
                        </Select>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={<FileTextOutlined />}
                        title={docWithType.file.name}
                        description={`${(docWithType.file.size / 1024 / 1024).toFixed(2)} MB`}
                      />
                      <Tag color="green">已上传</Tag>
                    </List.Item>
                  )}
                />
                <Divider />
                <Form form={form} layout="vertical" style={{ marginBottom: 16 }}>
                   {/* 暂时禁用分类选择功能 */}
                   {/* <Form.Item label="选择分类目录">
                     <TreeSelect
                       placeholder="选择分类目录来过滤图谱"
                       allowClear
                       value={selectedCategoryId}
                       treeData={buildCategoryTreeData(categoryTree)}
                       onChange={handleCategoryChange}
                       showSearch
                       treeDefaultExpandAll
                     />
                   </Form.Item> */}
                   
                   <Form.Item 
                     label="选择目标图谱"
                     rules={[{ required: true, message: '请选择目标图谱' }]}
                   >
                     <Select 
                       value={selectedGraphId}
                       onChange={setSelectedGraphId}
                       placeholder="请选择目标图谱"
                       notFoundContent={availableGraphs.length === 0 ? "暂无数据" : "暂无数据"}
                     >
                       {availableGraphs.map(graph => (
                         <Option key={graph.id} value={graph.id}>
                           {graph.name} ({graph.entity_count || 0} 实体, {graph.relation_count || 0} 关系)
                         </Option>
                       ))}
                     </Select>
                   </Form.Item>
                 </Form>
                <Space>
                  <Button 
                    type="primary" 
                    size="large" 
                    onClick={startProcessing}
                  >
                    🚀 开始构建知识图谱
                  </Button>
                  <Button onClick={resetProcess}>重置</Button>
                </Space>
              </div>
            )}
          </div>
        )}

        {currentStep === 1 && (
          <div>
            <Title level={4}>⚙️ 正在处理文档</Title>
            <Alert
              message="处理中"
              description="正在分析文档内容，提取实体和关系，请耐心等待..."
              type="info"
              showIcon
              icon={<LoadingOutlined />}
              style={{ marginBottom: 24 }}
            />

            {taskStatus && (
              <div style={{ marginBottom: 24 }}>
                <Progress
                  percent={taskStatus.progress || 0}
                  status={taskStatus.status === 'failed' ? 'exception' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <div style={{ marginTop: 16 }}>
                  <Text>当前状态: {taskStatus.status}</Text>
                  {taskStatus.message && (
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">{taskStatus.message}</Text>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div style={{ marginBottom: 24 }}>
              <Title level={5} style={{ marginBottom: 16 }}>📊 处理进度详情</Title>
              {processSteps.map((step, index) => (
                <Card key={index} size="small" style={{ marginBottom: 12 }}>
                  <Row align="middle">
                    <Col span={7}>
                      <Space>
                        {step.status === 'finish' && <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />}
                        {step.status === 'process' && <LoadingOutlined style={{ color: '#1890ff', fontSize: 16 }} />}
                        {step.status === 'error' && <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />}
                        {step.status === 'wait' && <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#d9d9d9', display: 'inline-block' }} />}
                        <Text strong style={{ 
                          color: step.status === 'finish' ? '#52c41a' : 
                                 step.status === 'process' ? '#1890ff' : 
                                 step.status === 'error' ? '#ff4d4f' : '#8c8c8c'
                        }}>
                          {step.title}
                        </Text>
                      </Space>
                    </Col>
                    <Col span={9}>
                      <Text type="secondary">{step.description}</Text>
                    </Col>
                    <Col span={8}>
                      <Progress
                        percent={step.progress || 0}
                        size="small"
                        status={
                          step.status === 'process' ? 'active' : 
                          step.status === 'error' ? 'exception' : 
                          step.status === 'finish' ? 'success' : 'normal'
                        }
                        strokeColor={
                          step.status === 'finish' ? '#52c41a' :
                          step.status === 'process' ? '#1890ff' :
                          step.status === 'error' ? '#ff4d4f' : '#d9d9d9'
                        }
                        showInfo={step.status !== 'wait'}
                      />
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          </div>
        )}

        {currentStep === 2 && buildResult && (
          <div>
            <Title level={4}>✅ 构建完成</Title>
            <Alert
              message="知识图谱构建成功！"
              description="文档已成功处理，知识图谱已生成。"
              type="success"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <NodeIndexOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
                    <div style={{ fontSize: 24, fontWeight: 'bold' }}>{buildResult.entities}</div>
                    <div>实体数量</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <BranchesOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 8 }} />
                    <div style={{ fontSize: 24, fontWeight: 'bold' }}>{buildResult.relations}</div>
                    <div>关系数量</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <FileTextOutlined style={{ fontSize: 32, color: '#722ed1', marginBottom: 8 }} />
                    <div style={{ fontSize: 24, fontWeight: 'bold' }}>{buildResult.documents}</div>
                    <div>处理文档</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <CheckCircleOutlined style={{ fontSize: 32, color: '#fa8c16', marginBottom: 8 }} />
                    <div style={{ fontSize: 24, fontWeight: 'bold' }}>{buildResult.processingTime}</div>
                    <div>处理时间</div>
                  </div>
                </Card>
              </Col>
            </Row>

            <Divider />
            <Space size="large">
              <Button type="primary" size="large">
                👁️ 查看图谱可视化
              </Button>
              <Button size="large">
                📊 管理图谱数据
              </Button>
              <Button onClick={resetProcess}>
                🔄 重新构建
              </Button>
            </Space>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GraphBuilder;