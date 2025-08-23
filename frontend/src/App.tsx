import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Dashboard from './pages/Dashboard';
import GraphBuilder from './pages/GraphBuilder';
import TaskManager from './pages/TaskManager';
import GraphManager from './pages/GraphManager';
import DocumentManager from './pages/DocumentManager';
import GraphVisualization from './pages/GraphVisualization';
import EntityManager from './pages/EntityManager';
import RelationManager from './pages/RelationManager';
import CategoryManager from './pages/CategoryManager';
import Settings from './pages/Settings';

const { Content } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Header />
        <Content style={{ margin: '24px', background: '#fff', padding: '24px', borderRadius: '8px' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/builder" element={<GraphBuilder />} />
            <Route path="/tasks" element={<TaskManager />} />
            <Route path="/manager" element={<GraphManager />} />
            <Route path="/documents" element={<DocumentManager />} />
            <Route path="/visualization" element={<GraphVisualization />} />
            <Route path="/entities" element={<EntityManager />} />
            <Route path="/relations" element={<RelationManager />} />
            <Route path="/categories" element={<CategoryManager />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;