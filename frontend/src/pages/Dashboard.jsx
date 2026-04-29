import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, message, Spin, Input, Button, Space } from 'antd'
import { ArrowUpOutlined } from '@ant-design/icons'
import { dashboardAPI, transactionAPI } from '../services/api'

export default function Dashboard() {
  const today = new Date().toISOString().slice(0, 10)
  const [metrics, setMetrics] = useState(null)
  const [statusRows, setStatusRows] = useState([])
  const [volumeRows, setVolumeRows] = useState([])
  const [recentTx, setRecentTx] = useState([])
  const [statusDate, setStatusDate] = useState(today)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData(today)
  }, [])

  const fetchDashboardData = async (selectedDate = statusDate) => {
    setLoading(true)
    try {
      const [summaryRes, statusRes, volumeRes, txRes] = await Promise.all([
        dashboardAPI.getSummary().catch(() => ({ data: {} })),
        dashboardAPI.getStatus({ as_of: selectedDate }).catch(() => ({ data: [] })),
        dashboardAPI.getVolume().catch(() => ({ data: [] })),
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
      setStatusRows(Array.isArray(statusRes.data) ? statusRes.data : [])
      setVolumeRows(Array.isArray(volumeRes.data) ? volumeRes.data : [])
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

  const statusColumns = [
    { title: 'Status', dataIndex: 'status', key: 'status', width: 180 },
    { title: 'Count', dataIndex: 'count', key: 'count', width: 100 },
  ]

  const volumeColumns = [
    { title: 'Date', dataIndex: 'date', key: 'date', width: 140 },
    { title: 'Count', dataIndex: 'count', key: 'count', width: 100 },
    { title: 'Total Amount', dataIndex: 'total_amount', key: 'total_amount', width: 140 },
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

        <Row gutter={16} style={{ marginTop: '16px' }}>
          <Col xs={24} sm={12}>
            <Card className="card">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 12,
                }}
              >
                <div className="card-title" style={{ marginBottom: 0 }}>Status Breakdown</div>
                <Space>
                  <Input
                    size="small"
                    type="date"
                    value={statusDate}
                    onChange={(e) => setStatusDate(e.target.value)}
                    style={{ width: 150 }}
                  />
                  <Button size="small" type="primary" onClick={() => fetchDashboardData(statusDate)}>
                    Apply
                  </Button>
                  <Button
                    size="small"
                    onClick={() => {
                      setStatusDate(today)
                      fetchDashboardData(today)
                    }}
                  >
                    Today
                  </Button>
                </Space>
              </div>
              <Table
                dataSource={statusRows}
                columns={statusColumns}
                rowKey={(r) => r.status}
                size="small"
                bordered
                pagination={false}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12}>
            <Card className="card">
              <div className="card-title">Volume Trend</div>
              <Table
                dataSource={volumeRows}
                columns={volumeColumns}
                rowKey={(r) => r.date}
                size="small"
                bordered
                pagination={{ pageSize: 10 }}
              />
            </Card>
          </Col>
        </Row>
      </div>
    </Spin>
  )
}
