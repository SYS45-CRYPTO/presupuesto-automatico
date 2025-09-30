import axios from 'axios';
import { message } from 'antd';

// Configuración base de Axios
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejar errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // El servidor respondió con un código de error
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          message.error(data.detail || 'Solicitud inválida');
          break;
        case 401:
          message.error('No autorizado');
          break;
        case 403:
          message.error('Acceso prohibido');
          break;
        case 404:
          message.error('Recurso no encontrado');
          break;
        case 500:
          message.error('Error interno del servidor');
          break;
        default:
          message.error('Error desconocido');
      }
    } else if (error.request) {
      // La solicitud fue hecha pero no hubo respuesta
      message.error('No se pudo conectar con el servidor');
    } else {
      // Algo pasó al configurar la solicitud
      message.error('Error al configurar la solicitud');
    }
    
    return Promise.reject(error);
  }
);

// Funciones auxiliares para manejar respuestas
export const handleResponse = <T>(response: any): T => {
  return response.data;
};

export const handleError = (error: any): never => {
  throw error;
};

// Función para descargar archivos
export const downloadFile = (url: string, filename: string) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export default api;