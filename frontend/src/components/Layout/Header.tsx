import React from 'react';
import { Layout, Typography, Space, Badge, Button } from 'antd';
import { BellOutlined, UserOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header: React.FC = () => {
  return (
    <AntHeader style={{ 
      background: '#fff', 
      padding: '0 24px', 
      borderBottom: '1px solid #f0f0f0',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <div>
        <Text strong style={{ fontSize: '16px' }}>
          知识图谱管理系统
        </Text>
      </div>
      
      <Space size="middle">
        <Button 
          type="text" 
          icon={<QuestionCircleOutlined />}
          title="帮助文档"
        />
        <Badge count={3}>
          <Button 
            type="text" 
            icon={<BellOutlined />}
            title="通知"
          />
        </Badge>
        <Button 
          type="text" 
          icon={<UserOutlined />}
          title="用户中心"
        >
          管理员
        </Button>
      </Space>
    </AntHeader>
  );
};

export default Header;