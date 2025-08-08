import React, { useState } from 'react';
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
  Col
} from 'antd';
import {
  InboxOutlined,
  FileTextOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;

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

const GraphBuilder: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [buildResult, setBuildResult] = useState<BuildResult | null>(null);
  const [processSteps, setProcessSteps] = useState<ProcessStep[]>([
    {
      title: '文档分块',
      description: '将文档切分为语义块',
      status: 'wait'
    },
    {
      title: '命名实体识别',
      description: '识别文档中的实体',
      status: 'wait'
    },
    {
      title: '实体消歧',
      description: '合并相似实体',
      status: 'wait'
    },
    {
      title: '关系抽取',
      description: '提取实体间关系',
      status: 'wait'
    },
    {
      title: '图谱构建',
      description: '生成知识图谱',
      status: 'wait'
    }
  ]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.pdf,.txt,.docx,.md',
    beforeUpload: (file) => {
      const isValidType = [
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown'
      ].includes(file.type);
      
      if (!isValidType) {
        message.error('只支持 PDF、TXT、DOCX、MD 格式的文件！');
        return false;
      }
      
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB！');
        return false;
      }
      
      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setUploadedFiles(info.fileList);
    },
    onDrop: (e) => {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };

  const startProcessing = async () => {
    if (uploadedFiles.length === 0) {
      message.warning('请先上传文档！');
      return;
    }

    setIsProcessing(true);
    setCurrentStep(1);

    // 模拟处理过程
    for (let i = 0; i < processSteps.length; i++) {
      const newSteps = [...processSteps];
      newSteps[i].status = 'process';
      setProcessSteps(newSteps);

      // 模拟处理时间
      await new Promise(resolve => setTimeout(resolve, 2000));

      newSteps[i].status = 'finish';
      newSteps[i].progress = 100;
      setProcessSteps(newSteps);
    }

    // 设置结果
    setBuildResult({
      entities: 1248,
      relations: 3567,
      documents: uploadedFiles.length,
      processingTime: '3分42秒'
    });

    setIsProcessing(false);
    setCurrentStep(2);
    message.success('知识图谱构建完成！');
  };

  const resetProcess = () => {
    setCurrentStep(0);
    setUploadedFiles([]);
    setIsProcessing(false);
    setBuildResult(null);
    setProcessSteps(processSteps.map(step => ({ ...step, status: 'wait', progress: 0 })));
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
          上传文档，自动提取实体和关系，构建知识图谱。支持 PDF、TXT、DOCX、MD 格式。
        </Paragraph>
      </div>

      <Card>
        <Steps current={currentStep} items={mainSteps} style={{ marginBottom: 32 }} />

        {currentStep === 0 && (
          <div>
            <Title level={4}>📁 上传文档</Title>
            <Dragger {...uploadProps} style={{ marginBottom: 24 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个或批量上传。支持 PDF、TXT、DOCX、MD 格式，单个文件不超过 50MB。
              </p>
            </Dragger>

            {uploadedFiles.length > 0 && (
              <div>
                <Title level={5}>📋 已上传文件 ({uploadedFiles.length})</Title>
                <List
                  dataSource={uploadedFiles}
                  renderItem={(file) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<FileTextOutlined />}
                        title={file.name}
                        description={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                      />
                      <Tag color="green">已上传</Tag>
                    </List.Item>
                  )}
                />
                <Divider />
                <Space>
                  <Button type="primary" size="large" onClick={startProcessing}>
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

            <div style={{ marginBottom: 24 }}>
              {processSteps.map((step, index) => (
                <Card key={index} size="small" style={{ marginBottom: 16 }}>
                  <Row align="middle">
                    <Col span={6}>
                      <Space>
                        {step.status === 'finish' && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                        {step.status === 'process' && <LoadingOutlined />}
                        <Text strong>{step.title}</Text>
                      </Space>
                    </Col>
                    <Col span={10}>
                      <Text type="secondary">{step.description}</Text>
                    </Col>
                    <Col span={8}>
                      <Progress
                        percent={step.status === 'finish' ? 100 : step.status === 'process' ? 50 : 0}
                        size="small"
                        status={step.status === 'process' ? 'active' : undefined}
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