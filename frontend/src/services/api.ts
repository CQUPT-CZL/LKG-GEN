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
  entity_type?: string;
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

// 实体子图中的关系接口（后端返回的字段名称与总图谱不同）
export interface SubgraphRelationship {
  id: string;
  type: string;
  source_id: string;
  target_id: string;
  properties?: Record<string, any>;
}

export interface EntitySubgraphResponse {
  center_entity: Entity;
  entities: Entity[];
  relationships: SubgraphRelationship[];
  hops: number;
  total_entities: number;
  total_relationships: number;
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

// Prompt管理相关接口
export interface Prompt {
  id: number;
  name: string;
  prompt_type: 'ner' | 're' | 'entity_validation' | 'custom';
  content: string;
  description?: string;
  version: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PromptCreate {
  name: string;
  prompt_type: 'ner' | 're' | 'entity_validation' | 'custom';
  content: string;
  description?: string;
  version?: string;
  is_default?: boolean;
  is_active?: boolean;
}

export interface PromptUpdate {
  name?: string;
  content?: string;
  description?: string;
  version?: string;
  is_default?: boolean;
  is_active?: boolean;
}

export interface PromptListResponse {
  prompts: Prompt[];
  total: number;
  page: number;
  size: number;
}

export interface PromptType {
  type: string;
  display_name: string;
  description: string;
}

export interface PromptTypesListResponse {
  types: PromptType[];
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
  entity_type: string;
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

// 配置管理相关类型定义
export interface KnowledgeGraphConfig {
  entity_types: string[];
  relation_types: string[];
}

export interface EntityTypesConfig {
  entity_types: string[];
}

export interface RelationTypesConfig {
  relation_types: string[];
}

export interface EntityMergeRequest {
  source_entity_id: string;
  target_entity_id: string;
  merged_name?: string;
  merged_description?: string;
}

export interface EntityMergeResponse {
  success: boolean;
  message: string;
  merged_entity?: Entity;
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
  
  // 配置管理
  getKnowledgeGraphConfig: (): Promise<KnowledgeGraphConfig> =>
    api.get('/config/knowledge-graph'),
  updateKnowledgeGraphConfig: (config: KnowledgeGraphConfig): Promise<{ message: string }> =>
    api.put('/config/knowledge-graph', config),
  getEntityTypes: (): Promise<EntityTypesConfig> =>
    api.get('/config/entity-types'),
  updateEntityTypes: (config: EntityTypesConfig): Promise<{ message: string }> =>
    api.put('/config/entity-types', config),
  getRelationTypes: (): Promise<RelationTypesConfig> =>
    api.get('/config/relation-types'),
  updateRelationTypes: (config: RelationTypesConfig): Promise<{ message: string }> =>
    api.put('/config/relation-types', config),
  resetConfigToDefaults: (): Promise<{ message: string }> =>
    api.post('/config/reset-defaults'),
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
  mergeEntities: (data: EntityMergeRequest): Promise<EntityMergeResponse> => 
    api.post('/entities/merge', data),
  getEntitySubgraph: (entityId: string, hops: number = 1): Promise<EntitySubgraphResponse> => 
    api.get(`/entities/${entityId}/subgraph?hops=${hops}`),

  // 关系管理接口
  getRelations: (graphId: string): Promise<Relationship[]> => 
    api.get(`/relations/?graph_id=${graphId}`),
  createRelation: (data: RelationCreateRequest): Promise<Relationship> => 
    api.post('/relations', data),
  updateRelation: (relationId: string, data: Partial<RelationCreateRequest>): Promise<Relationship> => 
    api.put(`/relations/${relationId}`, data),
  deleteRelation: (relationId: string): Promise<{ message: string }> => 
    api.delete(`/relations/${relationId}`),

  // 图谱数据导入接口
  importGraphData: (graphId: string): Promise<{ success: boolean; message: string }> => 
    api.post(`/graphs/${graphId}/import-data`),

  // Prompt管理接口
  getPrompts: (params?: {
    prompt_type?: string;
    is_active?: boolean;
    page?: number;
    size?: number;
  }): Promise<PromptListResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.prompt_type) queryParams.append('prompt_type', params.prompt_type);
    if (params?.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.size) queryParams.append('size', params.size.toString());
    return api.get(`/prompts/?${queryParams.toString()}`);
  },
  getPrompt: (promptId: number): Promise<Prompt> => 
    api.get(`/prompts/${promptId}`),
  createPrompt: (data: PromptCreate): Promise<Prompt> => 
    api.post('/prompts/', data),
  updatePrompt: (promptId: number, data: PromptUpdate): Promise<Prompt> => 
    api.put(`/prompts/${promptId}`, data),
  deletePrompt: (promptId: number): Promise<{ message: string }> => 
    api.delete(`/prompts/${promptId}`),
  getDefaultPrompt: (promptType: string): Promise<Prompt> => 
    api.get(`/prompts/default/${promptType}`),
  setDefaultPrompt: (promptId: number): Promise<{ message: string }> => 
    api.post('/prompts/set-default', { prompt_id: promptId }),
  getPromptTypes: (): Promise<PromptTypesListResponse> => 
    api.get('/prompts/types/list'),
};

export default api;