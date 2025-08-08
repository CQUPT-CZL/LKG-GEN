import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, List, Button, Upload, message, Progress, Modal, Typography, Space, Tag, Timeline, Alert, Divider, Avatar, Tooltip, Badge } from 'antd';
import { UploadOutlined, FileTextOutlined, NodeIndexOutlined, ShareAltOutlined, ClockCircleOutlined, 
         RiseOutlined, DatabaseOutlined, ThunderboltOutlined, TeamOutlined, 
         BugOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined,
         RocketOutlined, BarChartOutlined, PieChartOutlined, LineChartOutlined,
         SettingOutlined, EyeOutlined, BuildOutlined, DownloadOutlined, 
         FireOutlined, HeartOutlined, StarOutlined, SafetyOutlined } from '@ant-design/icons';
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
  const [systemPerformance, setSystemPerformance] = useState({
    cpu: 45,
    memory: 68,
    disk: 32,
    network: {
      upload: 15,
      download: 25
    }
  });
  const [recentActivities, setRecentActivities] = useState([
    { id: 1, type: 'success', message: '知识图谱"技术文档"构建完成', time: '2分钟前', icon: <CheckCircleOutlined /> },
    { id: 2, type: 'info', message: '新用户注册：张三', time: '5分钟前', icon: <TeamOutlined /> },
    { id: 3, type: 'warning', message: '系统内存使用率较高', time: '10分钟前', icon: <ExclamationCircleOutlined /> },
    { id: 4, type: 'success', message: '实体识别任务完成', time: '15分钟前', icon: <RocketOutlined /> },
    { id: 5, type: 'info', message: '数据备份已完成', time: '30分钟前', icon: <SafetyOutlined /> }
  ]);
  const [quickStats, setQuickStats] = useState({
    today_uploads: 12,
    processing_tasks: 3,
    success_rate: 96.5,
    avg_processing_time: 45
  });

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

  // 获取真实系统性能数据
  const fetchSystemPerformance = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/system/performance');
      if (response.ok) {
        const data = await response.json();
        setSystemPerformance({
          cpu: data.cpu_usage,
          memory: data.memory_usage,
          disk: data.disk_usage,
          network: {
            upload: data.network_io.bytes_sent / (1024 * 1024), // 转换为MB
            download: data.network_io.bytes_recv / (1024 * 1024) // 转换为MB
          }
        });
      }
    } catch (error) {
      console.error('获取系统性能数据失败:', error);
      // 如果API调用失败，保持当前数据不变
    }
  };

  useEffect(() => {
    loadStats();
    
    // 立即获取一次真实数据
    fetchSystemPerformance();
    
    // 实时数据更新
    const interval = setInterval(() => {
      // 获取真实系统性能数据
      fetchSystemPerformance();
      
      // 模拟快速统计数据变化（这部分仍然是模拟的）
      setQuickStats(prev => ({
        ...prev,
        today_uploads: prev.today_uploads + (Math.random() > 0.95 ? 1 : 0),
        processing_tasks: Math.max(0, Math.min(10, prev.processing_tasks + (Math.random() > 0.8 ? (Math.random() > 0.5 ? 1 : -1) : 0)))
      }));
    }, 5000);
    
    return () => clearInterval(interval);
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

      {/* 系统性能和快捷操作 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        {/* 系统性能监控 */}
        <Col xs={24} lg={12}>
          <Card title="🖥️ 系统性能监控" extra={<Badge status="processing" text="实时监控" />}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span>CPU使用率</span>
                    <span style={{ color: systemPerformance.cpu > 80 ? '#ff4d4f' : '#52c41a' }}>
                      {systemPerformance.cpu}%
                    </span>
                  </div>
                  <Progress 
                    percent={systemPerformance.cpu} 
                    size="small" 
                    status={systemPerformance.cpu > 80 ? 'exception' : 'normal'}
                    showInfo={false}
                  />
                </div>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span>内存使用率</span>
                    <span style={{ color: systemPerformance.memory > 80 ? '#ff4d4f' : '#52c41a' }}>
                      {systemPerformance.memory}%
                    </span>
                  </div>
                  <Progress 
                    percent={systemPerformance.memory} 
                    size="small" 
                    status={systemPerformance.memory > 80 ? 'exception' : 'normal'}
                    showInfo={false}
                  />
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span>磁盘使用率</span>
                    <span style={{ color: systemPerformance.disk > 80 ? '#ff4d4f' : '#52c41a' }}>
                      {systemPerformance.disk}%
                    </span>
                  </div>
                  <Progress 
                    percent={systemPerformance.disk} 
                    size="small" 
                    status={systemPerformance.disk > 80 ? 'exception' : 'normal'}
                    showInfo={false}
                  />
                </div>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span>网络I/O</span>
                    <span style={{ color: '#52c41a' }}>
                      {Math.round(systemPerformance.network.upload + systemPerformance.network.download)} MB/s
                    </span>
                  </div>
                  <Progress 
                    percent={Math.min(100, (systemPerformance.network.upload + systemPerformance.network.download) * 2)} 
                    size="small" 
                    showInfo={false}
                  />
                </div>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 今日统计 */}
        <Col xs={24} lg={12}>
          <Card title="📈 今日数据概览">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic
                  title="今日上传"
                  value={quickStats.today_uploads}
                  prefix={<UploadOutlined style={{ color: '#1890ff' }} />}
                  suffix="个文档"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="处理中任务"
                  value={quickStats.processing_tasks}
                  prefix={<ThunderboltOutlined style={{ color: '#faad14' }} />}
                  suffix="个"
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="成功率"
                  value={quickStats.success_rate}
                  prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                  suffix="%"
                  precision={1}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="平均处理时间"
                  value={quickStats.avg_processing_time}
                  prefix={<ClockCircleOutlined style={{ color: '#722ed1' }} />}
                  suffix="秒"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 快捷操作面板 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="⚡ 快捷操作" extra={<Button type="link" onClick={() => navigate('/settings')}>更多设置</Button>}>
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={8} md={6} lg={4}>
                <Button 
                  type="primary" 
                  block 
                  icon={<BuildOutlined />} 
                  onClick={() => navigate('/builder')}
                  style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
                >
                  <div>构建图谱</div>
                </Button>
              </Col>
              <Col xs={12} sm={8} md={6} lg={4}>
                <Button 
                  block 
                  icon={<EyeOutlined />} 
                  onClick={() => navigate('/visualization')}
                  style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
                >
                  <div>图谱可视化</div>
                </Button>
              </Col>
              <Col xs={12} sm={8} md={6} lg={4}>
                <Button 
                  block 
                  icon={<DatabaseOutlined />} 
                  onClick={() => navigate('/manager')}
                  style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
                >
                  <div>图谱管理</div>
                </Button>
              </Col>
              <Col xs={12} sm={8} md={6} lg={4}>
                <Button 
                  block 
                  icon={<TeamOutlined />} 
                  onClick={() => navigate('/entities')}
                  style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
                >
                  <div>实体管理</div>
                </Button>
              </Col>
              <Col xs={12} sm={8} md={6} lg={4}>
                <Button 
                  block 
                  icon={<ShareAltOutlined />} 
                  onClick={() => navigate('/relations')}
                  style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
                >
                  <div>关系管理</div>
                </Button>
              </Col>
              <Col xs={12} sm={8} md={6} lg={4}>
                <Button 
                  block 
                  icon={<SettingOutlined />} 
                  onClick={() => navigate('/settings')}
                  style={{ height: '60px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}
                >
                  <div>系统设置</div>
                </Button>
              </Col>
            </Row>
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

      {/* 活动日志和系统状态 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        {/* 最近活动 */}
        <Col xs={24} lg={12}>
          <Card 
            title="📋 最近活动" 
            extra={
              <Space>
                <Badge count={recentActivities.filter(a => a.type === 'warning').length} size="small">
                  <Button type="link" size="small">查看全部</Button>
                </Badge>
              </Space>
            }
          >
            <Timeline
              items={recentActivities.map(activity => ({
                dot: React.cloneElement(activity.icon, { 
                  style: { 
                    color: activity.type === 'success' ? '#52c41a' : 
                           activity.type === 'warning' ? '#faad14' : '#1890ff' 
                  } 
                }),
                children: (
                  <div>
                    <div style={{ marginBottom: 4 }}>{activity.message}</div>
                    <div style={{ fontSize: '12px', color: '#999' }}>{activity.time}</div>
                  </div>
                )
              }))}
            />
          </Card>
        </Col>

        {/* 系统健康状态 */}
        <Col xs={24} lg={12}>
          <Card title="💊 系统健康状态">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Alert
                message="系统运行正常"
                description="所有核心服务运行稳定，性能指标正常"
                type="success"
                icon={<CheckCircleOutlined />}
                showIcon
              />
              
              <div>
                <Title level={5} style={{ marginBottom: 16 }}>🔧 服务状态</Title>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Space>
                      <Badge status="success" />
                      <span>API服务</span>
                    </Space>
                  </Col>
                  <Col span={12}>
                    <Space>
                      <Badge status="success" />
                      <span>数据库</span>
                    </Space>
                  </Col>
                  <Col span={12}>
                    <Space>
                      <Badge status="processing" />
                      <span>AI模型</span>
                    </Space>
                  </Col>
                  <Col span={12}>
                    <Space>
                      <Badge status="success" />
                      <span>文件存储</span>
                    </Space>
                  </Col>
                </Row>
              </div>

              <div>
                <Title level={5} style={{ marginBottom: 16 }}>📊 数据统计</Title>
                <Row gutter={[16, 8]}>
                  <Col span={8}>
                    <Tooltip title="本周新增">
                      <Statistic
                        title="图谱"
                        value={5}
                        prefix={<RiseOutlined style={{ color: '#52c41a' }} />}
                        valueStyle={{ fontSize: '16px', color: '#52c41a' }}
                      />
                    </Tooltip>
                  </Col>
                  <Col span={8}>
                    <Tooltip title="本周新增">
                      <Statistic
                        title="实体"
                        value={128}
                        prefix={<RiseOutlined style={{ color: '#1890ff' }} />}
                        valueStyle={{ fontSize: '16px', color: '#1890ff' }}
                      />
                    </Tooltip>
                  </Col>
                  <Col span={8}>
                    <Tooltip title="本周新增">
                      <Statistic
                        title="关系"
                        value={89}
                        prefix={<RiseOutlined style={{ color: '#722ed1' }} />}
                        valueStyle={{ fontSize: '16px', color: '#722ed1' }}
                      />
                    </Tooltip>
                  </Col>
                </Row>
              </div>
            </Space>
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