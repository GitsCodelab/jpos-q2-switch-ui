import { useState, useEffect } from 'react'
import { Layout, Menu, Button, Dropdown, Avatar, Space } from 'antd'
import { UserOutlined, LogoutOutlined, DashboardOutlined, UnorderedListOutlined, ReconciliationOutlined, DollarOutlined } from '@ant-design/icons'
import Transactions from './pages/Transactions'
import Reconciliation from './pages/Reconciliation'
import Settlement from './pages/Settlement'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'

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
    return <Login />
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
          {!collapsed && 'jPOS Switch'}
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
            Core Banking Dashboard
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
          {renderPage()}
        </Content>
      </Layout>
    </Layout>
  )
}
