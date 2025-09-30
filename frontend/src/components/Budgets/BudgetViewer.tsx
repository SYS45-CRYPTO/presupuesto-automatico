import React, { useState } from 'react';
import { Modal, Tabs, Descriptions, Table, Card, Row, Col, Statistic, Typography, Space, Button } from 'antd';
import { DollarOutlined, CalculatorOutlined, DownloadOutlined } from '@ant-design/icons';
import { Budget } from '../../types';
import { formatCurrency } from '../../utils/formatters';
import BudgetCalculator from './BudgetCalculator';

const { TabPane } = Tabs;
const { Title } = Typography;

interface BudgetViewerProps {
  visible: boolean;
  onCancel: () => void;
  budget: Budget | null;
}

const BudgetViewer: React.FC<BudgetViewerProps> = ({
  visible,
  onCancel,
  budget,
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [showCalculator, setShowCalculator] = useState(false);

  if (!budget) return null;

  // Agrupar partidas por capítulo
  const chapters = budget.items?.reduce((acc, item) => {
    const chapter = item.chapter || 'Sin Capítulo';
    if (!acc[chapter]) {
      acc[chapter] = {
        name: chapter,
        items: [],
        total: 0,
      };
    }
    acc[chapter].items.push(item);
    acc[chapter].total += item.total_price;
    return acc;
  }, {} as { [key: string]: { name: string; items: any[]; total: number } }) || {};

  const columns = [
    {
      title: 'Código',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: 'Descripción',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Unidad',
      dataIndex: 'unit',
      key: 'unit',
    },
    {
      title: 'Cantidad',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(2),
    },
    {
      title: 'P. Unitario',
      dataIndex: 'unit_price',
      key: 'unit_price',
      render: (price: number) => formatCurrency(price),
    },
    {
      title: 'Total',
      dataIndex: 'total_price',
      key: 'total_price',
      render: (price: number) => formatCurrency(price),
    },
  ];

  const renderOverview = () => (
    <div>
      <Descriptions title="Información General" bordered style={{ marginBottom: 24 }}>
        <Descriptions.Item label="Nombre">{budget.name}</Descriptions.Item>
        <Descriptions.Item label="Proyecto">{budget.project?.name}</Descriptions.Item>
        <Descriptions.Item label="Cliente">{budget.project?.client_name}</Descriptions.Item>
        <Descriptions.Item label="Ubicación">{budget.project?.location}</Descriptions.Item>
        <Descriptions.Item label="Versión">{budget.version}</Descriptions.Item>
        <Descriptions.Item label="Estado">
          <span style={{ textTransform: 'capitalize' }}>{budget.status}</span>
        </Descriptions.Item>
        <Descriptions.Item label="Fecha de Creación">
          {new Date(budget.created_at).toLocaleDateString()}
        </Descriptions.Item>
      </Descriptions>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Monto Total"
              value={budget.final_amount}
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
              value={budget.profit_amount}
              prefix={<DollarOutlined />}
              precision={2}
              formatter={(value) => formatCurrency(value as number)}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Margen de Beneficio"
              value={budget.total_amount > 0 ? (budget.profit_amount / budget.total_amount) * 100 : 0}
              suffix="%"
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      <Space>
        <Button
          type="primary"
          icon={<CalculatorOutlined />}
          onClick={() => setShowCalculator(true)}
        >
          Calcular Presupuesto
        </Button>
        <Button icon={<DownloadOutlined />}>
          Exportar
        </Button>
      </Space>
    </div>
  );

  const renderItems = () => (
    <div>
      {Object.entries(chapters).map(([chapterKey, chapter]) => (
        <Card
          key={chapterKey}
          title={`${chapter.name} - ${formatCurrency(chapter.total)}`}
          style={{ marginBottom: 16 }}
        >
          <Table
            columns={columns}
            dataSource={chapter.items}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </Card>
      ))}
    </div>
  );

  const renderAnalysis = () => (
    <div>
      <Title level={4}>Análisis de Costos</Title>
      <Row gutter={16}>
        <Col span={12}>
          <Card title="Desglose de Costos">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Mano de Obra:</span>
                <span>{formatCurrency(budget.total_amount * 0.4)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Materiales:</span>
                <span>{formatCurrency(budget.total_amount * 0.5)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Equipo:</span>
                <span>{formatCurrency(budget.total_amount * 0.1)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                <span>Total:</span>
                <span>{formatCurrency(budget.total_amount)}</span>
              </div>
            </Space>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Estadísticas">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Número de Partidas:</span>
                <span>{budget.items?.length || 0}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Número de Capítulos:</span>
                <span>{Object.keys(chapters).length}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Promedio por Partida:</span>
                <span>
                  {formatCurrency(
                    (budget.items?.reduce((sum, item) => sum + item.total_price, 0) || 0) /
                      (budget.items?.length || 1)
                  )}
                </span>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );

  return (
    <Modal
      title={`Presupuesto: ${budget.name}`}
      open={visible}
      onCancel={onCancel}
      width={1200}
      footer={[
        <Button key="close" onClick={onCancel}>
          Cerrar
        </Button>,
      ]}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Resumen" key="overview">
          {renderOverview()}
        </TabPane>
        <TabPane tab="Partidas" key="items">
          {renderItems()}
        </TabPane>
        <TabPane tab="Análisis" key="analysis">
          {renderAnalysis()}
        </TabPane>
      </Tabs>

      {/* Modal para calculadora */}
      <BudgetCalculator
        visible={showCalculator}
        onCancel={() => setShowCalculator(false)}
        budgetId={budget.id}
        currentProfitMargin={budget.project?.profit_margin}
      />
    </Modal>
  );
};

export default BudgetViewer;