import React, { useState } from 'react';
import { Card, Button, Table, Tag, Space, Modal, Form, Input, Select, message, Row, Col, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { useProjects, useCreateProject, useUpdateProject, useDeleteProject } from '../hooks/useProjects';
import { Project, ProjectCreate } from '../types';
import { formatDate, formatStatus, getStatusColor } from '../utils/formatters';

const { Title } = Typography;
const { Option } = Select;

const Projects: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [form] = Form.useForm();
  
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      sorter: (a: Project, b: Project) => a.name.localeCompare(b.name),
    },
    {
      title: 'Cliente',
      dataIndex: 'client_name',
      key: 'client_name',
      render: (client_name: string) => client_name || 'N/A',
    },
    {
      title: 'Ubicación',
      dataIndex: 'location',
      key: 'location',
      render: (location: string) => location || 'N/A',
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
        { text: 'Activo', value: 'active' },
        { text: 'Completado', value: 'completed' },
        { text: 'Cancelado', value: 'cancelled' },
      ],
      onFilter: (value: string, record: Project) => record.status === value,
    },
    {
      title: 'Margen de Beneficio',
      dataIndex: 'profit_margin',
      key: 'profit_margin',
      render: (profit_margin: number) => `${profit_margin}%`,
    },
    {
      title: 'Fecha de Creación',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => formatDate(created_at),
      sorter: (a: Project, b: Project) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record: Project) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewProject(record)}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditProject(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteProject(record)}
          />
        </Space>
      ),
    },
  ];

  const handleViewProject = (project: Project) => {
    // Navegar a la página de detalles del proyecto
    console.log('Ver proyecto:', project);
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    form.setFieldsValue({
      ...project,
      // Asegurarse de que los valores numéricos sean strings para el formulario
      profit_margin: project.profit_margin.toString(),
    });
    setIsModalVisible(true);
  };

  const handleDeleteProject = (project: Project) => {
    Modal.confirm({
      title: 'Eliminar Proyecto',
      content: `¿Está seguro de que desea eliminar el proyecto "${project.name}"?`,
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: () => {
        deleteProject.mutate(project.id, {
          onSuccess: () => {
            message.success('Proyecto eliminado exitosamente');
          },
        });
      },
    });
  };

  const showModal = () => {
    setEditingProject(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setEditingProject(null);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    const projectData: ProjectCreate = {
      ...values,
      profit_margin: parseFloat(values.profit_margin),
      company_id: 1, // Asumir compañía por defecto
    };

    if (editingProject) {
      updateProject.mutate(
        { id: editingProject.id, data: projectData },
        {
          onSuccess: () => {
            message.success('Proyecto actualizado exitosamente');
            setIsModalVisible(false);
          },
        }
      );
    } else {
      createProject.mutate(projectData, {
        onSuccess: () => {
          message.success('Proyecto creado exitosamente');
          setIsModalVisible(false);
        },
      });
    }
  };

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>Proyectos</Title>
        </Col>
        <Col>
          <Button type="primary" icon={<PlusOutlined />} onClick={showModal}>
            Nuevo Proyecto
          </Button>
        </Col>
      </Row>

      <Card>
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total de ${total} proyectos`,
          }}
        />
      </Card>

      <Modal
        title={editingProject ? 'Editar Proyecto' : 'Nuevo Proyecto'}
        open={isModalVisible}
        onCancel={handleCancel}
        onOk={() => form.submit()}
        confirmLoading={createProject.isLoading || updateProject.isLoading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            status: 'draft',
            profit_margin: '15.00',
          }}
        >
          <Form.Item
            name="name"
            label="Nombre del Proyecto"
            rules={[{ required: true, message: 'Por favor ingrese el nombre del proyecto' }]}
          >
            <Input placeholder="Ingrese el nombre del proyecto" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Descripción"
            rules={[{ required: true, message: 'Por favor ingrese la descripción' }]}
          >
            <Input.TextArea rows={3} placeholder="Descripción del proyecto" />
          </Form.Item>

          <Form.Item
            name="client_name"
            label="Nombre del Cliente"
          >
            <Input placeholder="Nombre del cliente" />
          </Form.Item>

          <Form.Item
            name="location"
            label="Ubicación"
          >
            <Input placeholder="Ubicación del proyecto" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="status"
                label="Estado"
                rules={[{ required: true }]}
              >
                <Select>
                  <Option value="draft">Borrador</Option>
                  <Option value="active">Activo</Option>
                  <Option value="completed">Completado</Option>
                  <Option value="cancelled">Cancelado</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="profit_margin"
                label="Margen de Beneficio (%)"
                rules={[{ required: true, message: 'Ingrese el margen de beneficio' }]}
              >
                <Input placeholder="15.00" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default Projects;