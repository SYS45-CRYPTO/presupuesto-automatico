import React, { useState } from 'react';
import { Card, Button, Table, Tag, Space, Modal, message, Upload, Row, Col, Typography } from 'antd';
import { PlusOutlined, EyeOutlined, DeleteOutlined, UploadOutlined, CalculatorOutlined, DownloadOutlined } from '@ant-design/icons';
import { useBudgets, useDeleteBudget } from '../hooks/useBudgets';
import { Budget } from '../types';
import { formatCurrency, formatDate, formatStatus, getStatusColor } from '../utils/formatters';
import BudgetForm from '../components/Budgets/BudgetForm';
import BudgetViewer from '../components/Budgets/BudgetViewer';
import PDFUploader from '../components/Budgets/PDFUploader';

const { Title } = Typography;

const Budgets: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewerVisible, setIsViewerVisible] = useState(false);
  const [isUploadVisible, setIsUploadVisible] = useState(false);
  const [selectedBudget, setSelectedBudget] = useState<Budget | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  
  const { data: budgets, isLoading, refetch } = useBudgets();
  const deleteBudget = useDeleteBudget();

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      sorter: (a: Budget, b: Budget) => a.name.localeCompare(b.name),
    },
    {
      title: 'Proyecto',
      dataIndex: ['project', 'name'],
      key: 'project',
      render: (projectName: string) => projectName || 'N/A',
    },
    {
      title: 'Cliente',
      dataIndex: ['project', 'client_name'],
      key: 'client',
      render: (clientName: string) => clientName || 'N/A',
    },
    {
      title: 'Monto Total',
      dataIndex: 'final_amount',
      key: 'final_amount',
      render: (amount: number) => formatCurrency(amount),
      sorter: (a: Budget, b: Budget) => a.final_amount - b.final_amount,
    },
    {
      title: 'Beneficio',
      dataIndex: 'profit_amount',
      key: 'profit_amount',
      render: (amount: number) => formatCurrency(amount),
    },
    {
      title: 'Margen',
      dataIndex: 'profit_margin',
      key: 'profit_margin',
      render: (profit: number, record: Budget) => {
        const margin = record.total_amount > 0 ? (profit / record.total_amount) * 100 : 0;
        return `${margin.toFixed(1)}%`;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{formatStatus(status)}</Tag>
      ),
      filters: [
        { text: 'Borrador', value: 'draft' },
        { text: 'Aprobado', value: 'approved' },
        { text: 'Rechazado', value: 'rejected' },
      ],
      onFilter: (value: string, record: Budget) => record.status === value,
    },
    {
      title: 'Fecha de Creación',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => formatDate(created_at),
      sorter: (a: Budget, b: Budget) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record: Budget) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewBudget(record)}
          />
          <Button
            type="text"
            icon={<CalculatorOutlined />}
            onClick={() => handleCalculateBudget(record)}
          />
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleExportBudget(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteBudget(record)}
          />
        </Space>
      ),
    },
  ];

  const handleViewBudget = (budget: Budget) => {
    setSelectedBudget(budget);
    setIsViewerVisible(true);
  };

  const handleCalculateBudget = (budget: Budget) => {
    // Abrir modal de cálculo
    console.log('Calcular presupuesto:', budget);
  };

  const handleExportBudget = (budget: Budget) => {
    // Mostrar opciones de exportación
    Modal.confirm({
      title: 'Exportar Presupuesto',
      content: 'Seleccione el formato de exportación:',
      okText: 'PDF',
      cancelText: 'Excel',
      onOk: () => exportToPDF(budget),
      onCancel: () => exportToExcel(budget),
    });
  };

  const exportToPDF = (budget: Budget) => {
    // Implementar exportación a PDF
    message.info('Exportación a PDF en desarrollo');
  };

  const exportToExcel = (budget: Budget) => {
    // Implementar exportación a Excel
    message.info('Exportación a Excel en desarrollo');
  };

  const handleDeleteBudget = (budget: Budget) => {
    Modal.confirm({
      title: 'Eliminar Presupuesto',
      content: `¿Está seguro de que desea eliminar el presupuesto "${budget.name}"?`,
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: () => {
        deleteBudget.mutate(budget.id, {
          onSuccess: () => {
            message.success('Presupuesto eliminado exitosamente');
            refetch();
          },
        });
      },
    });
  };

  const showModal = (projectId?: number) => {
    setSelectedProjectId(projectId || null);
    setIsModalVisible(true);
  };

  const showUploadModal = () => {
    setIsUploadVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setIsViewerVisible(false);
    setIsUploadVisible(false);
    setSelectedBudget(null);
    setSelectedProjectId(null);
  };

  const handleBudgetCreated = () => {
    setIsModalVisible(false);
    refetch();
  };

  const handlePDFProcessed = (result: any) => {
    setIsUploadVisible(false);
    message.success(`PDF procesado: ${result.items_extracted} partidas extraídas`);
    refetch();
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>Presupuestos</Title>
        </Col>
        <Col>
          <Space>
            <Button icon={<UploadOutlined />} onClick={showUploadModal}>
              Cargar PDF
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => showModal()}>
              Nuevo Presupuesto
            </Button>
          </Space>
        </Col>
      </Row>

      <Card>
        <Table
          columns={columns}
          dataSource={budgets}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total de ${total} presupuestos`,
          }}
        />
      </Card>

      {/* Modal para crear/editar presupuesto */}
      <BudgetForm
        visible={isModalVisible}
        onCancel={handleCancel}
        onSuccess={handleBudgetCreated}
        projectId={selectedProjectId}
      />

      {/* Modal para ver detalles del presupuesto */}
      <BudgetViewer
        visible={isViewerVisible}
        onCancel={handleCancel}
        budget={selectedBudget}
      />

      {/* Modal para cargar PDF */}
      <PDFUploader
        visible={isUploadVisible}
        onCancel={handleCancel}
        onSuccess={handlePDFProcessed}
      />
    </div>
  );
};

export default Budgets;