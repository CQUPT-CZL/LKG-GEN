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
  TreeSelect,
  Form,
  Modal
} from 'antd';
import {
  FullscreenOutlined,
  FullscreenExitOutlined,
  DownloadOutlined,
  SettingOutlined,
  SearchOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  DeleteOutlined
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
  properties?: Record<string, any>;
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
  const [edgeLength, setEdgeLength] = useState(50);
  const [showLabels, setShowLabels] = useState(true);
  const [physics, setPhysics] = useState(true);
  const [mergeMode, setMergeMode] = useState(false);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);
  const [mergeDrawerVisible, setMergeDrawerVisible] = useState(false);
  // 点击节点进入子图模式开关（默认开启）
  const [clickToSubgraph, setClickToSubgraph] = useState<boolean>(true);
  const [mergedName, setMergedName] = useState('');
  const [mergedDescription, setMergedDescription] = useState('');
  const [isEditingEntity, setIsEditingEntity] = useState(false);
  const [isEditingEdge, setIsEditingEdge] = useState(false);
  const [entityTypes, setEntityTypes] = useState<string[]>([]);
  const [relationshipTypes, setRelationshipTypes] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [edgeForm] = Form.useForm();
  const networkRef = useRef<HTMLDivElement>(null);
  const networkInstance = useRef<Network | null>(null);
  
  // 实体子图相关状态
  const [entitySubgraphMode, setEntitySubgraphMode] = useState(false);
  const [currentEntityId, setCurrentEntityId] = useState<string | null>(null);
  
  // 全屏状态
  const [isFullscreen, setIsFullscreen] = useState(false);

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
    loadEntityTypes();
    loadRelationshipTypes();
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
  }, [networkData, nodeSize, edgeWidth, edgeLength, showLabels, physics]);

  const loadGraphs = async () => {
    try {
      const graphsData = await apiService.getGraphs();
      setGraphs(graphsData);
    } catch (error) {
      console.error('加载图谱失败:', error);
      message.error('加载图谱失败');
    }
  };

  const loadEntityTypes = async () => {
    try {
      const response = await apiService.getEntityTypes();
      setEntityTypes(response.entity_types);
    } catch (error) {
      console.error('加载实体类型失败:', error);
      message.error('加载实体类型失败');
    }
  };

  const loadRelationshipTypes = async () => {
    try {
      const response = await apiService.getRelationTypes();
      setRelationshipTypes(response.relation_types);
    } catch (error) {
      console.error('加载关系类型失败:', error);
      message.error('加载关系类型失败');
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

  // 新增：加载实体子图
  const loadEntitySubgraph = async (entityId: string) => {
    setLoading(true);
    try {
      const entitySubgraphResponse = await apiService.getEntitySubgraph(entityId, 1);
      
      // 将 EntitySubgraphResponse 转换为 Subgraph 格式
      // 需要将 SubgraphRelationship 转换为 Relationship 格式
       const convertedRelationships: Relationship[] = entitySubgraphResponse.relationships.map(rel => ({
          id: rel.id,
          relation_type: rel.type,
          source_entity_id: rel.source_id,
          target_entity_id: rel.target_id,
          description: rel.properties?.description || '',
          confidence: rel.properties?.confidence || 1.0,
          graph_id: selectedGraph?.id || '',
          properties: rel.properties
        }));
      
      // 去重处理：避免center_entity和entities中的重复节点
      const allEntities = [entitySubgraphResponse.center_entity, ...entitySubgraphResponse.entities];
      const uniqueEntities = allEntities.filter((entity, index, self) => 
        index === self.findIndex(e => e.id === entity.id)
      );
      
      const subgraphData: Subgraph = {
        entities: uniqueEntities,
        relationships: convertedRelationships
      };
      
      setSubgraph(subgraphData);
      setEntitySubgraphMode(true);
      setCurrentEntityId(entityId);
      message.success(`已加载实体 ${entityId} 的子图 (${entitySubgraphResponse.total_entities + 1}个实体，${entitySubgraphResponse.total_relationships}个关系) 🎯`);
    } catch (error) {
      console.error('加载实体子图失败:', error);
      message.error('加载实体子图失败');
    } finally {
      setLoading(false);
    }
  };

  // 重置到原始视图
  const resetToOriginalView = () => {
    setEntitySubgraphMode(false);
    setCurrentEntityId(null);
    if (selectedDocument) {
      loadDocumentSubgraph();
    } else if (selectedCategory) {
      loadCategorySubgraph();
    } else if (selectedGraph) {
      loadGraphSubgraph();
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
      const nodeType: string = (entity.entity_type as string) || (entity.properties?.entity_type as string) || 'Unknown';
      const nodeColor = getNodeColor(nodeType);
      const fontColor = getContrastingTextColor(nodeColor);

      return {
        id: entity.id.toString(),
        label: entity.name,
        type: nodeType,
        properties: {
          ...(entity as any).properties,
          ...(((entity as any).description) ? { description: (entity as any).description } : {}),
          ...(((entity as any).frequency !== undefined) ? { frequency: (entity as any).frequency } : {}),
          ...(((entity as any).entity_type && !(entity as any).properties?.entity_type) ? { entity_type: (entity as any).entity_type } : {})
        },
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
        size: (entitySubgraphMode && currentEntityId === entity.id.toString()) ? (nodeSize + 10) : nodeSize
      } as GraphNode;
    });

    const edges: GraphEdge[] = subgraph.relationships.map(rel => {
      const anyRel: any = rel as any;
      // 现在关系数据已经统一转换为标准格式
      const fromId = (anyRel.source_entity_id ?? anyRel.start_node_id ?? '').toString();
      const toId = (anyRel.target_entity_id ?? anyRel.end_node_id ?? '').toString();
      const relType = (anyRel.properties?.relation_type ?? anyRel.relation_type ?? anyRel.type ?? '') as string;
      const description = anyRel.description || anyRel.properties?.description || '';
      
      console.log('Edge data:', { id: anyRel.id, fromId, toId, relType, description, anyRel });
      console.log('Final edge object:', { id: (anyRel.id ?? '').toString(), from: fromId, to: toId, label: relType, type: relType });
      
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
        arrows: 'to',
        properties: anyRel.properties
      } as GraphEdge;
    });

    console.log('Setting network data - edges:', edges.map(e => ({ id: e.id, label: e.label, type: e.type })));
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
        shape: 'ellipse',
        size: nodeSize,
        font: {
          size: showLabels ? 12 : 0,
          color: '#ffffff',
          face: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
          strokeWidth: 0,
          align: 'center',
          vadjust: 0
        },
        borderWidth: 2,
        borderWidthSelected: 4,
        shadow: {
          enabled: false,
          color: 'rgba(0,0,0,0.2)',
          size: 7,
          x: 3,
          y: 3
        },
        widthConstraint: {
          minimum: 80,
          maximum: 200
        },
        margin: {
          top: 10,
          right: 10,
          bottom: 10,
          left: 10
        }
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
          type: 'continuous',
          roundness: 0.2
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
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -50,
          centralGravity: 0.01,
          springLength: edgeLength,
          springConstant: 0.08,
          damping: 0.4,
          avoidOverlap: 1.0
        },
        stabilization: {
          iterations: 800,
          updateInterval: 25,
          onlyDynamicEdges: false,
          fit: true
        },
        timestep: 0.35
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
        randomSeed: 42,
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

    // 添加事件：稳定后禁用物理以固定布局，避免后续抖动并进一步减少重叠
    networkInstance.current.once('stabilizationIterationsDone', () => {
      if (networkInstance.current) {
        networkInstance.current.setOptions({ physics: { enabled: false } });
        networkInstance.current.fit();
      }
    });

    // 如果处于实体子图模式，自动选中并聚焦中心节点，保证清晰展示
    if (entitySubgraphMode && currentEntityId) {
      try {
        networkInstance.current.selectNodes([currentEntityId]);
        networkInstance.current.focus(currentEntityId, { scale: 1.2, animation: true });
      } catch (e) {
        // ignore
      }
    }

    // 添加事件监听器
    networkInstance.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodes = networkData.nodes as GraphNode[];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          if (mergeMode) {
            // 合并模式下处理实体选择
            handleEntitySelection(nodeId);
          } else if (clickToSubgraph) {
            // 点击进入该节点的1跳子图视图
            loadEntitySubgraph(nodeId);
          } else {
            // 正常模式下显示节点详情
            setSelectedNode(node);
            setSelectedEdge(null);
            setDrawerVisible(true);
          }
        }
      } else if (params.edges.length > 0 && !mergeMode) {
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

    // 右键打开侧边栏（节点/边详情）
    networkInstance.current.on('oncontext', (params: any) => {
      // 阻止浏览器默认右键菜单
      if (params?.event?.preventDefault) params.event.preventDefault();
      if (params?.event?.stopPropagation) params.event.stopPropagation();

      if (params.nodes && params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodes = networkData.nodes as GraphNode[];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          setSelectedNode(node);
          setSelectedEdge(null);
          setDrawerVisible(true);
        }
      } else if (params.edges && params.edges.length > 0) {
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

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };



  // 实体合并相关函数
  const handleMergeMode = (enabled: boolean) => {
    setMergeMode(enabled);
    setSelectedEntities([]);
    if (networkInstance.current) {
      if (enabled) {
        message.info('合并模式已开启，请选择两个要合并的实体节点');
      } else {
        networkInstance.current.unselectAll();
        message.info('合并模式已关闭');
      }
    }
  };

  const handleEntitySelection = (nodeId: string) => {
    if (!mergeMode) return;
    
    const newSelection = [...selectedEntities];
    const index = newSelection.indexOf(nodeId);
    
    if (index > -1) {
      // 取消选择
      newSelection.splice(index, 1);
    } else {
      // 添加选择
      if (newSelection.length >= 2) {
        message.warning('最多只能选择两个实体进行合并');
        return;
      }
      newSelection.push(nodeId);
    }
    
    setSelectedEntities(newSelection);
    
    if (newSelection.length === 2) {
      // 准备合并
      const nodes = networkData.nodes as GraphNode[];
      const sourceEntity = nodes.find(n => n.id === newSelection[0]);
      const targetEntity = nodes.find(n => n.id === newSelection[1]);
      
      if (sourceEntity && targetEntity) {
        setMergedName(targetEntity.label);
        setMergedDescription('');
        setMergeDrawerVisible(true);
      }
    }
  };

  const executeMerge = async () => {
    if (selectedEntities.length !== 2) {
      message.error('请选择两个实体进行合并');
      return;
    }

    try {
      const mergeRequest = {
        source_entity_id: selectedEntities[0],
        target_entity_id: selectedEntities[1],
        merged_name: mergedName || undefined,
        merged_description: mergedDescription || undefined
      };

      const response = await apiService.mergeEntities(mergeRequest);
      
      if (response.success) {
        message.success(response.message);
        setMergeDrawerVisible(false);
        setMergeMode(false);
        setSelectedEntities([]);
        setMergedName('');
        setMergedDescription('');
        
        // 重新加载图谱数据
        if (selectedDocument) {
          loadDocumentSubgraph();
        } else if (selectedCategory) {
          loadCategorySubgraph();
        } else if (selectedGraph) {
          loadGraphSubgraph();
        }
      } else {
        message.error('合并失败: ' + response.message);
      }
    } catch (error) {
      console.error('合并实体失败:', error);
      message.error('合并实体失败');
    }
  };

  const cancelMerge = () => {
    setMergeDrawerVisible(false);
    setSelectedEntities([]);
    setMergedName('');
    setMergedDescription('');
    if (networkInstance.current) {
      networkInstance.current.unselectAll();
    }
  };

  // 实体编辑相关函数
  const handleEditEntity = () => {
    if (!selectedNode) return;
    
    setIsEditingEntity(true);
    form.setFieldsValue({
      name: selectedNode.label,
      entity_type: selectedNode.type,
      description: selectedNode.properties?.description || ''
    });
  };

  const handleSaveEntity = async () => {
    if (!selectedNode || !selectedGraph) return;
    
    try {
      const values = await form.validateFields();
      const updateData = {
        name: values.name,
        entity_type: values.entity_type,
        description: values.description || '',
        graph_id: selectedGraph.id
      };

      await apiService.updateEntity(selectedNode.id, updateData);
      message.success('实体更新成功! 🎉');
      
      // 更新本地节点数据
      const updatedNode = {
        ...selectedNode,
        label: values.name,
        type: values.entity_type,
        properties: {
          ...selectedNode.properties,
          description: values.description
        }
      };
      setSelectedNode(updatedNode);
      
      setIsEditingEntity(false);
      
      // 重新加载图谱数据以更新可视化
      if (selectedDocument) {
        loadDocumentSubgraph();
      } else if (selectedCategory) {
        loadCategorySubgraph();
      } else if (selectedGraph) {
        loadGraphSubgraph();
      }
    } catch (error) {
      console.error('更新实体失败:', error);
      message.error('更新实体失败');
    }
  };

  const handleCancelEdit = () => {
    setIsEditingEntity(false);
    form.resetFields();
  };

  const handleDeleteEntity = () => {
    if (!selectedNode || !selectedGraph) return;
    
    Modal.confirm({
      title: '确认删除实体',
      content: `确定要删除实体 "${selectedNode.label}" 吗？此操作不可撤销。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await apiService.deleteEntity(selectedNode.id);
          message.success('实体删除成功! 🗑️');
          
          // 关闭Drawer
          setDrawerVisible(false);
          setSelectedNode(null);
          setIsEditingEntity(false);
          
          // 重新加载图谱数据以更新可视化
          if (selectedDocument) {
            loadDocumentSubgraph();
          } else if (selectedCategory) {
            loadCategorySubgraph();
          } else if (selectedGraph) {
            loadGraphSubgraph();
          }
        } catch (error) {
          console.error('删除实体失败:', error);
          message.error('删除实体失败');
        }
      }
    });
  };

  // 边编辑相关函数
  const handleEditEdge = () => {
    if (!selectedEdge) return;
    
    setIsEditingEdge(true);
    edgeForm.setFieldsValue({
      type: selectedEdge.type,
      description: selectedEdge.description || ''
    });
  };

  const handleSaveEdge = async () => {
    if (!selectedEdge || !selectedGraph) return;
    
    try {
      const values = await edgeForm.validateFields();
      const updateData = {
        relation_type: values.type,
        description: values.description || '',
        graph_id: selectedGraph.id
      };

      await apiService.updateRelation(selectedEdge.id, updateData);
      message.success('关系更新成功! 🎉');
      
      // 更新本地边数据
      const updatedEdge = {
        ...selectedEdge,
        type: values.type,
        description: values.description
      };
      setSelectedEdge(updatedEdge);
      
      setIsEditingEdge(false);
      
      // 重新加载图谱数据以更新可视化
      if (selectedDocument) {
        loadDocumentSubgraph();
      } else if (selectedCategory) {
        loadCategorySubgraph();
      } else if (selectedGraph) {
        loadGraphSubgraph();
      }
    } catch (error) {
      console.error('更新关系失败:', error);
      message.error('更新关系失败');
    }
  };

  const handleCancelEditEdge = () => {
    setIsEditingEdge(false);
    edgeForm.resetFields();
  };

  return (
    <div style={{ 
      padding: isFullscreen ? '0' : '24px',
      position: isFullscreen ? 'fixed' : 'relative',
      top: isFullscreen ? 0 : 'auto',
      left: isFullscreen ? 0 : 'auto',
      width: isFullscreen ? '100vw' : 'auto',
      height: isFullscreen ? '100vh' : 'auto',
      zIndex: isFullscreen ? 9999 : 'auto',
      backgroundColor: isFullscreen ? '#fff' : 'transparent'
    }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={!isFullscreen ? <Title level={3}>🔍 图谱可视化</Title> : null}
            extra={
              !isFullscreen ? (
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
              ) : null
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={isFullscreen ? 24 : 18}>
                <Card
                  size="small"
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>图谱视图</span>
                      {entitySubgraphMode && currentEntityId && (
                         <Tag color="blue">
                           🎯 实体子图: {currentEntityId}
                         </Tag>
                       )}
                    </div>
                  }
                  extra={
                    <Space>
                      {entitySubgraphMode && (
                        <Button 
                          type="default" 
                          icon={<ReloadOutlined />}
                          onClick={resetToOriginalView}
                          size="small"
                        >
                          退出子图模式
                        </Button>
                      )}
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
                      <Tooltip title={isFullscreen ? "退出全屏" : "全屏显示"}>
                        <Button 
                          icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />} 
                          onClick={handleFullscreen} 
                        />
                      </Tooltip>
                      <Tooltip title="重置视图">
                        <Button icon={<ReloadOutlined />} onClick={handleReset} />
                      </Tooltip>
                      <Tooltip title="下载图片">
                        <Button icon={<DownloadOutlined />} onClick={handleDownload} />
                      </Tooltip>
                      <Tooltip title="实体合并">
                        <Button 
                          type={mergeMode ? 'primary' : 'default'}
                          onClick={() => handleMergeMode(!mergeMode)}
                        >
                          {mergeMode ? '🔗 合并中' : '🔗 合并'}
                        </Button>
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
                        height: isFullscreen ? 'calc(100vh - 80px)' : '600px',
                        border: '1px solid #d9d9d9',
                        borderRadius: '6px'
                      }}
                    />
                  </Spin>
                </Card>
              </Col>
              
              {!isFullscreen && (
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
                    <Text>边长度</Text>
                    <Slider
                      min={20}
                      max={150}
                      value={edgeLength}
                      onChange={setEdgeLength}
                      style={{ marginTop: 8 }}
                      marks={{
                        20: '短',
                        50: '中',
                        100: '长',
                        150: '很长'
                      }}
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
              )}
            </Row>
          </Card>
        </Col>
      </Row>

      <Drawer
        title={
          selectedNode ? (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{isEditingEntity ? '编辑实体' : '节点详情'}</span>
              {!isEditingEntity && (
                <Button 
                  type="text" 
                  icon={<EditOutlined />} 
                  onClick={handleEditEntity}
                  size="small"
                >
                  编辑
                </Button>
              )}
            </div>
          ) : selectedEdge ? (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{isEditingEdge ? '编辑关系' : '关系详情'}</span>
              {!isEditingEdge && (
                <Button 
                  type="text" 
                  icon={<EditOutlined />} 
                  onClick={handleEditEdge}
                  size="small"
                >
                  编辑
                </Button>
              )}
            </div>
          ) : '详情'
        }
        placement="right"
        onClose={() => {
          setDrawerVisible(false);
          setIsEditingEntity(false);
          setIsEditingEdge(false);
          form.resetFields();
          edgeForm.resetFields();
        }}
        open={drawerVisible}
        width={400}
        footer={isEditingEntity && selectedNode ? (
            <div style={{ textAlign: 'right' }}>
              <Space>
                <Button onClick={handleCancelEdit} icon={<CloseOutlined />}>
                  取消
                </Button>
                <Button danger onClick={handleDeleteEntity} icon={<DeleteOutlined />}>
                  删除
                </Button>
                <Button type="primary" onClick={handleSaveEntity} icon={<SaveOutlined />}>
                  保存
                </Button>
              </Space>
            </div>
          ) : isEditingEdge && selectedEdge ? (
            <div style={{ textAlign: 'right' }}>
              <Space>
                <Button onClick={handleCancelEditEdge} icon={<CloseOutlined />}>
                  取消
                </Button>
                <Button type="primary" onClick={handleSaveEdge} icon={<SaveOutlined />}>
                  保存
                </Button>
              </Space>
            </div>
          ) : null
        }
      >
        {selectedNode && (
          <div>
            {!isEditingEntity ? (
              // 查看模式
              <>
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="ID">{selectedNode.id}</Descriptions.Item>
                  <Descriptions.Item label="名称">{selectedNode.label}</Descriptions.Item>
                  <Descriptions.Item label="类型">
                    <Tag color={getNodeColor(selectedNode.type)}>{selectedNode.type}</Tag>
                  </Descriptions.Item>
                  {selectedNode.properties?.description && (
                    <Descriptions.Item label="描述">{selectedNode.properties.description}</Descriptions.Item>
                  )}
                  {selectedNode.properties?.frequency !== undefined && (
                    <Descriptions.Item label="频次">{selectedNode.properties.frequency}</Descriptions.Item>
                  )}
                </Descriptions>
                
                {/* 实体子图操作按钮 */}
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <Space>
                    <Button 
                      type="primary" 
                      icon={<SearchOutlined />}
                      onClick={() => loadEntitySubgraph(selectedNode.id)}
                      loading={loading}
                    >
                      查看实体子图
                    </Button>
                    {entitySubgraphMode && currentEntityId === selectedNode.id && (
                      <Button 
                        icon={<ReloadOutlined />}
                        onClick={resetToOriginalView}
                      >
                        返回原视图
                      </Button>
                    )}
                  </Space>
                </div>
                
                {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <Text strong>属性信息</Text>
                    <Descriptions column={1} bordered size="small" style={{ marginTop: 8 }}>
                      {Object.entries(selectedNode.properties).map(([key, value]) => (
                        <Descriptions.Item key={key} label={key}>
                          {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                        </Descriptions.Item>
                      ))}
                    </Descriptions>
                  </div>
                )}
              </>
            ) : (
              // 编辑模式
              <Form
                form={form}
                layout="vertical"
                initialValues={{
                  name: selectedNode.label,
                  entity_type: selectedNode.type,
                  description: selectedNode.properties?.description || ''
                }}
              >
                <Form.Item
                  label="实体名称"
                  name="name"
                  rules={[{ required: true, message: '请输入实体名称' }]}
                >
                  <Input placeholder="请输入实体名称" />
                </Form.Item>
                
                <Form.Item
                  label="实体类型"
                  name="entity_type"
                  rules={[{ required: true, message: '请选择实体类型' }]}
                >
                  <Select placeholder="请选择实体类型" showSearch>
                    {entityTypes.map(type => (
                      <Option key={type} value={type}>{type}</Option>
                    ))}
                  </Select>
                </Form.Item>
                
                <Form.Item
                  label="描述"
                  name="description"
                >
                  <Input.TextArea 
                    rows={4} 
                    placeholder="请输入实体描述（可选）" 
                  />
                </Form.Item>
                
                <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                  <Text strong style={{ color: '#666' }}>实体ID: </Text>
                  <Text code>{selectedNode.id}</Text>
                </div>
              </Form>
            )}
          </div>
        )}
        
        {selectedEdge && (
          <div>
            {!isEditingEdge ? (
              // 查看模式
              <>
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="ID">{selectedEdge.id}</Descriptions.Item>
                  <Descriptions.Item label="类型">{selectedEdge.type}</Descriptions.Item>
                  {selectedEdge.description && (
                    <Descriptions.Item label="描述">{selectedEdge.description}</Descriptions.Item>
                  )}
                  <Descriptions.Item label="源节点">{(() => {
                    const nodes = networkData.nodes as GraphNode[];
                    const n = nodes.find(node => node.id === selectedEdge.from);
                    return n ? `${n.label} (${selectedEdge.from})` : selectedEdge.from;
                  })()}</Descriptions.Item>
                  <Descriptions.Item label="目标节点">{(() => {
                    const nodes = networkData.nodes as GraphNode[];
                    const n = nodes.find(node => node.id === selectedEdge.to);
                    return n ? `${n.label} (${selectedEdge.to})` : selectedEdge.to;
                  })()}</Descriptions.Item>
                  {selectedEdge.properties?.confidence !== undefined && (
                    <Descriptions.Item label="置信度">{String(selectedEdge.properties.confidence)}</Descriptions.Item>
                  )}
                  {selectedEdge.weight && (
                    <Descriptions.Item label="权重">{selectedEdge.weight}</Descriptions.Item>
                  )}
                </Descriptions>
                {selectedEdge.properties && Object.keys(selectedEdge.properties).length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <Text strong>属性信息</Text>
                    <Descriptions column={1} bordered size="small" style={{ marginTop: 8 }}>
                      {Object.entries(selectedEdge.properties).map(([key, value]) => (
                        <Descriptions.Item key={key} label={key}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </Descriptions.Item>
                      ))}
                    </Descriptions>
                  </div>
                )}
              </>
            ) : (
              // 编辑模式
              <Form
                form={edgeForm}
                layout="vertical"
                initialValues={{
                  type: selectedEdge.type,
                  description: selectedEdge.description || ''
                }}
              >
                <Form.Item
                  label="关系类型"
                  name="type"
                  rules={[{ required: true, message: '请选择关系类型' }]}
                >
                  <Select placeholder="请选择关系类型" showSearch>
                    {relationshipTypes.map(type => (
                      <Option key={type} value={type}>{type}</Option>
                    ))}
                  </Select>
                </Form.Item>
                
                <Form.Item
                  label="描述"
                  name="description"
                >
                  <Input.TextArea 
                    rows={4} 
                    placeholder="请输入关系描述（可选）" 
                  />
                </Form.Item>
                
                <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                  <Text strong style={{ color: '#666' }}>关系ID: </Text>
                  <Text code>{selectedEdge.id}</Text>
                </div>
                
                <div style={{ marginTop: 12, padding: '12px', backgroundColor: '#f0f8ff', borderRadius: '6px' }}>
                  <Text strong style={{ color: '#666' }}>源节点: </Text>
                  <Text>{(() => {
                    const nodes = networkData.nodes as GraphNode[];
                    const n = nodes.find(node => node.id === selectedEdge.from);
                    return n ? `${n.label} (${selectedEdge.from})` : selectedEdge.from;
                  })()}</Text>
                  <br />
                  <Text strong style={{ color: '#666' }}>目标节点: </Text>
                  <Text>{(() => {
                    const nodes = networkData.nodes as GraphNode[];
                    const n = nodes.find(node => node.id === selectedEdge.to);
                    return n ? `${n.label} (${selectedEdge.to})` : selectedEdge.to;
                  })()}</Text>
                </div>
              </Form>
            )}
          </div>
        )}
      </Drawer>

      {/* 实体合并抽屉 */}
      <Drawer
        title="实体合并"
        placement="right"
        onClose={cancelMerge}
        open={mergeDrawerVisible}
        width={400}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={cancelMerge}>取消</Button>
              <Button type="primary" onClick={executeMerge}>
                确认合并
              </Button>
            </Space>
          </div>
        }
      >
        {selectedEntities.length === 2 && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>合并说明：</Text>
              <Paragraph>
                将把第一个实体合并到第二个实体中，第一个实体将被删除，所有相关的关系和属性将转移到第二个实体。
              </Paragraph>
            </div>
            
            <Divider />
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>源实体（将被删除）：</Text>
              <div style={{ padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px', marginTop: 8 }}>
                <Text>{(() => {
                  const nodes = networkData.nodes as GraphNode[];
                  const sourceEntity = nodes.find(n => n.id === selectedEntities[0]);
                  return sourceEntity?.label || selectedEntities[0];
                })()}</Text>
              </div>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>目标实体（保留）：</Text>
              <div style={{ padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px', marginTop: 8 }}>
                <Text>{(() => {
                  const nodes = networkData.nodes as GraphNode[];
                  const targetEntity = nodes.find(n => n.id === selectedEntities[1]);
                  return targetEntity?.label || selectedEntities[1];
                })()}</Text>
              </div>
            </div>
            
            <Divider />
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>合并后名称：</Text>
              <Input
                value={mergedName}
                onChange={(e) => setMergedName(e.target.value)}
                placeholder="输入合并后的实体名称"
                style={{ marginTop: 8 }}
              />
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <Text strong>合并后描述：</Text>
              <Input.TextArea
                value={mergedDescription}
                onChange={(e) => setMergedDescription(e.target.value)}
                placeholder="输入合并后的实体描述（可选）"
                rows={3}
                style={{ marginTop: 8 }}
              />
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default GraphVisualization;