import React, { useCallback } from 'react';
import { Modal, Upload, message, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useUploadPDF } from '../../hooks/usePDFUpload';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface PDFUploaderProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: (result: any) => void;
}

const PDFUploader: React.FC<PDFUploaderProps> = ({
  visible,
  onCancel,
  onSuccess,
}) => {
  const uploadPDF = useUploadPDF();

  const handleUpload = useCallback(
    (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', '1'); // Proyecto por defecto

      uploadPDF.mutate(formData, {
        onSuccess: (data) => {
          message.success('PDF procesado exitosamente');
          onSuccess(data);
        },
        onError: (error: any) => {
          message.error('Error al procesar el PDF: ' + error.message);
        },
      });

      return false; // Evitar que el upload automático de Ant Design se ejecute
    },
    [uploadPDF, onSuccess]
  );

  const props = {
    name: 'file',
    multiple: false,
    accept: '.pdf',
    beforeUpload: (file: File) => {
      const isPDF = file.type === 'application/pdf';
      if (!isPDF) {
        message.error('Solo se permiten archivos PDF');
        return false;
      }
      
      const isLt50M = file.size / 1024 / 1024 < 50;
      if (!isLt50M) {
        message.error('El archivo debe ser menor a 50MB');
        return false;
      }

      handleUpload(file);
      return false;
    },
  };

  return (
    <Modal
      title="Cargar Presupuesto desde PDF"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
    >
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <Title level={4}>Procesamiento Automático de PDF</Title>
        <Text type="secondary">
          Sube un archivo PDF de presupuesto y nuestro sistema lo procesará automáticamente
        </Text>
      </div>

      <Dragger {...props}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text">Haz clic o arrastra un archivo PDF aquí</p>
        <p className="ant-upload-hint">
          Soportamos presupuestos en formato PDF. El sistema extraerá automáticamente
          las partidas, cantidades y precios.
        </p>
      </Dragger>

      <div style={{ marginTop: 24, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
        <Title level={5}>Formatos soportados:</Title>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li>Presupuestos en tabla (columnas fijas)</li>
          <li>Presupuestos por capítulos</li>
          <li>PDFs escaneados (con OCR)</li>
          <li>Formatos estándar de la industria</li>
        </ul>
        
        <Title level={5} style={{ marginTop: 16 }}>
          Información extraída:
        </Title>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li>Códigos de partida</li>
          <li>Descripciones</li>
          <li>Unidades de medida</li>
          <li>Cantidades</li>
          <li>Precios unitarios</li>
          <li>Totales por partida</li>
        </ul>
      </div>

      {uploadPDF.isLoading && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text>Procesando PDF...</Text>
        </div>
      )}
    </Modal>
  );
};

export default PDFUploader;