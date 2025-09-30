import { useQuery } from 'react-query';
import api from '../services/api';
import { DashboardMetrics } from '../types';

// Función para obtener métricas del dashboard
const fetchDashboardMetrics = async (companyId?: number): Promise<DashboardMetrics> => {
  const params = companyId ? { company_id: companyId } : {};
  const response = await api.get('/dashboard/metrics', { params });
  return response.data;
};

// Hook para obtener métricas del dashboard
export const useDashboardMetrics = (companyId?: number) => {
  return useQuery(
    ['dashboard-metrics', companyId],
    () => fetchDashboardMetrics(companyId),
    {
      staleTime: 5 * 60 * 1000, // 5 minutos
      refetchInterval: 30 * 60 * 1000, // Refrescar cada 30 minutos
    }
  );
};