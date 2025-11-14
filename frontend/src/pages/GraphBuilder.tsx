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
  Form,
  Select,
  TreeSelect
} from 'antd';
import {
  InboxOutlined,
  FileTextOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { apiService, Category } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

interface BuildResult {
  documents: number;
}

interface DocumentWithType {
  file: any;
  type: string;
}

interface DocumentStatus {
  id: number;
  filename: string;
  status: string;
  resource_type: string;
}

interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  message: string;
  result?: any;
  documentStatuses?: DocumentStatus[];
}

const GraphBuilder: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [uploadedFiles, setUploadedFiles] = useState<DocumentWithType[]>([]);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [buildResult, setBuildResult] = useState<BuildResult | null>(null);
  const [availableGraphs, setAvailableGraphs] = useState<any[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<string | null>(null);
  const [availableCategories, setAvailableCategories] = useState<Category[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);

  // 获取状态文本
  const getStatusText = (status: string): string => {
    const statusMap: { [key: string]: string } = {
      'pending': '等待处理',
      'cleaning': '文档清洗中',
      'chunking': '文档分块中',
      'extracting_entities': '实体提取中',
      'disambiguating': '实体消歧中',
      'extracting_relations': '关系提取中',
      'building_graph': '构建图谱中',
      'completed': '处理完成',
      'failed': '处理失败'
    };
    return statusMap[status.toLowerCase()] || status;
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig: { [key: string]: { color: string; icon?: any } } = {
      'pending': { color: 'default' },
      'cleaning': { color: 'processing', icon: <LoadingOutlined /> },
      'chunking': { color: 'processing', icon: <LoadingOutlined /> },
      'extracting_entities': { color: 'processing', icon: <LoadingOutlined /> },
      'disambiguating': { color: 'processing', icon: <LoadingOutlined /> },
      'extracting_relations': { color: 'processing', icon: <LoadingOutlined /> },
      'building_graph': { color: 'processing', icon: <LoadingOutlined /> },
      'completed': { color: 'success' },
      'failed': { color: 'error' }
    };

    const config = statusConfig[status.toLowerCase()] || { color: 'default' };
    return (
      <Tag color={config.color} icon={config.icon}>
        {getStatusText(status)}
      </Tag>
    );
  };

  // 处理图谱选择变化，加载该图谱下的分类
  const handleGraphChange = async (graphId: string | null) => {
    setSelectedGraphId(graphId);
    setSelectedCategoryId(null); // 重置分类选择
    setAvailableCategories([]); // 清空分类列表
    
    if (graphId) {
      try {
        const categories = await apiService.getGraphCategories(graphId);
        setAvailableCategories(categories);
      } catch (error) {
        console.error('加载图谱分类失败:', error);
        message.error('加载图谱分类失败');
        setAvailableCategories([]);
      }
    }
  };

  // 处理分类选择变化
  const handleCategoryChange = (categoryId: string | null) => {
    setSelectedCategoryId(categoryId);
  };

  // 构建分类树结构数据
  const buildCategoryTreeData = (categories: Category[]) => {
    const categoryMap = new Map<string, Category & { children?: Category[] }>();
    const rootCategories: (Category & { children?: Category[] })[] = [];
    
    // 首先创建所有分类的映射
    categories.forEach(category => {
      categoryMap.set(category.id, { ...category, children: [] });
    });
    
    // 构建树结构
    categories.forEach(category => {
      const categoryWithChildren = categoryMap.get(category.id)!;
      
      if (category.parent_id && category.parent_id !== selectedGraphId && categoryMap.has(category.parent_id)) {
        // 有父分类且父分类不是图谱ID
        const parent = categoryMap.get(category.parent_id)!;
        if (!parent.children) parent.children = [];
        parent.children.push(categoryWithChildren);
      } else {
        // 根分类（parent_id为图谱ID或为空）
        rootCategories.push(categoryWithChildren);
      }
    });
    
    // 转换为TreeSelect需要的格式
    const convertToTreeData = (cats: (Category & { children?: Category[] })[]): any[] => {
      return cats.map(cat => ({
        title: `📁 ${cat.name}`,
        value: cat.id,
        key: cat.id,
        children: cat.children && cat.children.length > 0 ? convertToTreeData(cat.children) : undefined
      }));
    };
    
    return convertToTreeData(rootCategories);
  };

  // 加载图谱列表函数（当前未使用，保留供将来扩展）
  // const loadAvailableGraphs = async () => {
  //   try {
  //     const graphs = await apiService.getGraphs();
  //     setAvailableGraphs(graphs);
  //   } catch (error) {
  //     console.error('加载图谱列表失败:', error);
  //     message.error('加载图谱列表失败');
  //   }
  // };

  // 加载可用图谱列表
  useEffect(() => {
    const loadData = async () => {
      try {
        const graphs = await apiService.getGraphs();
        setAvailableGraphs(graphs);
      } catch (error) {
        console.error('加载图谱列表失败:', error);
        message.error('加载图谱列表失败');
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
  // const getCategoryPath = (categoryId: string, tree: Category | null): string | null => {
  //   // 暂时不使用分类功能
  //   return null;
  // };

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
    // 保存上传成功的文档ID列表，用于轮询状态
    const uploadedDocIds = result.created_resources.map((doc: any) => doc.id);

    if (uploadedDocIds.length > 0) {
      // 开始轮询文档状态
      startPollingDocumentStatus(uploadedDocIds);
    } else {
      // 没有成功上传的文档，直接显示失败结果
      setTaskStatus({
        task_id: `batch_${Date.now()}`,
        status: 'failed',
        progress: 0,
        message: '所有文档上传失败',
        result: null
      });
      message.error('所有文档上传失败');
    }
  };

  // 轮询文档状态
  const startPollingDocumentStatus = async (documentIds: number[]) => {
    const pollInterval = 2000; // 每2秒轮询一次
    const maxPollingTime = 300000; // 最多轮询5分钟
    const startTime = Date.now();

    const checkStatus = async () => {
      try {
        // 调用批量查询状态接口
        const statuses = await apiService.getBatchDocumentsStatus(documentIds);

        // 统计各状态的文档数量
        const completedCount = statuses.filter(s => s.status.toLowerCase() === 'completed').length;
        const failedCount = statuses.filter(s => s.status.toLowerCase() === 'failed').length;

        // 计算总体进度（基于完成和失败的文档数）
        const finishedCount = completedCount + failedCount;
        const totalCount = documentIds.length;
        const progress = Math.round((finishedCount / totalCount) * 100);

        // 更新状态显示，包括每个文档的详细状态
        setTaskStatus({
          task_id: `batch_${Date.now()}`,
          status: finishedCount === totalCount ? 'completed' : 'processing',
          progress: progress,
          message: '正在处理文档...',
          result: null,
          documentStatuses: statuses  // 保存所有文档的状态信息
        });

        // 检查是否所有文档都处理完成
        if (finishedCount === totalCount) {
          // 所有文档处理完成
          setCurrentStep(2);

          setBuildResult({
            documents: completedCount
          });

          if (completedCount > 0) {
            message.success(`处理完成！成功处理 ${completedCount} 个文档`);
          }
          if (failedCount > 0) {
            message.warning(`有 ${failedCount} 个文档处理失败`);
          }

          return; // 停止轮询
        }

        // 检查是否超时
        if (Date.now() - startTime > maxPollingTime) {
          message.warning('文档处理超时，请稍后在文档管理页面查看处理结果');
          return;
        }

        // 继续轮询
        setTimeout(checkStatus, pollInterval);
      } catch (error) {
        console.error('轮询文档状态失败:', error);
        message.error('获取文档状态失败');
      }
    };

    // 开始第一次检查
    checkStatus();
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
      setCurrentStep(1);

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
      // 如果选择了分类，使用分类ID作为parent_id，否则使用图谱ID
      const parentId = selectedCategoryId || selectedGraphId;
      const batchRequest = {
        parent_id: parentId,
        graph_id: selectedGraphId,
        resources: resources
      };
      
      console.log('📤 批量创建资源请求:', {
        parent_id: parentId,
        graph_id: selectedGraphId,
        category_selected: selectedCategoryId ? '是' : '否',
        resources_count: resources.length
      });
      
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
      setCurrentStep(0);
    } finally {
      // 确保错误处理后的清理
    }
  };

  const resetProcess = () => {
    setCurrentStep(0);
    setUploadedFiles([]);
    setBuildResult(null);
    setTaskStatus(null);
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
                   <Form.Item 
                     label="选择目标图谱"
                     rules={[{ required: true, message: '请选择目标图谱' }]}
                   >
                     <Select 
                       value={selectedGraphId}
                       onChange={handleGraphChange}
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
                   
                   {selectedGraphId && availableCategories.length > 0 && (
                     <Form.Item label="选择分类（可选）">
                       <TreeSelect
                         value={selectedCategoryId}
                         onChange={handleCategoryChange}
                         placeholder="选择图谱下的分类，不选择则添加到图谱根目录"
                         allowClear
                         showSearch
                         treeDefaultExpandAll
                         treeData={buildCategoryTreeData(availableCategories)}
                         notFoundContent="该图谱暂无分类"
                         style={{ width: '100%' }}
                       />
                     </Form.Item>
                   )}
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
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <Text type="secondary">{taskStatus.message}</Text>
                </div>
              </div>
            )}

            {/* 文档处理状态列表 */}
            {taskStatus?.documentStatuses && taskStatus.documentStatuses.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <Title level={5}>📋 文档处理进度</Title>
                <List
                  dataSource={taskStatus.documentStatuses}
                  renderItem={(doc: any) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<FileTextOutlined />}
                        title={doc.filename}
                        description={getStatusText(doc.status)}
                      />
                      {getStatusTag(doc.status)}
                    </List.Item>
                  )}
                  bordered
                  size="small"
                />
              </div>
            )}
          </div>
        )}

        {currentStep === 2 && buildResult && (
          <div>
            <Title level={4}>✅ 处理完成</Title>
            <Alert
              message="文档处理成功！"
              description={`成功处理 ${buildResult.documents} 个文档`}
              type="success"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Divider />
            <Space size="large">
              <Button type="primary" size="large">
                👁️ 查看图谱可视化
              </Button>
              <Button size="large">
                📊 管理图谱数据
              </Button>
              <Button onClick={resetProcess}>
                🔄 重新上传
              </Button>
            </Space>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GraphBuilder;