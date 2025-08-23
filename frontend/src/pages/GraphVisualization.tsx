import React, { useState, useEffect, useRef, useMemo } from 'react';
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
import { apiService, Graph, Subgraph, Entity, Relationship, SourceResource, Category } from '../services/api';

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

// 新增：分类树节点类型定义
type CategoryTreeNode = { title: string; value: string; key: string; children?: CategoryTreeNode[] };

const GraphVisualization: React.FC = () => {
  const [graphs, setGraphs] = useState<Graph[]>([]);
  const [documents, setDocuments] = useState<SourceResource[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedGraph, setSelectedGraph] = useState<Graph | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<SourceResource | null>(null);
  const [subgraph, setSubgraph] = useState<Subgraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [networkData, setNetworkData] = useState<Data>({ nodes: [], edges: [] });
  const [stats, setStats] = useState<GraphStats>({ nodes: 0, edges: 0, nodeTypes: {}, edgeTypes: {} });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [nodeSize, setNodeSize] = useState(25);
  const [edgeWidth, setEdgeWidth] = useState(2);
  const [showLabels, setShowLabels] = useState(true);
  const [physics, setPhysics] = useState(true);
  const networkRef = useRef<HTMLDivElement>(null);
  const networkInstance = useRef<Network | null>(null);

  // 新增：根据分类列表构建树形结构（支持多级分类）
  const categoryTree: CategoryTreeNode[] = useMemo(() => {
    if (!selectedGraph) return [];
    const nodeMap = new Map<string, CategoryTreeNode>();
    categories.forEach(cat => {
      nodeMap.set(cat.id, { title: cat.name, value: cat.id, key: cat.id, children: [] });
    });
    const roots: CategoryTreeNode[] = [];
    categories.forEach(cat => {
      const node = nodeMap.get(cat.id)!;
      if (cat.parent_id === selectedGraph.id) {
        roots.push(node);
      } else if (cat.parent_id && nodeMap.has(cat.parent_id)) {
        nodeMap.get(cat.parent_id)!.children!.push(node);
      } else {
        roots.push(node);
      }
    });
    return roots;
  }, [categories, selectedGraph]);

  useEffect(() => {
    loadGraphs();
  }, []);

  useEffect(() => {
    if (selectedGraph) {
      loadCategories();
      setSelectedCategory(null);
      setSelectedDocument(null);
      loadDocuments();
      // 同时加载图谱级子图谱，便于直接查看整图 🔎
      loadGraphSubgraph();
    }
  }, [selectedGraph]);

  useEffect(() => {
    // 选择分类后：加载该分类子图谱，并按分类过滤文档
    if (!selectedGraph) return;
    if (selectedCategory) {
      loadCategorySubgraph();
      loadDocuments();
    } else {
      // 清空分类时，回到整图
      loadGraphSubgraph();
      loadDocuments();
    }
  }, [selectedCategory]);
  useEffect(() => {
     if (selectedDocument) {
       loadDocumentSubgraph();
     }
   }, [selectedDocument]);

  useEffect(() => {
    if (subgraph) {
      buildNetworkData();
    }
  }, [subgraph]);

  useEffect(() => {
    if (networkData.nodes && networkData.nodes.length > 0 && networkRef.current) {
      initializeNetwork();
    }
  }, [networkData, nodeSize, edgeWidth, showLabels, physics]);

  const loadGraphs = async () => {
    try {
      const graphsData = await apiService.getGraphs();
      setGraphs(graphsData);
    } catch (error) {
      console.error('加载图谱失败:', error);
      message.error('加载图谱失败');
    }
  };

  const loadCategories = async () => {
    if (!selectedGraph) return;
    try {
      const list = await apiService.getGraphCategories(selectedGraph.id);
      setCategories(list);
    } catch (error) {
      console.error('加载分类失败:', error);
      message.error('加载分类失败');
    }
  };

  const loadDocuments = async () => {
    try {
      let documentsData: SourceResource[] = [];
      if (selectedCategory) {
        documentsData = await apiService.getCategoryDocuments(selectedCategory.id);
      } else if (selectedGraph) {
        documentsData = await apiService.getGraphDocuments(selectedGraph.id);
      } else {
        documentsData = await apiService.getDocuments();
      }
      setDocuments(documentsData);
    } catch (error) {
      console.error('加载文档失败:', error);
      message.error('加载文档失败');
    }
  };

  const loadDocumentSubgraph = async () => {
    if (!selectedDocument) return;
    
    setLoading(true);
    try {
      const subgraphData = await apiService.getDocumentSubgraph(selectedDocument.id);
      setSubgraph(subgraphData);
    } catch (error) {
      console.error('加载文档子图谱失败:', error);
      message.error('加载文档子图谱失败');
    } finally {
      setLoading(false);
    }
  };

  // 新增：加载图谱级子图谱（整张图）
  const loadGraphSubgraph = async () => {
    if (!selectedGraph) return;

    setLoading(true);
    try {
      const subgraphData = await apiService.getGraphSubgraph(selectedGraph.id);
      setSubgraph(subgraphData);
    } catch (error) {
      console.error('加载图谱子图谱失败:', error);
      message.error('加载图谱子图谱失败');
    } finally {
      setLoading(false);
    }
  };

  // 新增：加载分类级子图谱
  const loadCategorySubgraph = async () => {
    if (!selectedCategory) return;
    setLoading(true);
    try {
      const subgraphData = await apiService.getCategorySubgraph(selectedCategory.id);
      setSubgraph(subgraphData);
    } catch (error) {
      console.error('加载分类子图谱失败:', error);
      message.error('加载分类子图谱失败');
    } finally {
      setLoading(false);
    }
  };

  const buildNetworkData = () => {
    if (!subgraph) return;

    const nodes: GraphNode[] = subgraph.entities.map(entity => {
      const nodeType: string = (entity.type as string) || (entity.properties?.entity_type as string) || 'Unknown';
      return {
        id: entity.id.toString(),
        label: entity.name,
        type: nodeType,
        properties: entity.properties,
        color: getNodeColor(nodeType),
        size: nodeSize,
        font: { size: showLabels ? 14 : 0 }
      } as GraphNode;
    });

    const edges: GraphEdge[] = subgraph.relationships.map(rel => {
      const anyRel: any = rel as any;
      const fromId = (anyRel.source_entity_id ?? anyRel.start_node_id ?? '').toString();
      const toId = (anyRel.target_entity_id ?? anyRel.end_node_id ?? '').toString();
      const relType = (anyRel.relation_type ?? anyRel.type ?? '') as string;
      return {
        id: (anyRel.id ?? '').toString(),
        from: fromId,
        to: toId,
        label: relType,
        type: relType,
        width: edgeWidth,
        arrows: 'to'
      } as GraphEdge;
    });

    setNetworkData({ nodes, edges });
    calculateStats(nodes, edges);
  };

  const getNodeColor = (type: string): string => {
    const colors: Record<string, string> = {
      'Person': '#ff7875',
      'Organization': '#40a9ff',
      'Location': '#73d13d',
      'Event': '#ffb347',
      'Concept': '#b37feb',
      'Product': '#ffc069',
      'Technology': '#36cfc9'
    };
    return colors[type] || '#d9d9d9';
  };

  const calculateStats = (nodes: GraphNode[], edges: GraphEdge[]) => {
    const nodeTypes: Record<string, number> = {};
    const edgeTypes: Record<string, number> = {};

    nodes.forEach(node => {
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
    });

    edges.forEach(edge => {
      edgeTypes[edge.type] = (edgeTypes[edge.type] || 0) + 1;
    });

    setStats({
      nodes: nodes.length,
      edges: edges.length,
      nodeTypes,
      edgeTypes
    });
  };

  const initializeNetwork = () => {
    if (!networkRef.current) return;

    const options: Options = {
      nodes: {
        shape: 'dot',
        size: nodeSize,
        font: {
          size: showLabels ? 14 : 0,
          color: '#343434'
        },
        borderWidth: 2,
        shadow: true
      },
      edges: {
        width: edgeWidth,
        color: { inherit: 'from' },
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.5
        },
        arrows: {
          to: { enabled: true, scaleFactor: 1 }
        },
        font: {
          size: showLabels ? 12 : 0,
          align: 'middle'
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

    networkInstance.current = new Network(networkRef.current, networkData, options);

    // 添加事件监听器
    networkInstance.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodes = networkData.nodes as GraphNode[];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          setSelectedNode(node);
          setSelectedEdge(null);
          setDrawerVisible(true);
        }
      } else if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edges = networkData.edges as GraphEdge[];
        const edge = edges.find(e => e.id === edgeId);
        if (edge) {
          setSelectedEdge(edge);
          setSelectedNode(null);
          setDrawerVisible(true);
        }
      }
    });
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    if (networkInstance.current && value && networkData.nodes) {
      const nodes = networkData.nodes as GraphNode[];
      const matchingNodes = nodes.filter((node: GraphNode) => 
        node.label?.toLowerCase().includes(value.toLowerCase())
      );
      
      if (matchingNodes.length > 0) {
        const nodeIds = matchingNodes.map((node: GraphNode) => node.id);
        networkInstance.current.selectNodes(nodeIds);
        networkInstance.current.focus(nodeIds[0], {
          scale: 1.5,
          animation: true
        });
      }
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

  const handleDownload = () => {
    if (networkInstance.current && networkRef.current) {
      const canvas = networkRef.current.querySelector('canvas');
      if (canvas) {
        const link = document.createElement('a');
        link.download = `graph-${selectedGraph?.name || 'visualization'}.png`;
        link.href = canvas.toDataURL();
        link.click();
      }
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={<Title level={3}>🔍 图谱可视化</Title>}
            extra={
              <Space>
                <Select
                  placeholder="选择图谱"
                  style={{ width: 200 }}
                  value={selectedGraph?.id}
                  onChange={(value) => {
                    const graph = graphs.find(g => g.id === value);
                    setSelectedGraph(graph || null);
                    setSelectedDocument(null);
                    setSubgraph(null);
                  }}
                >
                  {graphs.map(graph => (
                    <Option key={graph.id} value={graph.id}>
                      {graph.name}
                    </Option>
                  ))}
                </Select>
                {selectedGraph && (
                  <TreeSelect
                    allowClear
                    placeholder="选择分类（可选，支持多级）"
                    style={{ width: 260 }}
                    dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
                    treeData={categoryTree as any}
                    value={selectedCategory?.id}
                    treeDefaultExpandAll
                    onChange={(value) => {
                      const cat = categories.find(c => c.id === value) || null;
                      setSelectedCategory(cat);
                      setSelectedDocument(null);
                    }}
                    onClear={() => {
                      setSelectedCategory(null);
                      setSelectedDocument(null);
                    }}
                  />
                )}
                 {selectedGraph && (
                   <Select
                     placeholder="选择文档"
                     style={{ width: 200 }}
                     value={selectedDocument?.id}
                     onChange={(value) => {
                       const doc = documents.find(d => d.id === value);
                       setSelectedDocument(doc || null);
                     }}
                   >
                     {documents.map(doc => (
                       <Option key={doc.id} value={doc.id}>
                         {doc.filename}
                       </Option>
                     ))}
                   </Select>
                 )}

                {selectedGraph && !selectedCategory && (
                  <Button type="primary" onClick={loadGraphSubgraph} icon={<SearchOutlined />}>加载图谱子图谱</Button>
                )}
                {selectedGraph && selectedCategory && (
                  <Button type="primary" onClick={loadCategorySubgraph} icon={<SearchOutlined />}>加载分类子图谱</Button>
                )}
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={18}>
                <Card
                  size="small"
                  title="图谱视图"
                  extra={
                    <Space>
                      <Input.Search
                        placeholder="搜索节点"
                        style={{ width: 200 }}
                        onSearch={handleSearch}
                        prefix={<SearchOutlined />}
                      />
                      <Tooltip title="放大">
                        <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
                      </Tooltip>
                      <Tooltip title="缩小">
                        <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
                      </Tooltip>
                      <Tooltip title="重置视图">
                        <Button icon={<ReloadOutlined />} onClick={handleReset} />
                      </Tooltip>
                      <Tooltip title="下载图片">
                        <Button icon={<DownloadOutlined />} onClick={handleDownload} />
                      </Tooltip>
                      <Tooltip title="设置">
                        <Button icon={<SettingOutlined />} onClick={() => setDrawerVisible(true)} />
                      </Tooltip>
                    </Space>
                  }
                >
                  <Spin spinning={loading}>
                    <div
                      ref={networkRef}
                      style={{
                        width: '100%',
                        height: '600px',
                        border: '1px solid #d9d9d9',
                        borderRadius: '6px'
                      }}
                    />
                  </Spin>
                </Card>
              </Col>
              
              <Col span={6}>
                <Card size="small" title="图谱统计">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="节点数量">
                      <Text strong>{stats.nodes}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="边数量">
                      <Text strong>{stats.edges}</Text>
                    </Descriptions.Item>
                  </Descriptions>
                  
                  <Divider style={{ margin: '12px 0' }} />
                  
                  <div style={{ marginBottom: 16 }}>
                    <Text strong>节点类型分布</Text>
                    <div style={{ marginTop: 8 }}>
                      {Object.entries(stats.nodeTypes).map(([type, count]) => (
                        <Tag key={type} color={getNodeColor(type)} style={{ marginBottom: 4 }}>
                          {type}: {count}
                        </Tag>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <Text strong>关系类型分布</Text>
                    <div style={{ marginTop: 8 }}>
                      {Object.entries(stats.edgeTypes).map(([type, count]) => (
                        <Tag key={type} style={{ marginBottom: 4 }}>
                          {type}: {count}
                        </Tag>
                      ))}
                    </div>
                  </div>
                </Card>
                
                <Card size="small" title="视图控制" style={{ marginTop: 16 }}>
                  <div style={{ marginBottom: 16 }}>
                    <Text>节点大小</Text>
                    <Slider
                      min={10}
                      max={50}
                      value={nodeSize}
                      onChange={setNodeSize}
                      style={{ marginTop: 8 }}
                    />
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <Text>边宽度</Text>
                    <Slider
                      min={1}
                      max={5}
                      value={edgeWidth}
                      onChange={setEdgeWidth}
                      style={{ marginTop: 8 }}
                    />
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <Space>
                      <Text>显示标签</Text>
                      <Switch checked={showLabels} onChange={setShowLabels} />
                    </Space>
                  </div>
                  
                  <div>
                    <Space>
                      <Text>物理引擎</Text>
                      <Switch checked={physics} onChange={setPhysics} />
                    </Space>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Drawer
        title={selectedNode ? '节点详情' : '关系详情'}
        placement="right"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={400}
      >
        {selectedNode && (
          <div>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="ID">{selectedNode.id}</Descriptions.Item>
              <Descriptions.Item label="名称">{selectedNode.label}</Descriptions.Item>
              <Descriptions.Item label="类型">
                <Tag color={getNodeColor(selectedNode.type)}>{selectedNode.type}</Tag>
              </Descriptions.Item>
            </Descriptions>
            
            {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>属性信息</Text>
                <Descriptions column={1} bordered size="small" style={{ marginTop: 8 }}>
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
                    <Descriptions.Item key={key} label={key}>
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </div>
            )}
          </div>
        )}
        
        {selectedEdge && (
          <div>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="ID">{selectedEdge.id}</Descriptions.Item>
              <Descriptions.Item label="类型">{selectedEdge.type}</Descriptions.Item>
              <Descriptions.Item label="源节点">{selectedEdge.from}</Descriptions.Item>
              <Descriptions.Item label="目标节点">{selectedEdge.to}</Descriptions.Item>
              {selectedEdge.weight && (
                <Descriptions.Item label="权重">{selectedEdge.weight}</Descriptions.Item>
              )}
            </Descriptions>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default GraphVisualization;