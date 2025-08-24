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
  description?: string;
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

// --- 新增辅助函数 ---

// 获取与背景色对比度高的文本颜色
const getContrastingTextColor = (bgColor: string): string => {
  const color = bgColor.startsWith('hsl') ? hslToRgb(bgColor) : hexToRgb(bgColor);
  if (!color) return '#ffffff'; // 默认白色

  // 计算亮度 (YIQ)
  const luminance = (color.r * 299 + color.g * 587 + color.b * 114) / 1000;
  return luminance >= 128 ? '#000000' : '#ffffff';
};

// HSL颜色转RGB
const hslToRgb = (hsl: string): { r: number; g: number; b: number } | null => {
  const match = /hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/.exec(hsl);
  if (!match) return null;

  let h = parseInt(match[1], 10);
  let s = parseInt(match[2], 10) / 100;
  let l = parseInt(match[3], 10) / 100;

  let c = (1 - Math.abs(2 * l - 1)) * s,
      x = c * (1 - Math.abs((h / 60) % 2 - 1)),
      m = l - c/2,
      r = 0,
      g = 0,
      b = 0;

  if (0 <= h && h < 60) {
    r = c; g = x; b = 0;
  } else if (60 <= h && h < 120) {
    r = x; g = c; b = 0;
  } else if (120 <= h && h < 180) {
    r = 0; g = c; b = x;
  } else if (180 <= h && h < 240) {
    r = 0; g = x; b = c;
  } else if (240 <= h && h < 300) {
    r = x; g = 0; b = c;
  } else if (300 <= h && h < 360) {
    r = c; g = 0; b = x;
  }
  r = Math.round((r + m) * 255);
  g = Math.round((g + m) * 255);
  b = Math.round((b + m) * 255);

  return { r, g, b };
}

// Hex颜色转RGB
const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

// 增加颜色亮度
const lightenColor = (color: string, percent: number): string => {
  const rgb = color.startsWith('hsl') ? hslToRgb(color) : hexToRgb(color);
  if (!rgb) return color;

  const amount = Math.round(2.55 * percent * 100);
  
  const r = Math.min(255, rgb.r + amount);
  const g = Math.min(255, rgb.g + amount);
  const b = Math.min(255, rgb.b + amount);

  return `rgb(${r}, ${g}, ${b})`;
}


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
      const nodeColor = getNodeColor(nodeType);
      const fontColor = getContrastingTextColor(nodeColor);

      return {
        id: entity.id.toString(),
        label: entity.name,
        type: nodeType,
        properties: entity.properties,
        color: {
          background: nodeColor,
          border: '#2B7CE9',
          highlight: {
            background: lightenColor(nodeColor, 0.2),
            border: '#FFC107'
          },
          hover: {
            background: lightenColor(nodeColor, 0.1),
            border: '#FFC107'
          }
        },
        font: {
          color: fontColor,
          size: 14,
          strokeWidth: 0.5,
          strokeColor: fontColor === '#ffffff' ? '#000000' : '#ffffff'
        },
        size: nodeSize
      } as GraphNode;
    });

    const edges: GraphEdge[] = subgraph.relationships.map(rel => {
      const anyRel: any = rel as any;
      const fromId = (anyRel.source_entity_id ?? anyRel.start_node_id ?? '').toString();
      const toId = (anyRel.target_entity_id ?? anyRel.end_node_id ?? '').toString();
      const relType = (anyRel.relation_type ?? anyRel.type ?? '') as string;
      const description = anyRel.description || '';
      
      console.log('Edge data:', { id: anyRel.id, relType, description, anyRel });
      
      const titleText = description ? `关系类型: ${relType}\n描述: ${description}` : `关系类型: ${relType}`;
      
      return {
        id: (anyRel.id ?? '').toString(),
        from: fromId,
        to: toId,
        label: relType,
        type: relType,
        description: description,
        title: titleText, // 添加悬浮提示
        width: edgeWidth,
        arrows: 'to'
      } as GraphEdge;
    });

    setNetworkData({ nodes, edges });
    calculateStats(nodes, edges);
  };

  // 动态生成节点颜色的函数
  const getNodeColor = (type: string): string => {
    // 预定义一些常见类型的颜色
    const predefinedColors: Record<string, string> = {
      'Person': '#ff7875',
      'Organization': '#40a9ff',
      'Location': '#73d13d',
      'Event': '#ffb347',
      'Concept': '#b37feb',
      'Product': '#ffc069',
      'Technology': '#36cfc9',
      '人物': '#ff7875',
      '组织': '#40a9ff',
      '地点': '#73d13d',
      '事件': '#ffb347',
      '概念': '#b37feb',
      '产品': '#ffc069',
      '技术': '#36cfc9'
    };
    
    // 如果有预定义颜色，直接返回
    if (predefinedColors[type]) {
      return predefinedColors[type];
    }
    
    // 动态生成颜色：使用字符串哈希生成HSL颜色
    const hashCode = (str: string): number => {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // 转换为32位整数
      }
      return Math.abs(hash);
    };
    
    const hash = hashCode(type);
    const hue = hash % 360; // 色相：0-359
    const saturation = 60 + (hash % 30); // 饱和度：60-89
    const lightness = 50 + (hash % 20); // 亮度：50-69
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
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
    if (!networkRef.current || !networkData) return;

    const options: Options = {
      nodes: {
        shape: 'dot',
        size: nodeSize,
        font: {
          size: showLabels ? 14 : 0,
          face: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"'
        },
        borderWidth: 2,
        borderWidthSelected: 4,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.2)',
          size: 7,
          x: 3,
          y: 3
        },
      },
      edges: {
        width: edgeWidth,
        color: { 
          color: '#cccccc',
          highlight: '#FFC107',
          hover: '#e0e0e0',
          inherit: false
        },
        smooth: {
          enabled: true,
          type: 'dynamic',
          roundness: 0.5
        },
        arrows: {
          to: { enabled: true, scaleFactor: 0.8 }
        },
        font: {
          size: showLabels ? 12 : 0,
          align: 'middle',
          strokeWidth: 0,
          color: '#888888'
        }
      },
      physics: {
        enabled: physics,
        barnesHut: {
          gravitationalConstant: -30000,
          centralGravity: 0.3,
          springLength: 150,
          springConstant: 0.05,
          damping: 0.09,
          avoidOverlap: 0.1
        },
        stabilization: { 
          iterations: 200,
          fit: true
        }
      },
      interaction: {
        hover: true,
        hoverConnectedEdges: true,
        selectConnectedEdges: true,
        multiselect: true,
        tooltipDelay: 200,
        keyboard: {
          enabled: true
        }
      },
      layout: {
        improvedLayout: true,
        hierarchical: {
          enabled: false
        }
      },
      manipulation: {
        enabled: true, // 允许用户编辑图形
      },
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
              {selectedEdge.description && (
                <Descriptions.Item label="描述">{selectedEdge.description}</Descriptions.Item>
              )}
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