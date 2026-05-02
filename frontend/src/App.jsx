import { useState, useEffect, lazy, Suspense } from 'react'
import { Layout, Menu, Button, Dropdown, Avatar, Space, Spin } from 'antd'
import { UserOutlined, LogoutOutlined, DashboardOutlined, UnorderedListOutlined, ReconciliationOutlined, DollarOutlined, ApartmentOutlined, DeploymentUnitOutlined, AlertOutlined, ExperimentOutlined } from '@ant-design/icons'

const Transactions = lazy(() => import('./pages/Transactions'))
const Reconciliation = lazy(() => import('./pages/Reconciliation'))
const Settlement = lazy(() => import('./pages/Settlement'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const NetSettlement = lazy(() => import('./pages/NetSettlement'))
const Routing = lazy(() => import('./pages/Routing'))
const Fraud = lazy(() => import('./pages/Fraud'))
const SwitchTesting = lazy(() => import('./pages/SwitchTesting'))
const Login = lazy(() => import('./pages/Login'))

const { Header, Sider, Content } = Layout

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [collapsed, setCollapsed] = useState(false)
  const [username, setUsername] = useState(localStorage.getItem('username') || null)
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'))

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const user = localStorage.getItem('username')
    setIsAuthenticated(!!token)
    setUsername(user)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('username')
    setUsername(null)
    setIsAuthenticated(false)
    setCurrentPage('dashboard')
  }

  if (!isAuthenticated) {
    return (
      <Suspense fallback={<div style={{ padding: 24, textAlign: 'center' }}><Spin /></div>}>
        <Login />
      </Suspense>
    )
  }

  const userMenu = {
    items: [
      {
        key: 'profile',
        label: `Logged in as ${username || 'User'}`,
        disabled: true,
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        label: 'Logout',
        icon: <LogoutOutlined />,
        onClick: handleLogout,
      },
    ],
  }

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: 'transactions',
      icon: <UnorderedListOutlined />,
      label: 'Transactions',
    },
    {
      key: 'reconciliation',
      icon: <ReconciliationOutlined />,
      label: 'Reconciliation',
    },
    {
      key: 'settlement',
      icon: <DollarOutlined />,
      label: 'Settlement',
    },
    {
      key: 'net-settlement',
      icon: <ApartmentOutlined />,
      label: 'Net Settlement',
    },
    {
      key: 'routing',
      icon: <DeploymentUnitOutlined />,
      label: 'Routing',
    },
    {
      key: 'fraud',
      icon: <AlertOutlined />,
      label: 'Fraud',
    },
    {
      key: 'switch-testing',
      icon: <ExperimentOutlined />,
      label: 'Switch Testing',
    },
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'transactions':
        return <Transactions />
      case 'reconciliation':
        return <Reconciliation />
      case 'settlement':
        return <Settlement />
      case 'net-settlement':
        return <NetSettlement />
      case 'routing':
        return <Routing />
      case 'fraud':
        return <Fraud />
      case 'switch-testing':
        return <SwitchTesting onNavigate={(page) => setCurrentPage(page)} />
      default:
        return <Dashboard />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={220}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        style={{
          background: '#ffffff',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div
          style={{
            padding: '16px',
            fontSize: '14px',
            fontWeight: '600',
            color: '#0a6ed1',
            textAlign: 'center',
          }}
        >
          {!collapsed && (
            <Space>
              <img src="https://jpos.org/img/logo.svg" alt="jPOS" width="20" height="20" />
              <span>jPOS Switch</span>
            </Space>
          )}
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[currentPage]}
          onClick={(e) => setCurrentPage(e.key)}
          items={menuItems}
          style={{ border: 'none' }}
        />
      </Sider>

      <Layout>
        <Header
          style={{
            background: '#ffffff',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingRight: '24px',
          }}
        >
          <div style={{ fontSize: '16px', fontWeight: '600', color: '#1d2d3e' }}>
            jPos - UX 
          </div>
          {username ? (
            <Dropdown menu={userMenu}>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span style={{ fontSize: '12px', color: '#1d2d3e' }}>{username}</span>
              </Space>
            </Dropdown>
          ) : (
            <Button
              type="primary"
              size="small"
              onClick={() => window.location.href = '/login'}
            >
              Login
            </Button>
          )}
        </Header>

        <Content style={{ margin: '16px', minHeight: 'calc(100vh - 64px)' }}>
          <Suspense fallback={<div style={{ padding: 24, textAlign: 'center' }}><Spin /></div>}>
            {renderPage()}
          </Suspense>
        </Content>
      </Layout>
    </Layout>
  )
}
