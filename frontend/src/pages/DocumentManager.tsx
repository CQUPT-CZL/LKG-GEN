import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Popconfirm,
  message,
  Row,
  Col,
  Statistic,
  Modal,
  Descriptions,
  Tabs,
  Spin
} from 'antd';
import {
  FileTextOutlined,
  EyeOutlined,
  DeleteOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { apiService, SourceResource } from '../services/api';
import type { ColumnsType } from 'antd/es/table';

const { Title, Paragraph } = Typography;

const DocumentManager: React.FC = () => {
  const [documents, setDocuments] = useState<SourceResource[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<SourceResource | null>(null);
  const [documentContent, setDocumentContent] = useState<string>('');
  const [contentLoading, setContentLoading] = useState(false);

  // 加载文档列表
  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await apiService.getDocuments(0, 1000);
      setDocuments(data);
    } catch (error) {
      console.error('加载文档列表失败:', error);
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取文档内容
  const fetchDocumentContent = async (documentId: number) => {
    try {
      setContentLoading(true);
      const document = await apiService.getDocument(documentId);
      // 从SourceResource对象中提取content字段
      setDocumentContent(document.content || '暂无内容');
    } catch (error) {
      console.error('获取文档内容失败:', error);
      message.error('获取文档内容失败');
      setDocumentContent('无法加载文档内容');
    } finally {
      setContentLoading(false);
    }
  };

  // 查看文档详情
  const handleView = (record: SourceResource) => {
    setSelectedDocument(record);
    setViewModalVisible(true);
    fetchDocumentContent(record.id);
  };

  // 删除文档
  const handleDelete = async (record: SourceResource) => {
    try {
      const result = await apiService.deleteDocument(record.id);
      
      // 展示删除详情
      const { details } = result;
      const deletedCount = details.deleted_entities?.length || 0;
      const updatedCount = details.updated_entities?.length || 0;
      
      Modal.success({
        title: '🎉 文档删除成功',
        width: 600,
        content: (
          <div style={{ marginTop: 16 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="📄 文档名称">{record.filename}</Descriptions.Item>
              <Descriptions.Item label="🗑️ 删除的实体数量">
                <Tag color="red">{deletedCount} 个</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="🔄 更新的实体数量">
                <Tag color="blue">{updatedCount} 个</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="📊 Neo4j文档节点">
                <Tag color={details.neo4j_document_deleted ? "green" : "orange"}>
                  {details.neo4j_document_deleted ? "✅ 删除成功" : "⚠️ 未找到"}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="💾 SQLite记录">
                <Tag color={details.sqlite_document_deleted ? "green" : "red"}>
                  {details.sqlite_document_deleted ? "✅ 删除成功" : "❌ 删除失败"}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
            
            {deletedCount > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>🗑️ 已删除的实体：</h4>
                <div style={{ maxHeight: 120, overflow: 'auto' }}>
                  {details.deleted_entities.map((entity: string, index: number) => (
                    <Tag key={index} color="red" style={{ margin: '2px' }}>
                      {entity}
                    </Tag>
                  ))}
                </div>
              </div>
            )}
            
            {updatedCount > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>🔄 已更新的实体：</h4>
                <div style={{ maxHeight: 120, overflow: 'auto' }}>
                  {details.updated_entities.map((entity: string, index: number) => (
                    <Tag key={index} color="blue" style={{ margin: '2px' }}>
                      {entity}
                    </Tag>
                  ))}
                </div>
              </div>
            )}
          </div>
        ),
        onOk: () => {
          loadDocuments();
        }
      });
    } catch (error) {
      console.error('删除文档失败:', error);
      message.error('删除文档失败');
    }
  };

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的文档');
      return;
    }

    try {
      const results = [];
      let totalDeletedEntities = 0;
      let totalUpdatedEntities = 0;
      let successCount = 0;
      let failedCount = 0;

      for (const id of selectedRowKeys) {
        try {
          const result = await apiService.deleteDocument(id as number);
          results.push({ id, success: true, result });
          totalDeletedEntities += result.details.deleted_entities?.length || 0;
          totalUpdatedEntities += result.details.updated_entities?.length || 0;
          successCount++;
        } catch (error) {
          results.push({ id, success: false, error });
          failedCount++;
        }
      }

      // 展示批量删除结果
      Modal.success({
        title: '📊 批量删除完成',
        width: 700,
        content: (
          <div style={{ marginTop: 16 }}>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="✅ 成功删除">
                <Tag color="green">{successCount} 个文档</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="❌ 删除失败">
                <Tag color="red">{failedCount} 个文档</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="🗑️ 总删除实体">
                <Tag color="red">{totalDeletedEntities} 个</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="🔄 总更新实体">
                <Tag color="blue">{totalUpdatedEntities} 个</Tag>
              </Descriptions.Item>
            </Descriptions>
            
            {failedCount > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4 style={{ color: '#ff4d4f' }}>❌ 删除失败的文档：</h4>
                {results
                   .filter(r => !r.success)
                   .map((r, index) => (
                     <Tag key={index} color="red" style={{ margin: '2px' }}>
                       {`ID: ${r.id}`}
                     </Tag>
                   ))
                 }
              </div>
            )}
          </div>
        ),
        onOk: () => {
          setSelectedRowKeys([]);
          loadDocuments();
        }
      });
    } catch (error) {
      console.error('批量删除失败:', error);
      message.error('批量删除失败');
    }
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
      processing: { color: 'processing', icon: <LoadingOutlined />, text: '处理中' },
      completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      failed: { color: 'error', icon: <ExclamationCircleOutlined />, text: '失败' }
    };

    const config = statusConfig[status.toLowerCase() as keyof typeof statusConfig] || statusConfig.pending;
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 格式化日期
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  // 表格列定义
  const columns: ColumnsType<SourceResource> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      align: 'center'
    },
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      width: 200,
      ellipsis: true,
      render: (text: string) => (
        <Space>
          <FileTextOutlined style={{ color: '#1890ff' }} />
          <span title={text}>{text}</span>
        </Space>
      )
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 120,
      align: 'center',
      render: (text: string) => (
        <Tag color="blue">{text}</Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      align: 'center',
      render: (status: string) => getStatusTag(status)
    },
    {
      title: '上传时间',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      width: 180,
      render: (date: string) => formatDate(date)
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
            size="small"
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个文档吗？"
            description="删除后将无法恢复，相关的实体和关系也会被清理"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  // 统计信息
  const getStatistics = () => {
    const total = documents.length;
    const pending = documents.filter(doc => doc.status.toLowerCase() === 'pending').length;
    const processing = documents.filter(doc => doc.status.toLowerCase() === 'processing').length;
    const completed = documents.filter(doc => doc.status.toLowerCase() === 'completed').length;
    const failed = documents.filter(doc => doc.status.toLowerCase() === 'failed').length;

    return { total, pending, processing, completed, failed };
  };

  const stats = getStatistics();

  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>📄 文档管理</Title>
        <Paragraph>管理SQLite数据库中的源文档，查看文档状态和处理进度。</Paragraph>
      </div>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="文档总数"
              value={stats.total}
              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="待处理"
              value={stats.pending}
              prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="处理中"
              value={stats.processing}
              prefix={<LoadingOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completed}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Button onClick={loadDocuments} loading={loading}>
            刷新列表
          </Button>
          {selectedRowKeys.length > 0 && (
            <Popconfirm
              title={`确定要删除选中的 ${selectedRowKeys.length} 个文档吗？`}
              description="删除后将无法恢复，相关的实体和关系也会被清理"
              onConfirm={handleBatchDelete}
              okText="确定"
              cancelText="取消"
            >
              <Button danger>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
      </Card>

      {/* 文档列表 */}
      <Card>
        <Table
          rowSelection={rowSelection}
          columns={columns}
          dataSource={documents}
          rowKey="id"
          loading={loading}
          scroll={{ x: 800 }}
          pagination={{
            total: documents.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 文档详情模态框 */}
      <Modal
        title={selectedDocument ? `文档详情 - ${selectedDocument.filename}` : '文档详情'}
        open={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false);
          setDocumentContent('');
        }}
        footer={[
          <Button key="close" onClick={() => {
            setViewModalVisible(false);
            setDocumentContent('');
          }}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        {selectedDocument && (
          <Tabs
            defaultActiveKey="info"
            items={[
              {
                key: 'info',
                label: '文档信息',
                children: (
                  <Descriptions column={1} bordered>
                    <Descriptions.Item label="文档ID">{selectedDocument.id}</Descriptions.Item>
                    <Descriptions.Item label="文件名">
                      {selectedDocument.filename}
                    </Descriptions.Item>
                    <Descriptions.Item label="资源类型">
                      <Tag color="blue">{selectedDocument.resource_type}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="状态">
                      {getStatusTag(selectedDocument.status)}
                    </Descriptions.Item>
                    <Descriptions.Item label="上传时间">
                      {formatDate(selectedDocument.uploaded_at)}
                    </Descriptions.Item>
                  </Descriptions>
                )
              },
              {
                key: 'content',
                label: '文档内容',
                children: (
                  contentLoading ? (
                    <Spin tip="正在加载文档内容...">
                      <div style={{ height: 400, width: '100%' }} />
                    </Spin>
                  ) : (
                    <div style={{ maxHeight: 400, overflowY: 'auto', padding: '8px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                        {documentContent}
                      </ReactMarkdown>
                    </div>
                  )
                )
              }
            ]}
          />
        )}
      </Modal>
    </div>
  );
};

export default DocumentManager;