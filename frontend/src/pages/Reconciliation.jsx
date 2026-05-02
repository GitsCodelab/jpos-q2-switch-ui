import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Tabs, Statistic, Row, Col, message, Form, Select } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { reconciliationAPI } from '../services/api'

export default function Reconciliation() {
  const [issues, setIssues] = useState([])
  const [missing, setMissing] = useState([])
  const [reversalCandidates, setReversalCandidates] = useState([])
  const [filteredIssues, setFilteredIssues] = useState([])
  const [filteredMissing, setFilteredMissing] = useState([])
  const [filteredReversalCandidates, setFilteredReversalCandidates] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

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
      setFilteredIssues(Array.isArray(issuesRes.data) ? issuesRes.data : [])
      setFilteredMissing(Array.isArray(missingRes.data) ? missingRes.data : [])
      setFilteredReversalCandidates(Array.isArray(reversalRes.data) ? reversalRes.data : [])
      setSummary(summaryRes.data)
    } catch (error) {
      message.error('Failed to fetch reconciliation data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = () => {
    const { status, issue_type } = form.getFieldsValue()
    const match = (row) => {
      if (status && row.status !== status) return false
      if (issue_type && row.issue_type !== issue_type) return false
      return true
    }
    setFilteredIssues(issues.filter(match))
    setFilteredMissing(missing.filter(match))
    setFilteredReversalCandidates(reversalCandidates.filter(match))
  }

  const resetFilters = () => {
    form.resetFields()
    setFilteredIssues(issues)
    setFilteredMissing(missing)
    setFilteredReversalCandidates(reversalCandidates)
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
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      defaultSortOrder: 'descend',
      sorter: (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0),
      render: (v) => v ? new Date(v).toLocaleString() : '—',
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
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      defaultSortOrder: 'descend',
      sorter: (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0),
      render: (v) => v ? new Date(v).toLocaleString() : '—',
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
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      defaultSortOrder: 'descend',
      sorter: (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0),
      render: (v) => v ? new Date(v).toLocaleString() : '—',
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
          dataSource={filteredIssues}
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
          dataSource={filteredMissing}
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
          dataSource={filteredReversalCandidates}
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
          <Space>
            <Button
              type="primary"
              size="small"
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={fetchReconciliationData}
            >
              Refresh
            </Button>
          </Space>
        </div>
        <Form form={form} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item label="Status" name="status">
            <Select
              size="small"
              allowClear
              style={{ width: 180 }}
              options={[
                { value: 'REQUEST_RECEIVED', label: 'REQUEST_RECEIVED' },
                { value: 'TIMEOUT', label: 'TIMEOUT' },
                { value: 'AUTHORIZED', label: 'AUTHORIZED' },
                { value: 'REVERSAL_PENDING', label: 'REVERSAL_PENDING' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Issue" name="issue_type">
            <Select
              size="small"
              allowClear
              style={{ width: 200 }}
              options={[
                { value: 'MISSING_RESPONSE', label: 'MISSING_RESPONSE' },
                { value: 'REVERSAL_CANDIDATE', label: 'REVERSAL_CANDIDATE' },
                { value: 'TIMEOUT', label: 'TIMEOUT' },
                { value: 'UNKNOWN', label: 'UNKNOWN' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" size="small" onClick={applyFilters}>Apply</Button>
              <Button size="small" onClick={resetFilters}>Reset</Button>
            </Space>
          </Form.Item>
        </Form>
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}
