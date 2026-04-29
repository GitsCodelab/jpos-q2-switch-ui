import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tabs, Statistic, Row, Col, message } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { reconciliationAPI } from '../services/api'

export default function Reconciliation() {
  const [issues, setIssues] = useState([])
  const [missing, setMissing] = useState([])
  const [reversalCandidates, setReversalCandidates] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchReconciliationData()
  }, [])

  const fetchReconciliationData = async () => {
    setLoading(true)
    try {
      const [issuesRes, missingRes, reversalRes, summaryRes] = await Promise.all([
        reconciliationAPI.getIssues(),
        reconciliationAPI.getMissing(),
        reconciliationAPI.getReversalCandidates(),
        reconciliationAPI.getSummary(),
      ])
      setIssues(issuesRes.data.issues || [])
      setMissing(missingRes.data.missing || [])
      setReversalCandidates(reversalRes.data.candidates || [])
      setSummary(summaryRes.data)
    } catch (error) {
      message.error('Failed to fetch reconciliation data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const issuesColumns = [
    {
      title: 'Transaction ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 150,
      render: (text) => <span style={{ fontSize: '11px' }}>{text}</span>,
    },
    {
      title: 'Issue Type',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 120,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
    },
    {
      title: 'Retry Count',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 80,
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
    },
  ]

  const missingColumns = [
    {
      title: 'Transaction ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 150,
      render: (text) => <span style={{ fontSize: '11px' }}>{text}</span>,
    },
    {
      title: 'STAN',
      dataIndex: 'stan',
      key: 'stan',
      width: 100,
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (text) => `$${parseFloat(text).toFixed(2)}`,
    },
    {
      title: 'Missing In',
      dataIndex: 'missing_in',
      key: 'missing_in',
      width: 100,
    },
  ]

  const reversalColumns = [
    {
      title: 'Transaction ID',
      dataIndex: 'transaction_id',
      key: 'transaction_id',
      width: 150,
      render: (text) => <span style={{ fontSize: '11px' }}>{text}</span>,
    },
    {
      title: 'Original STAN',
      dataIndex: 'stan',
      key: 'stan',
      width: 100,
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      render: (text) => `$${parseFloat(text).toFixed(2)}`,
    },
    {
      title: 'Retry Count',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 80,
    },
    {
      title: 'Last Response',
      dataIndex: 'response_code',
      key: 'response_code',
      width: 100,
    },
  ]

  const tabItems = [
    {
      key: 'summary',
      label: 'Summary',
      children: summary && (
        <Row gutter={16}>
          <Col xs={12} sm={6}>
            <Statistic
              title="Total Issues"
              value={summary.total_issues || 0}
              valueStyle={{ color: '#bb0000' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Missing Transactions"
              value={summary.missing_transactions || 0}
              valueStyle={{ color: '#e3a821' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Reversal Candidates"
              value={summary.reversal_candidates || 0}
              valueStyle={{ color: '#0a6ed1' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Total Amount at Risk"
              value={`$${parseFloat(summary.total_amount_at_risk || 0).toFixed(2)}`}
            />
          </Col>
        </Row>
      ),
    },
    {
      key: 'issues',
      label: `Issues (${issues.length})`,
      children: (
        <Table
          dataSource={issues}
          columns={issuesColumns}
          rowKey="transaction_id"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      ),
    },
    {
      key: 'missing',
      label: `Missing Transactions (${missing.length})`,
      children: (
        <Table
          dataSource={missing}
          columns={missingColumns}
          rowKey="transaction_id"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      ),
    },
    {
      key: 'reversals',
      label: `Reversal Candidates (${reversalCandidates.length})`,
      children: (
        <Table
          dataSource={reversalCandidates}
          columns={reversalColumns}
          rowKey="transaction_id"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      ),
    },
  ]

  return (
    <div>
      <Card className="card">
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <div className="card-title" style={{ marginBottom: 0 }}>
            Reconciliation Dashboard
          </div>
          <Button
            type="primary"
            size="small"
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={fetchReconciliationData}
          >
            Refresh
          </Button>
        </div>
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}
