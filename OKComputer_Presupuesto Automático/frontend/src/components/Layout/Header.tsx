import React from 'react';
import { Layout, Avatar, Dropdown, Menu, Space, Typography } from 'antd';
import { UserOutlined, LogoutOutlined, SettingOutlined } from '@ant-design/icons';
import styled from 'styled-components';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const StyledHeader = styled(AntHeader)`
  background: #fff;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  position: fixed;
  top: 0;
  right: 0;
  left: 200px;
  z-index: 100;
`;

const LogoSection = styled.div`
  display: flex;
  align-items: center;
`;

const Logo = styled.div`
  font-size: 20px;
  font-weight: bold;
  color: #2E4057;
  margin-right: 20px;
`;

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Header: React.FC = () => {
  const menu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />}>
        Mi Perfil
      </Menu.Item>
      <Menu.Item key="settings" icon={<SettingOutlined />}>
        Configuración
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />}>
        Cerrar Sesión
      </Menu.Item>
    </Menu>
  );

  return (
    <StyledHeader>
      <LogoSection>
        <Logo>Sistema de Presupuestos</Logo>
      </LogoSection>
      
      <UserSection>
        <Text type="secondary">Bienvenido, Usuario</Text>
        <Dropdown overlay={menu} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Avatar size="small" icon={<UserOutlined />} />
          </Space>
        </Dropdown>
      </UserSection>
    </StyledHeader>
  );
};

export default Header;