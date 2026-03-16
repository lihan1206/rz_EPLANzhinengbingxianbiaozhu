import apiClient from './client';
import {
  Annotation,
  DashboardSummary,
  DistributionItem,
  ImportRecord,
  LoginPayload,
  OperationLog,
  ParallelGroup,
  Project,
  UserInfo,
} from '../types';

export const login = async (payload: LoginPayload) => {
  const { data } = await apiClient.post<{ access_token: string; token_type: string }>('/auth/login', payload);
  return data;
};

export const getCurrentUser = async () => {
  const { data } = await apiClient.get<UserInfo>('/auth/me');
  return data;
};

export const getProjects = async () => {
  const { data } = await apiClient.get<Project[]>('/projects');
  return data;
};

export const createProject = async (payload: { name: string; version: string }) => {
  const { data } = await apiClient.post<Project>('/projects', payload);
  return data;
};

export const deleteProject = async (projectId: number) => {
  const { data } = await apiClient.delete<{ message: string }>(`/projects/${projectId}`);
  return data;
};

export const getDashboardSummary = async () => {
  const { data } = await apiClient.get<DashboardSummary>('/dashboard/summary');
  return data;
};

export const getDistribution = async (projectId: number) => {
  const { data } = await apiClient.get<DistributionItem[]>(`/dashboard/distribution/${projectId}`);
  return data;
};

export const importEplan = async (projectId: number, file: File) => {
  const formData = new FormData();
  formData.append('project_id', String(projectId));
  formData.append('file', file);
  const { data } = await apiClient.post('/imports/eplan', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const getImportRecords = async (projectId: number) => {
  const { data } = await apiClient.get<ImportRecord[]>('/imports/records', {
    params: { project_id: projectId },
  });
  return data;
};

export const analyzeProject = async (projectId: number, minParallelCount: number) => {
  const { data } = await apiClient.post<{ groups_created: number }>(`/analysis/${projectId}`, {
    min_parallel_count: minParallelCount,
  });
  return data;
};

export const getParallelGroups = async (projectId: number) => {
  const { data } = await apiClient.get<ParallelGroup[]>(`/analysis/${projectId}/groups`);
  return data;
};

export const generateAnnotations = async (projectId: number, template: string, style: string) => {
  const { data } = await apiClient.post<Annotation[]>(`/annotations/generate/${projectId}`, {
    template,
    style,
  });
  return data;
};

export const getAnnotations = async (projectId: number) => {
  const { data } = await apiClient.get<Annotation[]>(`/annotations/${projectId}`);
  return data;
};

export const getUsers = async () => {
  const { data } = await apiClient.get<UserInfo[]>('/users');
  return data;
};

export const getLogs = async () => {
  const { data } = await apiClient.get<OperationLog[]>('/logs');
  return data;
};

export const downloadGroupsCsv = async (projectId: number) => {
  const response = await apiClient.get(`/exports/groups/${projectId}`, {
    responseType: 'blob',
  });
  return response.data as Blob;
};
