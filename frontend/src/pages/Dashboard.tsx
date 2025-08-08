import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, List, Button, Upload, message, Progress, Modal, Typography, Space, Tag } from 'antd';
import { UploadOutlined, FileTextOutlined, NodeIndexOutlined, ShareAltOutlined, ClockCircleOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useNavigate } from 'react-router-dom';
import { apiService, Graph, SystemStats, TaskStatus } from '../services/api';

const { Title, Paragraph } = Typography;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [currentTask, setCurrentTask] = useState<string>('');
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [recentGraphs, setRecentGraphs] = useState<Graph[]>([]);
  const [loading, setLoading] = useState(true);

  // 加载统计数据
  const loadStats = async () => {
    try {
      const statsData = await apiService.getStats();
      setStats(statsData);
      setRecentGraphs(statsData.recent_graphs || []);
    } catch (error) {
      console.error('加载统计数据失败:', error);
      message.error('加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setShowProgress(true);
    setUploadProgress(0);
    setCurrentTask('正在上传文件...');

    try {
      // 上传文件
      const uploadResult = await apiService.uploadDocument(file);
      const taskId = uploadResult.task_id;
      
      message.success(`文件上传成功: ${uploadResult.filename}`);
      setCurrentTask('正在处理文档...');
      
      // 轮询任务状态
      const pollTaskStatus = async () => {
        try {
          const taskStatus: TaskStatus = await apiService.getTaskStatus(taskId);
          
          setUploadProgress(taskStatus.progress);
          setCurrentTask(taskStatus.message);
          
          if (taskStatus.status === 'completed') {
            message.success('知识图谱构建完成！');
            setUploading(false);
            setShowProgress(false);
            // 重新加载统计数据
            loadStats();
          } else if (taskStatus.status === 'failed') {
            message.error(`处理失败: ${taskStatus.message}`);
            setUploading(false);
            setShowProgress(false);
          } else {
            // 继续轮询
            setTimeout(pollTaskStatus, 2000);
          }
        } catch (error) {
          console.error('获取任务状态失败:', error);
          message.error('获取任务状态失败');
          setUploading(false);
          setShowProgress(false);
        }
      };
      
      // 开始轮询
      setTimeout(pollTaskStatus, 2000);
      
    } catch (error) {
      console.error('文件上传失败:', error);
      message.error('文件上传失败');
      setUploading(false);
      setShowProgress(false);
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    // 移除accept限制，支持所有文件类型
    // accept: '.pdf,.doc,.docx,.txt',
    beforeUpload: (file) => {
      handleUpload(file);
      return false; // 阻止默认上传
    },
    showUploadList: false,
  };



  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">📊 系统仪表板</Title>
        <Paragraph className="page-description">
          欢迎使用知识图谱管理系统！这里是您的数据概览和快速操作中心。
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="知识图谱总数"
              value={stats?.total_graphs || 0}
              prefix={<NodeIndexOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="实体总数"
              value={stats?.total_entities || 0}
              prefix={<FileTextOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="关系总数"
              value={stats?.total_relations || 0}
              prefix={<ShareAltOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={stats?.system_health || '未知'}
              prefix={<ClockCircleOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 文档上传 */}
        <Col xs={24} lg={16}>
          <Card title="📄 构建知识图谱">
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Upload {...uploadProps} disabled={uploading}>
                <Button 
                  icon={<UploadOutlined />} 
                  size="large" 
                  loading={uploading}
                  disabled={uploading}
                >
                  {uploading ? '处理中...' : '上传文档'}
                </Button>
              </Upload>
              <div style={{ marginTop: 16, color: '#666' }}>
                支持所有格式文档
              </div>
            </div>
          </Card>
        </Col>

        {/* 最近图谱 */}
        <Col xs={24} lg={8}>
          <Card title="📊 最近图谱" loading={loading}>
            <List
              loading={loading}
              dataSource={recentGraphs}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button 
                      type="link" 
                      onClick={() => navigate(`/graph/${item.id}`)}
                    >
                      查看详情
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        {item.name}
                        <Tag color={item.status === 'active' ? 'green' : 'orange'}>
                          {item.status === 'active' ? '活跃' : item.status}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <div>{item.description}</div>
                        <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                          实体: {item.entity_count} | 关系: {item.relation_count} | 创建时间: {new Date(item.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 进度弹窗 */}
      <Modal
        title="知识图谱构建进度"
        open={showProgress}
        footer={null}
        closable={false}
        centered
      >
        <div style={{ textAlign: 'center' }}>
          <Progress 
            type="circle" 
            percent={Math.round(uploadProgress)} 
            status={uploading ? 'active' : 'success'}
          />
          <div style={{ marginTop: 16, fontSize: '16px' }}>
            {currentTask}
          </div>
        </div>
      </Modal>


    </div>
  );
};

export default Dashboard;