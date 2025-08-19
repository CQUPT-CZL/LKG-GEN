import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Select,
  Slider,
  Switch,
  Tooltip,
  Drawer,
  Descriptions,
  Tag,
  Input,
  Row,
  Col,
  Divider,
  message,
  Spin,
  TreeSelect
} from 'antd';
import {
  FullscreenOutlined,
  DownloadOutlined,
  SettingOutlined,
  SearchOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { Network } from 'vis-network/standalone';
import type { Data, Options, Node, Edge } from 'vis-network/standalone';
import { apiService, Graph, VisualizationData, Category } from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

interface GraphNode extends Node {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
}

interface GraphEdge extends Edge {
  id: string;
  from: string;
  to: string;
  label: string;
  type: string;
  weight?: number;
}

interface GraphStats {
  nodes: number;
  edges: number;
  nodeTypes: Record<string, number>;
  edgeTypes: Record<string, number>;
}

const GraphVisualization: React.FC = () => {
  const networkRef = useRef<HTMLDivElement>(null);
  const networkInstance = useRef<Network | null>(null);
  const [selectedGraph, setSelectedGraph] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('root');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [physics, setPhysics] = useState(true);
  const [nodeSize, setNodeSize] = useState(25);
  const [edgeWidth, setEdgeWidth] = useState(2);
  const [showLabels, setShowLabels] = useState(true);
  const [loading, setLoading] = useState(false);
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [categoryTree, setCategoryTree] = useState<Category | null>(null);
  const [visualizationData, setVisualizationData] = useState<VisualizationData | null>(null);
  const [graphStats, setGraphStats] = useState<GraphStats>({
    nodes: 0,
    edges: 0,
    nodeTypes: {},
    edgeTypes: {}
  });

  // 加载分类树
  const loadCategoryTree = async () => {
    try {
      const tree = await apiService.getCategoryTree();
      setCategoryTree(tree);
    } catch (error) {
      console.error('加载分类树失败:', error);
      message.error('加载分类树失败');
    }
  };

  // 加载图谱列表（根据分类）
  const loadGraphs = async (categoryId: string = 'root') => {
    try {
      const graphList = await apiService.getCategoryGraphs(categoryId);
      setGraphs(graphList);
      // 如果当前选择的图谱不在新的列表中，清空选择
      if (selectedGraph && !graphList.find(g => g.id === selectedGraph)) {
        setSelectedGraph('');
        setVisualizationData(null);
      }
      // 如果没有选择图谱且有可用图谱，选择第一个
      if (!selectedGraph && graphList.length > 0) {
        setSelectedGraph(graphList[0].id);
      }
    } catch (error) {
      console.error('加载图谱列表失败:', error);
      message.error('加载图谱列表失败');
    }
  };

  // 加载可视化数据（根据分类）
  const loadVisualizationData = async (categoryId: string) => {
    if (!categoryId) return;
    
    setLoading(true);
    try {
      const data = await apiService.getCategoryVisualization(categoryId);
      setVisualizationData(data);
      
      // 计算统计信息
      const nodeTypes: Record<string, number> = {};
      const edgeTypes: Record<string, number> = {};
      
      data.nodes.forEach((node) => {
        nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
      });
      
      data.edges.forEach((edge) => {
        const edgeType = edge.label || 'unknown';
        edgeTypes[edgeType] = (edgeTypes[edgeType] || 0) + 1;
      });
      
      setGraphStats({
        nodes: data.nodes.length,
        edges: data.edges.length,
        nodeTypes,
        edgeTypes
      });
      
    } catch (error) {
      console.error('加载可视化数据失败:', error);
      message.error('加载可视化数据失败');
    } finally {
      setLoading(false);
    }
  };

  const initializeNetwork = () => {
    if (!networkRef.current || !visualizationData) return;

    const data = {
      nodes: visualizationData.nodes,
      edges: visualizationData.edges
    };

    const options: Options = {
      nodes: {
        size: nodeSize,
        font: {
          size: showLabels ? 14 : 0,
          color: '#333'
        },
        borderWidth: 2,
        shadow: true
      },
      edges: {
        width: edgeWidth,
        font: {
          size: showLabels ? 12 : 0,
          align: 'middle'
        },
        arrows: {
          to: { enabled: true, scaleFactor: 1 }
        },
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.5
        }
      },
      physics: {
        enabled: physics,
        stabilization: { iterations: 100 }
      },
      interaction: {
        hover: true,
        selectConnectedEdges: false
      },
      layout: {
        improvedLayout: true
      }
    };

    if (networkInstance.current) {
      networkInstance.current.destroy();
    }

    networkInstance.current = new Network(networkRef.current, data, options);

    // 事件监听
    networkInstance.current.on('selectNode', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = visualizationData.nodes.find((n) => n.id === nodeId) as GraphNode;
        if (node) {
          setSelectedNode(node);
          setSelectedEdge(null);
          setDrawerVisible(true);
        }
      }
    });

    networkInstance.current.on('selectEdge', (params) => {
      if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edge = visualizationData.edges.find((e) => e.id === edgeId) as GraphEdge;
        if (edge) {
          setSelectedEdge(edge);
          setSelectedNode(null);
          setDrawerVisible(true);
        }
      }
    });

    networkInstance.current.on('deselectNode', () => {
      setSelectedNode(null);
    });

    networkInstance.current.on('deselectEdge', () => {
      setSelectedEdge(null);
    });
  };

  // 将分类树转换为TreeSelect数据格式
  const convertCategoryToTreeData = (category: Category): any => {
    return {
      title: category.name,
      value: category.id,
      key: category.id,
      children: category.children?.map(child => convertCategoryToTreeData(child)) || []
    };
  };

  // 处理分类选择变化
  const handleCategoryChange = (categoryId: string) => {
    setSelectedCategory(categoryId);
    loadGraphs(categoryId);
    loadVisualizationData(categoryId);
  };

  useEffect(() => {
    loadCategoryTree();
    loadGraphs('root');
    loadVisualizationData('root');
    return () => {
      if (networkInstance.current) {
        networkInstance.current.destroy();
      }
    };
  }, []);

  // 移除这个useEffect，因为分类变化已经在handleCategoryChange中处理

  // 移除基于selectedGraph的useEffect，现在直接基于分类加载数据

  useEffect(() => {
    if (visualizationData) {
      initializeNetwork();
    }
  }, [visualizationData]);

  useEffect(() => {
    if (networkInstance.current) {
      networkInstance.current.setOptions({
        nodes: {
          size: nodeSize,
          font: { size: showLabels ? 14 : 0 }
        },
        edges: {
          width: edgeWidth,
          font: { size: showLabels ? 12 : 0 }
        },
        physics: { enabled: physics }
      });
    }
  }, [nodeSize, edgeWidth, showLabels, physics]);

  const handleSearch = () => {
    if (!networkInstance.current || !searchText || !visualizationData) return;
    
    const matchedNodes = visualizationData.nodes.filter((node) => 
      node.label.toLowerCase().includes(searchText.toLowerCase())
    );
    
    if (matchedNodes.length > 0) {
      const nodeIds = matchedNodes.map((node) => node.id);
      networkInstance.current.selectNodes(nodeIds);
      networkInstance.current.focus(nodeIds[0], {
        scale: 1.5,
        animation: true
      });
      message.success(`找到 ${matchedNodes.length} 个匹配的节点`);
    } else {
      message.warning('未找到匹配的节点');
    }
  };

  const handleZoomIn = () => {
    if (networkInstance.current) {
      const scale = networkInstance.current.getScale();
      networkInstance.current.moveTo({ scale: scale * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkInstance.current) {
      const scale = networkInstance.current.getScale();
      networkInstance.current.moveTo({ scale: scale * 0.8 });
    }
  };

  const handleReset = () => {
    if (networkInstance.current) {
      networkInstance.current.fit();
    }
  };

  const handleRefresh = () => {
    if (selectedGraph) {
      loadVisualizationData(selectedGraph);
    }
  };

  const handleExport = () => {
    if (networkInstance.current) {
      try {
        // 使用vis-network的导出功能
        const canvas = document.querySelector('#network-container canvas') as HTMLCanvasElement;
        if (canvas) {
          const dataURL = canvas.toDataURL('image/png');
          const link = document.createElement('a');
          link.download = `knowledge-graph-${selectedGraph}.png`;
          link.href = dataURL;
          link.click();
          message.success('图片导出成功！');
        }
      } catch (error) {
        console.error('导出失败:', error);
        message.error('导出失败，请重试');
      }
    }
  };

  const handleFullscreen = () => {
    const container = document.getElementById('network-container');
    if (!container) return;

    try {
      if (!document.fullscreenElement) {
        // 进入全屏
        if (container.requestFullscreen) {
          container.requestFullscreen();
        } else if ((container as any).webkitRequestFullscreen) {
          (container as any).webkitRequestFullscreen();
        } else if ((container as any).mozRequestFullScreen) {
          (container as any).mozRequestFullScreen();
        } else if ((container as any).msRequestFullscreen) {
          (container as any).msRequestFullscreen();
        }
        message.success('已进入全屏模式，按ESC键退出');
      } else {
        // 退出全屏
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if ((document as any).webkitExitFullscreen) {
          (document as any).webkitExitFullscreen();
        } else if ((document as any).mozCancelFullScreen) {
          (document as any).mozCancelFullScreen();
        } else if ((document as any).msExitFullscreen) {
          (document as any).msExitFullscreen();
        }
      }
    } catch (error) {
      console.error('全屏操作失败:', error);
      message.error('全屏功能不支持或操作失败');
    }
  };

  const getNodeTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      concept: '#1890ff',
      algorithm: '#52c41a',
      model: '#fa8c16',
      field: '#722ed1'
    };
    return colors[type] || '#666';
  };

  const getNodeTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      concept: '概念',
      algorithm: '算法',
      model: '模型',
      field: '领域'
    };
    return labels[type] || type;
  };

  const getEdgeTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      contains: '包含',
      based_on: '基于',
      implements: '实现',
      applied_to: '应用于',
      used_for: '用于'
    };
    return labels[type] || type;
  };

  return (
    <div>
      <div className="page-header">
        <Title level={2} className="page-title">🎨 图谱可视化</Title>
        <Paragraph className="page-description">
          交互式知识图谱可视化，支持节点搜索、缩放、导出等功能。
        </Paragraph>
      </div>

      {/* 控制面板 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <TreeSelect
                style={{ width: '100%' }}
                placeholder="请选择分类"
                value={selectedCategory}
                onChange={handleCategoryChange}
                treeData={categoryTree ? [convertCategoryToTreeData(categoryTree)] : []}
                showSearch
                treeDefaultExpandAll
                allowClear={false}
              />

            </Space>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <Input.Search
              placeholder="搜索节点"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          
          <Col xs={24} md={10}>
            <Space wrap>
              <Tooltip title="放大">
                <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
              </Tooltip>
              <Tooltip title="缩小">
                <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
              </Tooltip>
              <Tooltip title="重置视图">
                <Button icon={<ReloadOutlined />} onClick={handleReset} />
              </Tooltip>
              <Tooltip title="刷新数据">
                <Button icon={<ReloadOutlined />} onClick={handleRefresh} loading={loading} />
              </Tooltip>
              <Tooltip title="全屏">
                <Button icon={<FullscreenOutlined />} onClick={handleFullscreen} />
              </Tooltip>
              <Tooltip title="导出图片">
                <Button icon={<DownloadOutlined />} onClick={handleExport} />
              </Tooltip>
              <Tooltip title="显示信息">
                <Button 
                  icon={<InfoCircleOutlined />} 
                  onClick={() => setDrawerVisible(true)}
                />
              </Tooltip>
            </Space>
          </Col>
        </Row>
       </Card>

      {/* 可视化区域 */}
      <Card>
        <Spin spinning={loading} tip="加载图谱数据中...">
          <Row gutter={16}>
            <Col xs={24} lg={18}>
              <div 
                ref={networkRef} 
                id="network-container"
                className="graph-container"
                style={{ height: '600px', border: '1px solid #d9d9d9', borderRadius: '8px' }}
              />
            </Col>
          
          <Col xs={24} lg={6}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {/* 统计信息 */}
              <Card size="small" title="📊 图谱统计">
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="节点数">{graphStats.nodes}</Descriptions.Item>
                  <Descriptions.Item label="边数">{graphStats.edges}</Descriptions.Item>
                </Descriptions>
                
                <Divider style={{ margin: '12px 0' }} />
                
                <div style={{ marginBottom: 8 }}>
                  <Text strong>节点类型:</Text>
                </div>
                {Object.entries(graphStats.nodeTypes).map(([type, count]) => (
                  <div key={type} style={{ marginBottom: 4 }}>
                    <Tag color={getNodeTypeColor(type)}>
                      {getNodeTypeLabel(type)}: {count}
                    </Tag>
                  </div>
                ))}
              </Card>
              

            </Space>
          </Col>
        </Row>
        </Spin>
      </Card>

      {/* 详情抽屉 */}
      <Drawer
        title={selectedNode ? '节点详情' : selectedEdge ? '关系详情' : '图谱信息'}
        placement="right"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={400}
      >
        {selectedNode && (
          <div>
            <Descriptions column={1}>
              <Descriptions.Item label="名称">{selectedNode?.label}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={getNodeTypeColor(selectedNode?.type || '')}>
                  {getNodeTypeLabel(selectedNode?.type || '')}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="ID">{selectedNode?.id}</Descriptions.Item>
            </Descriptions>
            
            {selectedNode?.properties && Object.keys(selectedNode.properties).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>属性:</Text>
                <div style={{ marginTop: 8 }}>
                  {Object.entries(selectedNode.properties || {}).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: 4 }}>
                      <Text code>{key}:</Text> {String(value)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {selectedEdge && (
          <div>
            <Descriptions column={1}>
              <Descriptions.Item label="关系">{selectedEdge?.label}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag>{getEdgeTypeLabel(selectedEdge?.type || '')}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="源节点">{selectedEdge?.from}</Descriptions.Item>
              <Descriptions.Item label="目标节点">{selectedEdge?.to}</Descriptions.Item>
              {selectedEdge?.weight && (
                <Descriptions.Item label="权重">{selectedEdge.weight}</Descriptions.Item>
              )}
            </Descriptions>
          </div>
        )}
        
        {!selectedNode && !selectedEdge && (
          <div>
            <Title level={4}>图谱概览</Title>
            <Descriptions column={1}>
              <Descriptions.Item label="节点总数">{graphStats.nodes}</Descriptions.Item>
              <Descriptions.Item label="边总数">{graphStats.edges}</Descriptions.Item>
            </Descriptions>
            
            <Divider />
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>节点类型分布:</Text>
              {Object.entries(graphStats.nodeTypes).map(([type, count]) => (
                <div key={type} style={{ marginTop: 8 }}>
                  <Tag color={getNodeTypeColor(type)}>
                    {getNodeTypeLabel(type)}: {count}
                  </Tag>
                </div>
              ))}
            </div>
            
            <div>
              <Text strong>关系类型分布:</Text>
              {Object.entries(graphStats.edgeTypes).map(([type, count]) => (
                <div key={type} style={{ marginTop: 8 }}>
                  <Tag>{getEdgeTypeLabel(type)}: {count}</Tag>
                </div>
              ))}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default GraphVisualization;