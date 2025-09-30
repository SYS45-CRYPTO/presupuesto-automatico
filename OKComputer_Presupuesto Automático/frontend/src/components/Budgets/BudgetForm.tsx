import React from 'react';
import { Modal, Form, Input, Select, InputNumber, Button, Space, message } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { useCreateBudget } from '../../hooks/useBudgets';
import { BudgetCreate, BudgetItem } from '../../types';

const { Option } = Select;
const { TextArea } = Input;

interface BudgetFormProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  projectId?: number | null;
}

const BudgetForm: React.FC<BudgetFormProps> = ({
  visible,
  onCancel,
  onSuccess,
  projectId,
}) => {
  const [form] = Form.useForm();
  const createBudget = useCreateBudget();

  const handleSubmit = (values: any) => {
    const budgetData: BudgetCreate = {
      project_id: values.project_id || projectId || 1,
      name: values.name,
      description: values.description,
      version: values.version || '1.0',
    };

    createBudget.mutate(budgetData, {
      onSuccess: (data) => {
        message.success('Presupuesto creado exitosamente');
        form.resetFields();
        onSuccess();
      },
      onError: (error: any) => {
        message.error('Error al crear el presupuesto: ' + error.message);
      },
    });
  };

  return (
    <Modal
      title="Nuevo Presupuesto"
      open={visible}
      onCancel={onCancel}
      onOk={() => form.submit()}
      confirmLoading={createBudget.isLoading}
      width={800}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancelar
        </Button>,
        <Button
          key="submit"
          type="primary"
          onClick={() => form.submit()}
          loading={createBudget.isLoading}
        >
          Crear Presupuesto
        </Button>,
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          version: '1.0',
        }}
      >
        {!projectId && (
          <Form.Item
            name="project_id"
            label="Proyecto"
            rules={[{ required: true, message: 'Seleccione un proyecto' }]}
          >
            <Select placeholder="Seleccione un proyecto">
              <Option value={1}>Proyecto Demo 1</Option>
              <Option value={2}>Proyecto Demo 2</Option>
            </Select>
          </Form.Item>
        )}

        <Form.Item
          name="name"
          label="Nombre del Presupuesto"
          rules={[{ required: true, message: 'Ingrese el nombre del presupuesto' }]}
        >
          <Input placeholder="Ingrese el nombre del presupuesto" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Descripción"
          rules={[{ required: true, message: 'Ingrese la descripción' }]}
        >
          <TextArea rows={3} placeholder="Descripción del presupuesto" />
        </Form.Item>

        <Form.Item
          name="version"
          label="Versión"
          rules={[{ required: true, message: 'Ingrese la versión' }]}
        >
          <Input placeholder="1.0" />
        </Form.Item>

        {/* Sección de partidas - simplificada para este ejemplo */}
        <Form.List name="items">
          {(fields, { add, remove }) => (
            <>
              <Form.Item label="Partidas del Presupuesto">
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item
                      {...restField}
                      name={[name, 'description']}
                      rules={[{ required: true, message: 'Descripción requerida' }]}
                    >
                      <Input placeholder="Descripción" style={{ width: 300 }} />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'unit']}
                      rules={[{ required: true, message: 'Unidad requerida' }]}
                    >
                      <Input placeholder="Unidad" style={{ width: 100 }} />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'quantity']}
                      rules={[{ required: true, message: 'Cantidad requerida' }]}
                    >
                      <InputNumber placeholder="Cantidad" style={{ width: 100 }} />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'unit_price']}
                      rules={[{ required: true, message: 'Precio requerido' }]}
                    >
                      <InputNumber placeholder="P. Unitario" style={{ width: 100 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(name)} />
                  </Space>
                ))}
                <Form.Item>
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    Agregar Partida
                  </Button>
                </Form.Item>
              </Form.Item>
            </>
          )}
        </Form.List>
      </Form>
    </Modal>
  );
};

export default BudgetForm;