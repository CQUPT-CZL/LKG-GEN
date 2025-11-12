import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, List, Button, Upload, message, Modal, Typography, Space, Tag, Divider, Avatar, Tooltip } from 'antd';
import { UploadOutlined, FileTextOutlined, NodeIndexOutlined, ShareAltOutlined, DatabaseOutlined, 
         CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
         RocketOutlined, BarChartOutlined, EyeOutlined, BuildOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useNavigate } from 'react-router-dom';
import { apiService, Graph, SourceResource } from '../services/api';

const { Title, Paragraph } = Typography;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [documents, setDocuments] = useState<SourceResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [selectedGraph, setSelectedGraph] = useState<string>('');

  // 加载数据
  const loadData = async () => {
    try {
      setLoading(true);
      const [graphsData, documentsData] = await Promise.all([
        apiService.getGraphs(0, 10),
        apiService.getDocuments(0, 10)
      ]);
      setGraphs(graphsData);
      setDocuments(documentsData);
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 文件上传处理
  const handleUpload = async (file: File) => {
    if (!selectedGraph) {
      message.error('请先选择一个知识图谱');
      return;
    }

    try {
      setUploading(true);
      const reader = new FileReader();
      reader.onload = async (e) => {
        const content = e.target?.result as string;
        await apiService.createResources({
          parent_id: selectedGraph,
          graph_id: selectedGraph,
          resources: [{
            filename: file.name,
            content: content,
            type: file.type || 'TEXT'
          }]
        });
        message.success('文档上传成功');
        setUploadModalVisible(false);
        loadData();
      };
      reader.readAsText(file);
    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const uploadProps: UploadProps = {
    beforeUpload: (file) => {
      handleUpload(file);
      return false;
    },
    showUploadList: false,
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'success';
      case 'PROCESSING': return 'processing';
      case 'FAILED': return 'error';
      default: return 'default';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'COMPLETED': return '已完成';
      case 'PROCESSING': return '处理中';
      case 'FAILED': return '失败';
      case 'PENDING': return '等待中';
      default: return status;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8, color: '#262626', fontWeight: 600 }}>📊 知识图谱平台控制台</Title>
        <Paragraph style={{ color: '#8c8c8c', fontSize: '14px' }}>欢迎使用知识图谱平台，在这里您可以管理文档、构建知识图谱并进行可视化分析。</Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[20, 20]} style={{ marginBottom: 32 }}>
        <Col xs={24} sm={12} md={6}>
          <Card
            style={{
              borderRadius: '12px',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'
            }}
            hoverable
          >
            <Statistic
              title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>知识图谱总数</span>}
              value={graphs.length}
              prefix={<NodeIndexOutlined style={{ color: '#1890ff', fontSize: '20px' }} />}
              valueStyle={{ color: '#262626', fontSize: '28px', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card
            style={{
              borderRadius: '12px',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'
            }}
            hoverable
          >
            <Statistic
              title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>文档总数</span>}
              value={documents.length}
              prefix={<FileTextOutlined style={{ color: '#52c41a', fontSize: '20px' }} />}
              valueStyle={{ color: '#262626', fontSize: '28px', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card
            style={{
              borderRadius: '12px',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'
            }}
            hoverable
          >
            <Statistic
              title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>已完成文档</span>}
              value={documents.filter(doc => doc.status === 'COMPLETED').length}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: '20px' }} />}
              valueStyle={{ color: '#262626', fontSize: '28px', fontWeight: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card
            style={{
              borderRadius: '12px',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'
            }}
            hoverable
          >
            <Statistic
              title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>处理中文档</span>}
              value={documents.filter(doc => doc.status === 'PROCESSING').length}
              prefix={<RocketOutlined style={{ color: '#faad14', fontSize: '20px' }} />}
              valueStyle={{ color: '#262626', fontSize: '28px', fontWeight: 600 }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要功能区 */}
      <Row gutter={[20, 20]}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <DatabaseOutlined style={{ color: '#1890ff', fontSize: '18px' }} />
                <span style={{ fontSize: '16px', fontWeight: 600, color: '#262626' }}>知识图谱</span>
              </Space>
            }
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<BuildOutlined />}
                  onClick={() => navigate('/manager')}
                  style={{
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(24, 144, 255, 0.2)'
                  }}
                >
                  管理图谱
                </Button>
              </Space>
            }
            loading={loading}
            style={{
              borderRadius: '12px',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
            }}
          >
            <List
              dataSource={graphs}
              renderItem={(graph) => (
                <List.Item
                  actions={[
                    <Button 
                      type="link" 
                      icon={<EyeOutlined />}
                      onClick={() => navigate('/visualization')}
                    >
                      查看
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<NodeIndexOutlined />} />}
                    title={graph.name}
                    description={graph.description || '暂无描述'}
                  />
                </List.Item>
              )}
              locale={{ emptyText: '暂无知识图谱' }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <FileTextOutlined style={{ color: '#52c41a', fontSize: '18px' }} />
                <span style={{ fontSize: '16px', fontWeight: 600, color: '#262626' }}>最近文档</span>
              </Space>
            }
            extra={
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={() => setUploadModalVisible(true)}
                style={{
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(82, 196, 26, 0.2)'
                }}
              >
                上传文档
              </Button>
            }
            loading={loading}
            style={{
              borderRadius: '12px',
              border: '1px solid #f0f0f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
            }}
          >
            <List
              dataSource={documents}
              renderItem={(doc) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={<FileTextOutlined />} />}
                    title={
                      <Space>
                        {doc.filename}
                        <Tag color={getStatusColor(doc.status)}>
                          {getStatusText(doc.status)}
                        </Tag>
                      </Space>
                    }
                    description={`上传时间: ${new Date(doc.uploaded_at).toLocaleString()}`}
                  />
                </List.Item>
              )}
              locale={{ emptyText: '暂无文档' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card
        title="🚀 快速操作"
        style={{
          marginTop: 20,
          borderRadius: '12px',
          border: '1px solid #f0f0f0',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)'
        }}
      >
        <Row gutter={[20, 20]}>
          <Col xs={24} sm={8}>
            <Button
              type="dashed"
              block
              size="large"
              icon={<BuildOutlined style={{ fontSize: '20px' }} />}
              onClick={() => navigate('/manager')}
              style={{
                borderRadius: '12px',
                height: '80px',
                fontSize: '16px',
                borderWidth: '2px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              创建知识图谱
            </Button>
          </Col>
          <Col xs={24} sm={8}>
            <Button
              type="dashed"
              block
              size="large"
              icon={<UploadOutlined style={{ fontSize: '20px' }} />}
              onClick={() => setUploadModalVisible(true)}
              style={{
                borderRadius: '12px',
                height: '80px',
                fontSize: '16px',
                borderWidth: '2px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              上传文档
            </Button>
          </Col>
          <Col xs={24} sm={8}>
            <Button
              type="dashed"
              block
              size="large"
              icon={<BarChartOutlined style={{ fontSize: '20px' }} />}
              onClick={() => navigate('/visualization')}
              style={{
                borderRadius: '12px',
                height: '80px',
                fontSize: '16px',
                borderWidth: '2px',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              数据可视化
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 上传文档模态框 */}
      <Modal
        title="上传文档"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <div style={{ marginBottom: 16 }}>
          <label>选择知识图谱：</label>
          <select 
            value={selectedGraph} 
            onChange={(e) => setSelectedGraph(e.target.value)}
            style={{ width: '100%', padding: '8px', marginTop: '8px' }}
          >
            <option value="">请选择知识图谱</option>
            {graphs.map(graph => (
              <option key={graph.id} value={graph.id}>{graph.name}</option>
            ))}
          </select>
        </div>
        <Upload {...uploadProps} disabled={!selectedGraph || uploading}>
          <Button icon={<UploadOutlined />} loading={uploading}>
            {uploading ? '上传中...' : '选择文件'}
          </Button>
        </Upload>
      </Modal>
    </div>
  );
};

export default Dashboard;