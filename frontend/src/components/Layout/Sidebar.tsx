import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  BuildOutlined,
  SettingOutlined,
  NodeIndexOutlined,
  BranchesOutlined,
  EyeOutlined,
  DatabaseOutlined,
  ShareAltOutlined,
  UnorderedListOutlined,
  FolderOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { MessageOutlined } from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/builder',
      icon: <BuildOutlined />,
      label: '知识图谱构建',
    },
    {
      key: 'manager',
      icon: <DatabaseOutlined />,
      label: '知识图谱管理',
      children: [
        {
          key: '/manager',
          label: '图谱概览',
        },
        {
          key: '/documents',
          label: '文档管理',
        },
        {
          key: '/entities',
          label: '实体管理',
        },
        {
          key: '/relations',
          label: '关系管理',
        },
        {
          key: '/categories',
          label: '分类管理',
        },
      ],
    },
    {
      key: '/disambiguation',
      icon: <BranchesOutlined />,
      label: '实体歧义消除',
    },
    {
      key: '/visualization',
      icon: <EyeOutlined />,
      label: '图谱可视化',
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: '图谱问答',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      theme="light"
      width={250}
      style={{
        boxShadow: '2px 0 12px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div style={{
        height: 72,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderBottom: '1px solid #e8e8e8',
        fontWeight: 'bold',
        fontSize: collapsed ? '18px' : '20px',
        background: 'linear-gradient(180deg, #ffffff 0%, #fafafa 100%)',
        padding: '20px 0',
        letterSpacing: '0.5px'
      }}>
        {collapsed ? '🧠' : '🧠 知识图谱系统'}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        defaultOpenKeys={['builder', 'manager']}
        items={menuItems}
        onClick={handleMenuClick}
        style={{
          borderRight: 0,
          height: 'calc(100vh - 72px)',
          paddingTop: '8px'
        }}
      />
    </Sider>
  );
};

export default Sidebar;