import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  ProjectOutlined,
  CalculatorOutlined,
  BookOutlined,
  BarChartOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import styled from 'styled-components';

const { Sider } = Layout;

const StyledSider = styled(Sider)`
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background: #2E4057;
  
  .ant-layout-sider-trigger {
    background: #1a2a3a;
  }
  
  .ant-menu {
    background: transparent;
    border: none;
  }
  
  .ant-menu-item {
    color: rgba(255, 255, 255, 0.8);
    
    &:hover {
      color: white;
      background: rgba(255, 255, 255, 0.1);
    }
    
    &.ant-menu-item-selected {
      color: white;
      background: rgba(255, 255, 255, 0.2);
    }
  }
`;

const LogoContainer = styled.div`
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/projects',
      icon: <ProjectOutlined />,
      label: 'Proyectos',
    },
    {
      key: '/budgets',
      icon: <CalculatorOutlined />,
      label: 'Presupuestos',
    },
    {
      key: '/price-books',
      icon: <BookOutlined />,
      label: 'Libros de Precios',
    },
    {
      key: '/reports',
      icon: <BarChartOutlined />,
      label: 'Reportes',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <StyledSider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      trigger={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
      width={200}
    >
      <LogoContainer>
        {!collapsed && 'Constructora'}
      </LogoContainer>
      
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ marginTop: '16px' }}
      />
    </StyledSider>
  );
};

export default Sidebar;