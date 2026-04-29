import { useState } from 'react'
import { Form, Input, Button, Card, message, Spin } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authAPI } from '../services/api'

export default function Login() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleLogin = async (values) => {
    setLoading(true)
    try {
      const response = await authAPI.login(values.username, values.password)
      const { access_token } = response.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('username', values.username)
      message.success('Login successful')
      window.location.href = '/'
    } catch (error) {
      message.error(error.response?.data?.message || 'Login failed')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f6f7',
      }}
    >
      <Spin spinning={loading}>
        <Card
          style={{
            width: 400,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div
            style={{
              textAlign: 'center',
              marginBottom: '24px',
            }}
          >
            <div
              style={{
                fontSize: '20px',
                fontWeight: '600',
                color: '#0a6ed1',
                marginBottom: '8px',
              }}
            >
              jPOS Switch
            </div>
            <div style={{ fontSize: '12px', color: '#999999' }}>
              Core Banking Dashboard
            </div>
          </div>

          <Form
            form={form}
            layout="vertical"
            onFinish={handleLogin}
          >
            <Form.Item
              label="Username"
              name="username"
              rules={[
                { required: true, message: 'Please enter your username' },
              ]}
            >
              <Input
                size="small"
                placeholder="admin"
                prefix={<UserOutlined />}
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              label="Password"
              name="password"
              rules={[
                { required: true, message: 'Please enter your password' },
              ]}
            >
              <Input.Password
                size="small"
                placeholder="password"
                prefix={<LockOutlined />}
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                block
                size="small"
                htmlType="submit"
                loading={loading}
              >
                Sign In
              </Button>
            </Form.Item>
          </Form>

          <div style={{ fontSize: '11px', color: '#999999', textAlign: 'center' }}>
            Demo credentials: admin / admin123
          </div>
        </Card>
      </Spin>
    </div>
  )
}
