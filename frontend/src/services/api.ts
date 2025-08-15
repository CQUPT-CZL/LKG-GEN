import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api',
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
  description: string;
  domain?: string;
  category_id?: string;
  category_path?: string;
  category_name?: string;
  created_at: string;
  updated_at: string;
  entity_count: number;
  relation_count: number;
  status: string;
}

export interface Category {
  id: string;
  name: string;
  description: string;
  parent_id?: string;
  level: number;
  path: string;
  children_ids: string[];
  graph_ids: string[];
  created_at: string;
  updated_at: string;
  children?: Category[];  // 用于树形结构
}

export interface Entity {
  id: string;
  name: string;
  type: string;
  description: string;
  graph_id: string;
  created_at: string;
  updated_at: string;
  frequency: number;
  aliases: string[];
}

export interface Relation {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  source_entity_name: string;
  target_entity_name: string;
  relation_type: string;
  confidence: number;
  description: string;
  graph_id: string;
  created_at: string;
  updated_at: string;
}

export interface VisualizationData {
  nodes: Array<{
    id: string;
    label: string;
    title: string;
    color: string;
    size: number;
    font: { size: number };
    type: string;
  }>;
  edges: Array<{
    id: string;
    from: string;
    to: string;
    label: string;
    title: string;
    width: number;
    arrows: string;
    color: { color: string; highlight: string };
    font: { size: number };
  }>;
  graph_info: Graph;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: any;
}

export interface Task {
  id: string;
  name: string;
  type: 'knowledge_graph_build' | 'entity_extraction' | 'relation_extraction';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
  files: string[];
  build_mode: 'standalone' | 'append';
  target_graph_id?: string;
  result?: any;
  description?: string;
}

export interface CreateTaskRequest {
  name: string;
  type: 'knowledge_graph_build';
  build_mode: 'standalone' | 'append';
  target_graph_id?: string;
  description?: string;
  files: string[];
}

export interface SystemStats {
  total_graphs: number;
  total_entities: number;
  total_relations: number;
  entity_type_distribution: Record<string, number>;
  relation_type_distribution: Record<string, number>;
  recent_graphs: Graph[];
  system_health: string;
  last_updated: string;
}

// API方法
export const apiService = {
  // 健康检查
  healthCheck: () => api.get('/health'),

  // 统计信息
  getStats: (): Promise<SystemStats> => api.get('/stats'),

  // 图谱管理
  getGraphs: (): Promise<Graph[]> => api.get('/graphs'),
  getGraph: (id: string): Promise<Graph> => api.get(`/graphs/${id}`),
  createGraph: (data: { name: string; description?: string; category_id?: string }): Promise<Graph> => 
    api.post('/graphs', data),
  updateGraph: (id: string, data: { name: string; description?: string }): Promise<Graph> => 
    api.put(`/graphs/${id}`, data),
  deleteGraph: (id: string): Promise<{ message: string }> => 
    api.delete(`/graphs/${id}`),

  // 分类管理
  getCategories: (): Promise<Category[]> => api.get('/categories'),
  getCategoryTree: (): Promise<Category> => api.get('/categories/tree'),
  getCategory: (id: string): Promise<Category> => api.get(`/categories/${id}`),
  createCategory: (data: { name: string; description?: string; parent_id?: string }): Promise<Category> => 
    api.post('/categories', data),
  updateCategory: (id: string, data: { name: string; description?: string }): Promise<Category> => 
    api.put(`/categories/${id}`, data),
  deleteCategory: (id: string): Promise<{ message: string }> => 
    api.delete(`/categories/${id}`),
  getCategoryGraphs: (categoryId: string): Promise<Graph[]> => 
    api.get(`/categories/${categoryId}/graphs`),

  // 任务相关
  uploadDocument: (file: File): Promise<{ task_id: string; message: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getTaskStatus: (taskId: string): Promise<TaskStatus> => 
    api.get(`/tasks/${taskId}/status`),
  
  // 任务管理
  getTasks: (): Promise<Task[]> => api.get('/tasks'),
  getTask: (taskId: string): Promise<Task> => api.get(`/tasks/${taskId}`),
  createTask: (data: CreateTaskRequest): Promise<Task> => api.post('/tasks', data),
  deleteTask: (taskId: string): Promise<{ message: string }> => api.delete(`/tasks/${taskId}`),
  cancelTask: (taskId: string): Promise<{ message: string }> => api.post(`/tasks/${taskId}/cancel`),

  // 实体管理
  getEntities: (graphId: string): Promise<Entity[]> => 
    api.get(`/graphs/${graphId}/entities`),
  createEntity: (data: {
    name: string;
    type: string;
    description?: string;
    graph_id: string;
  }): Promise<Entity> => api.post('/entities', data),
  updateEntity: (id: string, data: {
    name: string;
    type: string;
    description?: string;
    graph_id: string;
  }): Promise<Entity> => api.put(`/entities/${id}`, data),
  deleteEntity: (id: string): Promise<{ message: string }> => 
    api.delete(`/entities/${id}`),

  // 关系管理
  getRelations: (graphId: string): Promise<Relation[]> => 
    api.get(`/graphs/${graphId}/relations`),
  createRelation: (data: {
    source_entity_id: string;
    target_entity_id: string;
    relation_type: string;
    confidence?: number;
    description?: string;
    graph_id: string;
  }): Promise<Relation> => api.post('/relations', data),
  deleteRelation: (id: string): Promise<{ message: string }> => 
    api.delete(`/relations/${id}`),

  // 可视化数据
  getGraphVisualization: (graphId: string): Promise<VisualizationData> => 
    api.get(`/graphs/${graphId}/visualization`),
  getCategoryVisualization: (categoryId: string): Promise<VisualizationData> => 
    api.get(`/categories/${categoryId}/visualization`),
};

export default api;