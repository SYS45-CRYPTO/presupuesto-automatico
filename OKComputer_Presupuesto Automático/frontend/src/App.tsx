import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import styled from 'styled-components';

// Componentes
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Budgets from './pages/Budgets';
import PriceBooks from './pages/PriceBooks';
import Reports from './pages/Reports';

const { Content } = Layout;

const AppLayout = styled(Layout)`
  min-height: 100vh;
`;

const MainContent = styled(Content)`
  margin: 24px 16px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const App: React.FC = () => {
  return (
    <AppLayout>
      <Header />
      <Layout>
        <Sidebar />
        <Layout style={{ marginLeft: 200 }}>
          <MainContent>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/budgets" element={<Budgets />} />
              <Route path="/price-books" element={<PriceBooks />} />
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </MainContent>
        </Layout>
      </Layout>
    </AppLayout>
  );
};

export default App;