import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API请求错误:', error);
    return Promise.reject(error);
  }
);

// 数据类型定义
export interface Graph {
  id: string;
  name: string;
  description?: string;
  entity_count?: number;
  relation_count?: number;
}

export interface Category {
  id: string;
  name: string;
  parent_id?: string;
  graph_id: string;
}

export interface Entity {
  id: string;
  name: string;
  type?: string;
  properties?: Record<string, any>;
}

export interface Relationship {
  id: string;
  relation_type: string;
  source_entity_id: string;
  target_entity_id: string;
  description?: string;
  confidence?: number;
  graph_id: string;
  properties?: Record<string, any>;
}

export interface SourceResource {
  id: number;
  filename: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  uploaded_at: string;
  resource_type: string;
  content?: string;
}

export interface Subgraph {
  entities: Entity[];
  relationships: Relationship[];
}

export interface BatchResourceRequest {
  parent_id: string;
  graph_id: string;
  resources: {
    filename: string;
    content: string;
    type: string;
  }[];
}

export interface BatchResourceResponse {
  success_count: number;
  failed_count: number;
  total_count: number;
  created_resources: SourceResource[];
  failed_resources: any[];
}

// 移除任务相关类型定义，不再使用tasks API

export interface EntityCreateRequest {
  name: string;
  type: string;
  description?: string;
  graph_id: string;
}

export interface RelationCreateRequest {
  source_entity_id: string;
  target_entity_id: string;
  relation_type: string;
  confidence?: number;
  description?: string;
  graph_id: string;
}



// API方法
export const apiService = {
  // 文档管理
  getDocuments: (skip = 0, limit = 100): Promise<SourceResource[]> => 
    api.get(`/documents/?skip=${skip}&limit=${limit}`),
  getDocument: (documentId: number): Promise<SourceResource> => 
    api.get(`/documents/${documentId}`),
  deleteDocument: (documentId: number): Promise<{ message: string; details: any }> => 
    api.delete(`/documents/${documentId}`),
  createResources: (data: BatchResourceRequest): Promise<BatchResourceResponse> => 
    api.post('/documents/resources', data),
  getDocumentSubgraph: (documentId: number): Promise<Subgraph> => 
    api.get(`/documents/${documentId}/subgraph`),

  // 知识图谱管理
  getGraphs: (skip = 0, limit = 100): Promise<Graph[]> => 
    api.get(`/graphs/?skip=${skip}&limit=${limit}`),
  getGraph: (graphId: string): Promise<Graph> => 
    api.get(`/graphs/${graphId}`),
  // 新增：获取图谱下的分类列表
  getGraphCategories: (graphId: string): Promise<Category[]> => 
    api.get(`/graphs/${graphId}/categories`),
  // 新增：获取图谱级别的子图谱
  getGraphSubgraph: (graphId: string): Promise<Subgraph> => 
    api.get(`/graphs/${graphId}/subgraph`),
  // 新增：获取图谱下的文档列表（根据Neo4j关联）
  getGraphDocuments: (graphId: string): Promise<SourceResource[]> => 
    api.get(`/graphs/${graphId}/documents`),
  createGraph: (data: { name: string; description?: string }): Promise<Graph> => 
    api.post('/graphs/', data),
  deleteGraph: (graphId: string): Promise<{ message: string }> => 
    api.delete(`/graphs/${graphId}`),

  // 分类管理
  getCategory: (categoryId: string): Promise<Category> => 
    api.get(`/categories/${categoryId}`),
  createCategory: (data: { name: string; parent_id: string }): Promise<Category> => 
    api.post('/categories/', data),
  deleteCategory: (categoryId: string): Promise<{ message: string }> => 
    api.delete(`/categories/${categoryId}`),
  getCategorySubgraph: (categoryId: string): Promise<Subgraph> => 
    api.get(`/categories/${categoryId}/subgraph`),
  getCategoryDocuments: (categoryId: string): Promise<SourceResource[]> => 
    api.get(`/categories/${categoryId}/documents`),

  // 移除任务管理API，不再使用tasks接口

  // 实体管理接口
  getEntities: (graphId: string): Promise<Entity[]> => 
    api.get(`/entities/?graph_id=${graphId}`),
  createEntity: (data: EntityCreateRequest): Promise<Entity> => 
    api.post('/entities', data),
  updateEntity: (entityId: string, data: EntityCreateRequest): Promise<Entity> => 
    api.put(`/entities/${entityId}`, data),
  deleteEntity: (entityId: string): Promise<{ message: string }> => 
    api.delete(`/entities/${entityId}`),

  // 关系管理接口
  getRelations: (graphId: string): Promise<Relationship[]> => 
    api.get(`/relations/?graph_id=${graphId}`),
  createRelation: (data: RelationCreateRequest): Promise<Relationship> => 
    api.post('/relations', data),
  deleteRelation: (relationId: string): Promise<{ message: string }> => 
    api.delete(`/relations/${relationId}`),

  // 图谱数据导入接口
  importGraphData: (graphId: string): Promise<{ success: boolean; message: string }> => 
    api.post(`/graphs/${graphId}/import-data`),
};

export default api;