import { useQuery, useMutation, useQueryClient } from 'react-query';
import api from '../services/api';
import { Budget, BudgetCreate, CalculationRequest, CalculationResult } from '../types';

// Funciones API
const fetchBudgets = async (projectId?: number): Promise<Budget[]> => {
  const params = projectId ? { project_id: projectId } : {};
  const response = await api.get('/budgets/', { params });
  return response.data;
};

const fetchBudget = async (id: number): Promise<Budget> => {
  const response = await api.get(`/budgets/${id}`);
  return response.data;
};

const createBudget = async (budget: BudgetCreate): Promise<Budget> => {
  const response = await api.post('/budgets/', budget);
  return response.data;
};

const updateBudget = async ({ id, data }: { id: number; data: Partial<Budget> }): Promise<Budget> => {
  const response = await api.put(`/budgets/${id}`, data);
  return response.data;
};

const deleteBudget = async (id: number): Promise<void> => {
  await api.delete(`/budgets/${id}`);
};

const calculateBudget = async (request: CalculationRequest): Promise<CalculationResult> => {
  const response = await api.post(`/budgets/${request.budget_id}/calculate`, request);
  return response.data;
};

const simulateBudget = async (budgetId: number, profitMargin?: number, performanceAdjustments?: { [key: number]: number }): Promise<CalculationResult> => {
  const response = await api.post(`/budgets/${budgetId}/simulate`, {
    profit_margin: profitMargin,
    performance_adjustments: performanceAdjustments
  });
  return response.data;
};

// Funciones de exportación
const exportBudgetPDF = async (budgetId: number): Promise<Blob> => {
  const response = await api.post(`/budgets/${budgetId}/export/pdf`, {}, {
    responseType: 'blob',
  });
  return response.data;
};

const exportBudgetExcel = async (budgetId: number): Promise<Blob> => {
  const response = await api.post(`/budgets/${budgetId}/export/excel`, {}, {
    responseType: 'blob',
  });
  return response.data;
};

// Hooks
export const useBudgets = (projectId?: number) => {
  return useQuery(['budgets', projectId], () => fetchBudgets(projectId), {
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
};

export const useBudget = (id: number) => {
  return useQuery(['budget', id], () => fetchBudget(id), {
    staleTime: 5 * 60 * 1000,
    enabled: !!id,
  });
};

export const useCreateBudget = () => {
  const queryClient = useQueryClient();
  
  return useMutation(createBudget, {
    onSuccess: () => {
      queryClient.invalidateQueries('budgets');
    },
  });
};

export const useUpdateBudget = () => {
  const queryClient = useQueryClient();
  
  return useMutation(updateBudget, {
    onSuccess: (data) => {
      queryClient.invalidateQueries('budgets');
      queryClient.invalidateQueries(['budget', data.id]);
    },
  });
};

export const useDeleteBudget = () => {
  const queryClient = useQueryClient();
  
  return useMutation(deleteBudget, {
    onSuccess: () => {
      queryClient.invalidateQueries('budgets');
    },
  });
};

export const useCalculateBudget = () => {
  const queryClient = useQueryClient();
  
  return useMutation(calculateBudget, {
    onSuccess: (data) => {
      // Invalidar el presupuesto específico para actualizar los valores
      queryClient.invalidateQueries(['budget', data.budget_id]);
    },
  });
};

export const useSimulateBudget = () => {
  return useMutation(
    ({ budgetId, profitMargin, performanceAdjustments }: 
     { budgetId: number; profitMargin?: number; performanceAdjustments?: { [key: number]: number } }) => 
      simulateBudget(budgetId, profitMargin, performanceAdjustments)
  );
};

// Hooks de exportación
export const useExportBudgetPDF = () => {
  return useMutation(exportBudgetPDF);
};

export const useExportBudgetExcel = () => {
  return useMutation(exportBudgetExcel);
};

// Hook para análisis de materiales
export const useMaterialsAnalysis = (budgetId: number) => {
  return useQuery(
    ['materials-analysis', budgetId],
    async () => {
      const response = await api.get(`/budgets/${budgetId}/analysis/materials`);
      return response.data;
    },
    {
      enabled: !!budgetId,
      staleTime: 5 * 60 * 1000,
    }
  );
};

// Hook para análisis de mano de obra
export const useLaborAnalysis = (budgetId: number) => {
  return useQuery(
    ['labor-analysis', budgetId],
    async () => {
      const response = await api.get(`/budgets/${budgetId}/analysis/labor`);
      return response.data;
    },
    {
      enabled: !!budgetId,
      staleTime: 5 * 60 * 1000,
    }
  );
};