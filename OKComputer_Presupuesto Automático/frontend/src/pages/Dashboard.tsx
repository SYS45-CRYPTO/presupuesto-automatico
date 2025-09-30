import React from 'react';
import { Row, Col, Card, Statistic, Typography, Table, Tag } from 'antd';
import {
  DollarOutlined,
  ProjectOutlined,
  CalculatorOutlined,
  TrendingUpOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useDashboardMetrics } from '../hooks/useDashboard';
import { formatCurrency } from '../utils/formatters';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const { data: metrics, isLoading } = useDashboardMetrics();

  // Datos de ejemplo para gráficos
  const monthlyData = [
    { month: 'Ene', value: 40000 },
    { month: 'Feb', value: 65000 },
    { month: 'Mar', value: 85000 },
    { month: 'Abr', value: 120000 },
    { month: 'May', value: 95000 },
    { month: 'Jun', value: 150000 },
  ];

  const categoryData = [
    { name: 'Estructura', value: 45, color: '#2E4057' },
    { name: 'Acabados', value: 30, color: '#5D6D7E' },
    { name: 'Instalaciones', value: 15, color: '#7F8C8D' },
    { name: 'Otros', value: 10, color: '#BDC3C7' },
  ];

  const recentBudgets = [
    {
      key: '1',
      name: 'Casa Residencial - Proyecto A',
      client: 'Juan Pérez',
      amount: 125000,
      status: 'approved',
      date: '2024-01-15',
    },
    {
      key: '2',
      name: 'Oficinas Comerciales - Proyecto B',
      client: 'Empresa XYZ',
      amount: 85000,
      status: 'draft',
      date: '2024-01-14',
    },
    {
      key: '3',
      name: 'Remodelación - Proyecto C',
      client: 'María García',
      amount: 45000,
      status: 'approved',
      date: '2024-01-13',
    },
  ];

  const columns = [
    {
      title: 'Presupuesto',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Cliente',
      dataIndex: 'client',
      key: 'client',
    },
    {
      title: 'Monto',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => formatCurrency(amount),
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'approved' ? 'green' : 'orange'}>
          {status === 'approved' ? 'Aprobado' : 'Borrador'}
        </Tag>
      ),
    },
    {
      title: 'Fecha',
      dataIndex: 'date',
      key: 'date',
    },
  ];

  return (
    <div>
      <Title level={2} style={{ marginBottom: 24 }}>
        Dashboard
      </Title>

      {/* Métricas principales */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Proyectos Totales"
              value={metrics?.total_projects || 12}
              prefix={<ProjectOutlined />}
              loading={isLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Presupuestos Activos"
              value={metrics?.active_budgets || 8}
              prefix={<CalculatorOutlined />}
              loading={isLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Valor Total"
              value={metrics?.total_amount || 850000}
              prefix={<DollarOutlined />}
              precision={0}
              formatter={(value) => formatCurrency(value as number)}
              loading={isLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Margen Promedio"
              value={metrics?.average_profit_margin || 18.5}
              prefix={<TrendingUpOutlined />}
              suffix="%"
              precision={1}
              loading={isLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* Gráficos */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="Tendencia Mensual" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value as number)} />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#2E4057" 
                  strokeWidth={2}
                  dot={{ fill: '#2E4057', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Distribución por Categoría" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Presupuestos recientes */}
      <Row>
        <Col span={24}>
          <Card title="Presupuestos Recientes">
            <Table
              columns={columns}
              dataSource={recentBudgets}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;