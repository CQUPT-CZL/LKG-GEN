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
      key: 'builder',
      icon: <BuildOutlined />,
      label: '知识图谱构建',
      children: [
        {
          key: '/tasks',
          label: '任务管理',
        },
        {
          key: '/builder',
          label: '实时构建',
        },
      ],
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
      key: '/visualization',
      icon: <EyeOutlined />,
      label: '图谱可视化',
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
    >
      <div style={{ 
        height: 64, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        borderBottom: '1px solid #f0f0f0',
        fontWeight: 'bold',
        fontSize: collapsed ? '16px' : '18px'
      }}>
        {collapsed ? '🧠' : '🧠 知识图谱系统'}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        defaultOpenKeys={['builder', 'manager']}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ borderRight: 0, height: 'calc(100vh - 64px)' }}
      />
    </Sider>
  );
};

export default Sidebar;