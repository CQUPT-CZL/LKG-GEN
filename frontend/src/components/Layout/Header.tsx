import React from 'react';
import { Layout, Typography, Space, Badge, Button } from 'antd';
import { BellOutlined, UserOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header: React.FC = () => {
  return (
    <AntHeader style={{
      background: '#fff',
      padding: '0 32px',
      borderBottom: '1px solid #e8e8e8',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      height: '72px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
    }}>
      <div>
        <Text strong style={{ fontSize: '18px', color: '#262626', letterSpacing: '0.5px' }}>
          知识图谱管理系统
        </Text>
      </div>

      <Space size="large">
        <Button
          type="text"
          icon={<QuestionCircleOutlined style={{ fontSize: '16px' }} />}
          title="帮助文档"
          style={{
            borderRadius: '8px',
            transition: 'all 0.3s ease'
          }}
        />
        <Badge count={3} offset={[-2, 2]}>
          <Button
            type="text"
            icon={<BellOutlined style={{ fontSize: '16px' }} />}
            title="通知"
            style={{
              borderRadius: '8px',
              transition: 'all 0.3s ease'
            }}
          />
        </Badge>
        <Button
          type="text"
          icon={<UserOutlined style={{ fontSize: '16px' }} />}
          title="用户中心"
          style={{
            borderRadius: '8px',
            padding: '4px 16px',
            background: 'linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%)',
            transition: 'all 0.3s ease'
          }}
        >
          <Text style={{ marginLeft: '4px', fontSize: '14px' }}>管理员</Text>
        </Button>
      </Space>
    </AntHeader>
  );
};

export default Header;