import { useQuery, useMutation, useQueryClient } from 'react-query';
import api from '../services/api';
import { Project, ProjectCreate } from '../types';

// Funciones API
const fetchProjects = async (companyId?: number): Promise<Project[]> => {
  const params = companyId ? { company_id: companyId } : {};
  const response = await api.get('/projects/', { params });
  return response.data;
};

const fetchProject = async (id: number): Promise<Project> => {
  const response = await api.get(`/projects/${id}`);
  return response.data;
};

const createProject = async (project: ProjectCreate): Promise<Project> => {
  const response = await api.post('/projects/', project);
  return response.data;
};

const updateProject = async ({ id, data }: { id: number; data: Partial<Project> }): Promise<Project> => {
  const response = await api.put(`/projects/${id}`, data);
  return response.data;
};

const deleteProject = async (id: number): Promise<void> => {
  await api.delete(`/projects/${id}`);
};

// Hooks
export const useProjects = (companyId?: number) => {
  return useQuery(['projects', companyId], () => fetchProjects(companyId), {
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
};

export const useProject = (id: number) => {
  return useQuery(['project', id], () => fetchProject(id), {
    staleTime: 5 * 60 * 1000,
    enabled: !!id,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation(createProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
    },
  });
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation(updateProject, {
    onSuccess: (data) => {
      queryClient.invalidateQueries('projects');
      queryClient.invalidateQueries(['project', data.id]);
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation(deleteProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('projects');
    },
  });
};