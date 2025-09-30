import React, { useState } from 'react';
import { Modal, Form, InputNumber, Button, Space, Row, Col, Card, Statistic, Typography } from 'antd';
import { CalculatorOutlined, DollarOutlined } from '@ant-design/icons';
import { useCalculateBudget, useSimulateBudget } from '../../hooks/useBudgets';
import { formatCurrency } from '../../utils/formatters';

const { Title } = Typography;

interface BudgetCalculatorProps {
  visible: boolean;
  onCancel: () => void;
  budgetId: number;
  currentProfitMargin?: number;
}

const BudgetCalculator: React.FC<BudgetCalculatorProps> = ({
  visible,
  onCancel,
  budgetId,
  currentProfitMargin = 15,
}) => {
  const [form] = Form.useForm();
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'basic' | 'advanced'>('basic');
  
  const calculateBudget = useCalculateBudget();
  const simulateBudget = useSimulateBudget();

  const handleBasicCalculation = (values: any) => {
    const request = {
      budget_id: budgetId,
      profit_margin: values.profit_margin,
    };

    calculateBudget.mutate(request, {
      onSuccess: (data) => {
        setSimulationResult(data);
      },
    });
  };

  const handleAdvancedSimulation = (values: any) => {
    simulateBudget.mutate(
      {
        budgetId,
        profitMargin: values.profit_margin,
        performanceAdjustments: values.performance_adjustments,
      },
      {
        onSuccess: (data) => {
          setSimulationResult(data);
        },
      }
    );
  };

  const renderBasicCalculator = () => (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleBasicCalculation}
      initialValues={{
        profit_margin: currentProfitMargin,
      }}
    >
      <Form.Item
        name="profit_margin"
        label="Margen de Beneficio (%)"
        rules={[{ required: true, message: 'Ingrese el margen de beneficio' }]}
      >
        <InputNumber
          min={0}
          max={100}
          step={0.1}
          style={{ width: '100%' }}
          placeholder="15.0"
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<CalculatorOutlined />}
          loading={calculateBudget.isLoading}
          block
        >
          Calcular Presupuesto
        </Button>
      </Form.Item>
    </Form>
  );

  const renderAdvancedCalculator = () => (
    <Form
      layout="vertical"
      onFinish={handleAdvancedSimulation}
      initialValues={{
        profit_margin: currentProfitMargin,
      }}
    >
      <Form.Item
        name="profit_margin"
        label="Margen de Beneficio (%)"
        rules={[{ required: true }]}
      >
        <InputNumber
          min={0}
          max={100}
          step={0.1}
          style={{ width: '100%' }}
        />
      </Form.Item>

      <Form.Item
        name="performance_adjustments"
        label="Ajustes de Rendimiento"
        help="Ajuste el rendimiento por partida (opcional)"
      >
        <InputNumber
          min={0.1}
          max={5.0}
          step={0.1}
          style={{ width: '100%' }}
          placeholder="1.0 = Rendimiento normal"
        />
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<CalculatorOutlined />}
          loading={simulateBudget.isLoading}
          block
        >
          Simular Presupuesto
        </Button>
      </Form.Item>
    </Form>
  );

  const renderResults = () => {
    if (!simulationResult) return null;

    return (
      <div style={{ marginTop: 24 }}>
        <Title level={4}>Resultados del Cálculo</Title>
        <Row gutter={16}>
          <Col span={8}>
            <Card>
              <Statistic
                title="Subtotal"
                value={simulationResult.subtotal}
                prefix={<DollarOutlined />}
                precision={2}
                formatter={(value) => formatCurrency(value as number)}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="Beneficio"
                value={simulationResult.profit_amount}
                prefix={<DollarOutlined />}
                precision={2}
                formatter={(value) => formatCurrency(value as number)}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="Total"
                value={simulationResult.total_amount}
                prefix={<DollarOutlined />}
                precision={2}
                formatter={(value) => formatCurrency(value as number)}
              />
            </Card>
          </Col>
        </Row>

        {simulationResult.cost_breakdown && (
          <Card title="Desglose de Costos" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Mano de Obra"
                  value={simulationResult.cost_breakdown.labor_cost}
                  precision={2}
                  formatter={(value) => formatCurrency(value as number)}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Materiales"
                  value={simulationResult.cost_breakdown.material_cost}
                  precision={2}
                  formatter={(value) => formatCurrency(value as number)}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Equipo"
                  value={simulationResult.cost_breakdown.equipment_cost}
                  precision={2}
                  formatter={(value) => formatCurrency(value as number)}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Costos Indirectos"
                  value={simulationResult.cost_breakdown.indirect_cost}
                  precision={2}
                  formatter={(value) => formatCurrency(value as number)}
                />
              </Col>
            </Row>
          </Card>
        )}

        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Space>
            <Button type="primary" onClick={() => console.log('Aplicar cambios')}>
              Aplicar Cambios
            </Button>
            <Button onClick={() => setSimulationResult(null)}>
              Limpiar Resultados
            </Button>
          </Space>
        </div>
      </div>
    );
  };

  return (
    <Modal
      title="Calculadora de Presupuesto"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button
            type={activeTab === 'basic' ? 'primary' : 'default'}
            onClick={() => setActiveTab('basic')}
          >
            Cálculo Básico
          </Button>
          <Button
            type={activeTab === 'advanced' ? 'primary' : 'default'}
            onClick={() => setActiveTab('advanced')}
          >
            Simulación Avanzada
          </Button>
        </Space>
      </div>

      {activeTab === 'basic' ? renderBasicCalculator() : renderAdvancedCalculator()}

      {renderResults()}
    </Modal>
  );
};

export default BudgetCalculator;