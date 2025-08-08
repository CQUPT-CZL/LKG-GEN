import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, List, Typography, Button, Space } from 'antd';
import { 
  DatabaseOutlined, 
  NodeIndexOutlined, 
  BranchesOutlined,
  FileTextOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

interface DashboardStats {
  totalEntities: number;
  totalRelations: number;
  totalDocuments: number;
  totalGraphs: number;
  recentActivities: Array<{
    id: string;
    type: string;
    description: string;
    timestamp: string;
  }>;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalEntities: 0,
    totalRelations: 0,
    totalDocuments: 0,
    totalGraphs: 0,
    recentActivities: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 模拟数据加载
    setTimeout(() => {
      setStats({
        totalEntities: 1248,
        totalRelations: 3567,
        totalDocuments: 89,
        totalGraphs: 12,
        recentActivities: [
          {
            id: '1',
            type: 'build',
            description: '完成文档 "AI技术报告.pdf" 的知识图谱构建',
            timestamp: '2024-01-15 14:30'
          },
          {
            id: '2',
            type: 'entity',
            description: '新增实体 "深度学习" 及其相关关系',
            timestamp: '2024-01-15 13:45'
          },
          {
            id: '3',
            type: 'relation',
            description: '优化了 "包含" 关系的权重计算',
            timestamp: '2024-01-15 12:20'
          },
          {
            id: '4',
            type: 'visualization',
            description: '导出了 "技术架构" 知识图谱可视化',
            timestamp: '2024-01-15 11:15'
          }
        ]
      });
      setLoading(false);
    }, 1000);
  }, []);

  const quickActions = [
    {
      title: '📄 构建知识图谱',
      description: '上传文档，自动提取实体和关系',
      action: () => navigate('/builder'),
      color: '#1890ff'
    },
    {
      title: '🔍 管理图谱',
      description: '查看和编辑现有知识图谱',
      action: () => navigate('/manager'),
      color: '#52c41a'
    },
    {
      title: '👁️ 可视化展示',
      description: '交互式图谱可视化和探索',
      action: () => navigate('/visualization'),
      color: '#722ed1'
    },
    {
      title: '⚙️ 系统设置',
      description: '配置系统参数和模型设置',
      action: () => navigate('/settings'),
      color: '#fa8c16'
    }
  ];

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
              title="总实体数"
              value={stats.totalEntities}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#3f8600' }}
              suffix={<ArrowUpOutlined style={{ fontSize: '12px' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总关系数"
              value={stats.totalRelations}
              prefix={<BranchesOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix={<ArrowUpOutlined style={{ fontSize: '12px' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="处理文档"
              value={stats.totalDocuments}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="知识图谱"
              value={stats.totalGraphs}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 快速操作 */}
        <Col xs={24} lg={16}>
          <Card title="🚀 快速操作" loading={loading}>
            <Row gutter={[16, 16]}>
              {quickActions.map((action, index) => (
                <Col xs={24} sm={12} key={index}>
                  <Card 
                    hoverable
                    className="feature-card"
                    onClick={action.action}
                    style={{ borderLeft: `4px solid ${action.color}` }}
                  >
                    <Card.Meta
                      title={action.title}
                      description={action.description}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={8}>
          <Card title="📋 最近活动" loading={loading}>
            <List
              dataSource={stats.recentActivities}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={item.description}
                    description={item.timestamp}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 系统状态 */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24}>
          <Card title="💻 系统状态">
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={85} format={() => 'CPU'} />
                  <div style={{ marginTop: 8 }}>处理器使用率</div>
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={62} format={() => 'MEM'} />
                  <div style={{ marginTop: 8 }}>内存使用率</div>
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div style={{ textAlign: 'center' }}>
                  <Progress type="circle" percent={45} format={() => 'DISK'} />
                  <div style={{ marginTop: 8 }}>磁盘使用率</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;