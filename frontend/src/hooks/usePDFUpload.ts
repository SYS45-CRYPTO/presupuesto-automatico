import { useMutation } from 'react-query';
import api from '../services/api';
import { PDFUploadResponse } from '../types';

// Función para subir y procesar PDF
const uploadPDF = async (formData: FormData): Promise<PDFUploadResponse> => {
  const response = await api.post('/pdf/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Hook para subir PDF
export const useUploadPDF = () => {
  return useMutation(uploadPDF);
};