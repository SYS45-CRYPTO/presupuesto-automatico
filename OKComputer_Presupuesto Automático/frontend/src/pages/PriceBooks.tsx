import React, { useState } from 'react';
import { Card, Button, Table, Tag, Space, Modal, message, Upload, Row, Col, Typography, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined, DownloadOutlined, BookOutlined } from '@ant-design/icons';
import { usePriceBooks, useDeletePriceBook } from '../../hooks/usePriceBooks';
import { PriceBook } from '../../types';
import { formatDate, formatStatus, getStatusColor } from '../../utils/formatters';
import PriceBookForm from '../PriceBooks/PriceBookForm';
import PriceBookViewer from '../PriceBooks/PriceBookViewer';

const { Title } = Typography;
const { Option } = Select;

const PriceBooks: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isViewerVisible, setIsViewerVisible] = useState(false);
  const [selectedPriceBook, setSelectedPriceBook] = useState<PriceBook | null>(null);
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
  
  const { data: priceBooks, isLoading, refetch } = usePriceBooks(selectedCompanyId || undefined);
  const deletePriceBook = useDeletePriceBook();

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      sorter: (a: PriceBook, b: PriceBook) => a.name.localeCompare(b.name),
    },
    {
      title: 'Descripción',
      dataIndex: 'description',
      key: 'description',
      render: (description: string) => description || 'N/A',
      ellipsis: true,
    },
    {
      title: 'Compañía',
      dataIndex: ['company', 'name'],
      key: 'company',
      render: (companyName: string) => companyName || 'N/A',
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
      filters: [
        { text: 'Activo', value: true },
        { text: 'Inactivo', value: false },
      ],
      onFilter: (value: boolean, record: PriceBook) => record.is_active === value,
    },
    {
      title: 'Vigencia',
      key: 'validity',
      render: (_, record: PriceBook) => (
        <span>
          {record.valid_from ? new Date(record.valid_from).toLocaleDateString() : 'N/A'} - 
          {record.valid_to ? new Date(record.valid_to).toLocaleDateString() : 'N/A'}
        </span>
      ),
    },
    {
      title: 'Entradas',
      dataIndex: 'entries',
      key: 'entries',
      render: (entries: any[]) => entries?.length || 0,
      sorter: (a: PriceBook, b: PriceBook) => (a.entries?.length || 0) - (b.entries?.length || 0),
    },
    {
      title: 'Fecha de Creación',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => formatDate(created_at),
      sorter: (a: PriceBook, b: PriceBook) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record: PriceBook) => (
        <Space>
          <Button
            type="text"
            icon={<BookOutlined />}
            onClick={() => handleViewPriceBook(record)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditPriceBook(record)}
          />
          <Button
            type="text"
            icon={<UploadOutlined />}
            onClick={() => handleImportPrices(record)}
          />
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleExportPriceBook(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeletePriceBook(record)}
          />
        </Space>
      ),
    },
  ];

  const handleViewPriceBook = (priceBook: PriceBook) => {
    setSelectedPriceBook(priceBook);
    setIsViewerVisible(true);
  };

  const handleEditPriceBook = (priceBook: PriceBook) => {
    setSelectedPriceBook(priceBook);
    setIsModalVisible(true);
  };

  const handleImportPrices = (priceBook: PriceBook) => {
    // Implementar importación de precios
    console.log('Importar precios:', priceBook);
  };

  const handleExportPriceBook = (priceBook: PriceBook) => {
    // Implementar exportación
    console.log('Exportar libro de precios:', priceBook);
  };

  const handleDeletePriceBook = (priceBook: PriceBook) => {
    Modal.confirm({
      title: 'Eliminar Libro de Precios',
      content: `¿Está seguro de que desea eliminar el libro de precios "${priceBook.name}"?`,
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: () => {
        deletePriceBook.mutate(priceBook.id, {
          onSuccess: () => {
            message.success('Libro de precios eliminado exitosamente');
            refetch();
          },
        });
      },
    });
  };

  const showModal = () => {
    setSelectedPriceBook(null);
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setIsViewerVisible(false);
    setSelectedPriceBook(null);
  };

  const handleSuccess = () => {
    setIsModalVisible(false);
    refetch();
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>Libros de Precios</Title>
        </Col>
        <Col>
          <Space>
            <Select
              placeholder="Filtrar por compañía"
              style={{ width: 200 }}
              onChange={setSelectedCompanyId}
              allowClear
            >
              <Option value={1}>Constructora Demo</Option>
              <Option value={2}>Otra Compañía</Option>
            </Select>
            <Button type="primary" icon={<PlusOutlined />} onClick={showModal}>
              Nuevo Libro de Precios
            </Button>
          </Space>
        </Col>
      </Row>

      <Card>
        <Table
          columns={columns}
          dataSource={priceBooks}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total de ${total} libros de precios`,
          }}
        />
      </Card>

      {/* Modal para crear/editar libro de precios */}
      <PriceBookForm
        visible={isModalVisible}
        onCancel={handleCancel}
        onSuccess={handleSuccess}
        priceBook={selectedPriceBook}
      />

      {/* Modal para ver detalles del libro de precios */}
      <PriceBookViewer
        visible={isViewerVisible}
        onCancel={handleCancel}
        priceBook={selectedPriceBook}
      />
    </div>
  );
};

export default PriceBooks;