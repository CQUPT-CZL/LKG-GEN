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
  message
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
  const [selectedGraph, setSelectedGraph] = useState<string>('1');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [physics, setPhysics] = useState(true);
  const [nodeSize, setNodeSize] = useState(25);
  const [edgeWidth, setEdgeWidth] = useState(2);
  const [showLabels, setShowLabels] = useState(true);
  const [graphStats, setGraphStats] = useState<GraphStats>({
    nodes: 0,
    edges: 0,
    nodeTypes: {},
    edgeTypes: {}
  });

  // 模拟图谱数据
  const generateMockData = (): Data => {
    const nodes: GraphNode[] = [
      { id: '1', label: '人工智能', type: 'concept', color: '#1890ff' },
      { id: '2', label: '机器学习', type: 'concept', color: '#1890ff' },
      { id: '3', label: '深度学习', type: 'concept', color: '#1890ff' },
      { id: '4', label: '神经网络', type: 'concept', color: '#1890ff' },
      { id: '5', label: 'CNN', type: 'algorithm', color: '#52c41a' },
      { id: '6', label: 'RNN', type: 'algorithm', color: '#52c41a' },
      { id: '7', label: 'Transformer', type: 'algorithm', color: '#52c41a' },
      { id: '8', label: 'BERT', type: 'model', color: '#fa8c16' },
      { id: '9', label: 'GPT', type: 'model', color: '#fa8c16' },
      { id: '10', label: '自然语言处理', type: 'field', color: '#722ed1' },
      { id: '11', label: '计算机视觉', type: 'field', color: '#722ed1' },
      { id: '12', label: '语音识别', type: 'field', color: '#722ed1' }
    ];

    const edges: GraphEdge[] = [
      { id: 'e1', from: '1', to: '2', label: '包含', type: 'contains' },
      { id: 'e2', from: '2', to: '3', label: '包含', type: 'contains' },
      { id: 'e3', from: '3', to: '4', label: '基于', type: 'based_on' },
      { id: 'e4', from: '4', to: '5', label: '实现', type: 'implements' },
      { id: 'e5', from: '4', to: '6', label: '实现', type: 'implements' },
      { id: 'e6', from: '4', to: '7', label: '实现', type: 'implements' },
      { id: 'e7', from: '7', to: '8', label: '应用于', type: 'applied_to' },
      { id: 'e8', from: '7', to: '9', label: '应用于', type: 'applied_to' },
      { id: 'e9', from: '8', to: '10', label: '用于', type: 'used_for' },
      { id: 'e10', from: '9', to: '10', label: '用于', type: 'used_for' },
      { id: 'e11', from: '5', to: '11', label: '用于', type: 'used_for' },
      { id: 'e12', from: '6', to: '12', label: '用于', type: 'used_for' }
    ];

    return { nodes, edges };
  };

  const initializeNetwork = () => {
    if (!networkRef.current) return;

    const data = generateMockData();
    
    // 计算统计信息
    const nodeTypes: Record<string, number> = {};
    const edgeTypes: Record<string, number> = {};
    
    if (data.nodes) {
      const nodes = Array.isArray(data.nodes) ? data.nodes : data.nodes.get();
      nodes.forEach((node: any) => {
        nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
      });
    }
    
    if (data.edges) {
      const edges = Array.isArray(data.edges) ? data.edges : data.edges.get();
      edges.forEach((edge: any) => {
        edgeTypes[edge.type] = (edgeTypes[edge.type] || 0) + 1;
      });
    }
    
    setGraphStats({
      nodes: data.nodes ? (Array.isArray(data.nodes) ? data.nodes.length : data.nodes.length) : 0,
      edges: data.edges ? (Array.isArray(data.edges) ? data.edges.length : data.edges.length) : 0,
      nodeTypes,
      edgeTypes
    });

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
        if (data.nodes) {
          const nodes = Array.isArray(data.nodes) ? data.nodes : data.nodes.get();
          const node = nodes.find((n: any) => n.id === nodeId) as GraphNode;
          if (node) {
            setSelectedNode(node);
            setSelectedEdge(null);
            setDrawerVisible(true);
          }
        }
      }
    });

    networkInstance.current.on('selectEdge', (params) => {
      if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        if (data.edges) {
          const edges = Array.isArray(data.edges) ? data.edges : data.edges.get();
          const edge = edges.find((e: any) => e.id === edgeId) as GraphEdge;
          if (edge) {
            setSelectedEdge(edge);
            setSelectedNode(null);
            setDrawerVisible(true);
          }
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

  useEffect(() => {
    initializeNetwork();
    return () => {
      if (networkInstance.current) {
        networkInstance.current.destroy();
      }
    };
  }, [selectedGraph]);

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
    if (!networkInstance.current || !searchText) return;
    
    const data = generateMockData();
    if (!data.nodes) return;
    
    const nodes = Array.isArray(data.nodes) ? data.nodes : data.nodes.get();
    const matchedNodes = nodes.filter((node: any) => 
      node.label.toLowerCase().includes(searchText.toLowerCase())
    );
    
    if (matchedNodes.length > 0) {
      const nodeIds = matchedNodes.map((node: any) => node.id);
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
          message.success('图谱已导出为图片');
        } else {
          message.error('无法获取画布，导出失败');
        }
      } catch (error) {
        message.error('导出失败');
      }
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
            <Space>
              <Text strong>选择图谱:</Text>
              <Select
                value={selectedGraph}
                onChange={setSelectedGraph}
                style={{ width: 150 }}
              >
                <Option value="1">AI技术图谱</Option>
                <Option value="2">医学文献图谱</Option>
                <Option value="3">法律条文图谱</Option>
              </Select>
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
              <Tooltip title="全屏">
                <Button icon={<FullscreenOutlined />} />
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
              
              {/* 控制选项 */}
              <Card size="small" title="⚙️ 显示设置">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>物理引擎:</Text>
                    <Switch 
                      checked={physics} 
                      onChange={setPhysics} 
                      style={{ marginLeft: 8 }}
                    />
                  </div>
                  
                  <div>
                    <Text>显示标签:</Text>
                    <Switch 
                      checked={showLabels} 
                      onChange={setShowLabels} 
                      style={{ marginLeft: 8 }}
                    />
                  </div>
                  
                  <div>
                    <Text>节点大小:</Text>
                    <Slider
                      min={10}
                      max={50}
                      value={nodeSize}
                      onChange={setNodeSize}
                      style={{ marginTop: 8 }}
                    />
                  </div>
                  
                  <div>
                    <Text>边宽度:</Text>
                    <Slider
                      min={1}
                      max={5}
                      value={edgeWidth}
                      onChange={setEdgeWidth}
                      style={{ marginTop: 8 }}
                    />
                  </div>
                </Space>
              </Card>
            </Space>
          </Col>
        </Row>
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
              <Descriptions.Item label="名称">{selectedNode.label}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={getNodeTypeColor(selectedNode.type)}>
                  {getNodeTypeLabel(selectedNode.type)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="ID">{selectedNode.id}</Descriptions.Item>
            </Descriptions>
            
            {selectedNode.properties && (
              <div style={{ marginTop: 16 }}>
                <Text strong>属性:</Text>
                <div style={{ marginTop: 8 }}>
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
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
              <Descriptions.Item label="关系">{selectedEdge.label}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag>{getEdgeTypeLabel(selectedEdge.type)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="源节点">{selectedEdge.from}</Descriptions.Item>
              <Descriptions.Item label="目标节点">{selectedEdge.to}</Descriptions.Item>
              {selectedEdge.weight && (
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