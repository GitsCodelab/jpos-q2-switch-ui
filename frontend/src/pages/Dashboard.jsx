import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, message, Spin } from 'antd'
import { ArrowUpOutlined } from '@ant-design/icons'
import { dashboardAPI, transactionAPI } from '../services/api'

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [recentTx, setRecentTx] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const [summaryRes, statusRes, txRes] = await Promise.all([
        dashboardAPI.getSummary().catch(() => ({ data: {} })),
        dashboardAPI.getStatus().catch(() => ({ data: [] })),
        transactionAPI.list({ limit: 10 }).catch(() => ({ data: [] })),
      ])

      const statusMap = {}
      for (const item of statusRes.data || []) {
        statusMap[item.status] = item.count
      }

      const computed = {
        ...summaryRes.data,
        approved: statusMap.APPROVED || 0,
        pending: statusMap.REQUEST_RECEIVED || statusMap.PENDING || 0,
        failed: (statusMap.DECLINED || 0) + (statusMap.SECURITY_DECLINE || 0) + (statusMap.TIMEOUT || 0),
      }
      setMetrics(computed)
      setRecentTx(Array.isArray(txRes.data) ? txRes.data : [])
    } catch (error) {
      message.error('Failed to load dashboard data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: 'Transaction ID',
      dataIndex: 'id',
      key: 'id',
      width: 140,
      render: (text) => <span style={{ fontSize: '11px' }}>{text}</span>,
    },
    {
      title: 'STAN',
      dataIndex: 'stan',
      key: 'stan',
      width: 70,
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      align: 'right',
      render: (text) => `$${parseFloat(text).toFixed(2)}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const colors = {
          APPROVED: '#107e3e',
          REJECTED: '#bb0000',
          PENDING: '#e3a821',
        }
        return (
          <span style={{ color: colors[status] || '#1d2d3e', fontWeight: '500' }}>
            {status}
          </span>
        )
      },
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (text) => new Date(text).toLocaleString(),
    },
  ]

  return (
    <Spin spinning={loading}>
      <div>
        {/* Top Metrics */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Total Transactions"
                value={metrics?.total_transactions || 0}
                prefix={<ArrowUpOutlined style={{ color: '#0a6ed1' }} />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Approved"
                value={metrics?.approved || 0}
                valueStyle={{ color: '#107e3e' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Pending"
                value={metrics?.pending || 0}
                valueStyle={{ color: '#e3a821' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Failed/Rejected"
                value={metrics?.failed || 0}
                valueStyle={{ color: '#bb0000' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Additional Metrics */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Total Amount"
                value={`$${parseFloat(metrics?.total_amount || 0).toFixed(2)}`}
                valueStyle={{ fontSize: '16px' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Avg Amount"
                value={`$${parseFloat(metrics?.avg_amount || 0).toFixed(2)}`}
                valueStyle={{ fontSize: '16px' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Settlement Batches"
                value={metrics?.settlement_batches || 0}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="card" style={{ textAlign: 'center' }}>
              <Statistic
                title="Recon Issues"
                value={metrics?.recon_issues || 0}
                valueStyle={{ color: '#bb0000' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Recent Transactions */}
        <Card className="card">
          <div className="card-title">Recent Transactions</div>
          <Table
            dataSource={recentTx}
            columns={columns}
            rowKey="id"
            size="small"
            bordered
            pagination={false}
          />
        </Card>
      </div>
    </Spin>
  )
}
