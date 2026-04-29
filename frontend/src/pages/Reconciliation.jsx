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
      setIssues(Array.isArray(issuesRes.data) ? issuesRes.data : [])
      setMissing(Array.isArray(missingRes.data) ? missingRes.data : [])
      setReversalCandidates(Array.isArray(reversalRes.data) ? reversalRes.data : [])
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
      dataIndex: 'stan',
      key: 'stan',
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
      title: 'RRN',
      dataIndex: 'rrn',
      key: 'rrn',
    },
  ]

  const missingColumns = [
    {
      title: 'Transaction ID',
      dataIndex: 'stan',
      key: 'stan',
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
      title: 'Issue Type',
      dataIndex: 'issue_type',
      key: 'issue_type',
      width: 100,
    },
  ]

  const reversalColumns = [
    {
      title: 'Transaction ID',
      dataIndex: 'stan',
      key: 'stan',
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
      title: 'Retry Count',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 80,
    },
    {
      title: 'Issue Type',
      dataIndex: 'issue_type',
      key: 'issue_type',
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
              value={summary.missing_responses || 0}
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
            <Statistic title="Open Issues" value={summary.total_issues || 0} />
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
          rowKey={(r) => `${r.stan}-${r.rrn}-${r.issue_type}`}
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
          rowKey={(r) => `${r.stan}-${r.rrn}-${r.issue_type}`}
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
          rowKey={(r) => `${r.stan}-${r.rrn}-${r.issue_type}`}
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
