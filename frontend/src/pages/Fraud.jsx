import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  message,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
} from 'antd'
import { fraudAPI } from '../services/api'

const severityColor = {
  LOW: 'blue',
  MEDIUM: 'orange',
  HIGH: 'red',
}

const statusColor = {
  OPEN: 'red',
  ACKED: 'blue',
  ESCALATED: 'orange',
  CLOSED: 'green',
}

export default function Fraud() {
  const [loading, setLoading] = useState(false)
  const [dashboard, setDashboard] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [rules, setRules] = useState([])
  const [blacklist, setBlacklist] = useState([])
  const [cases, setCases] = useState([])
  const [flaggedTransactions, setFlaggedTransactions] = useState([])
  const [checkResult, setCheckResult] = useState(null)

  const [ruleForm] = Form.useForm()
  const [blacklistForm] = Form.useForm()
  const [checkForm] = Form.useForm()
  const [caseForm] = Form.useForm()

  const loadAll = async () => {
    setLoading(true)
    const labels = ['dashboard', 'alerts', 'rules', 'blacklist', 'cases', 'flagged-transactions']
    const requests = [
      fraudAPI.getDashboard(),
      fraudAPI.getAlerts(),
      fraudAPI.getRules(),
      fraudAPI.getBlacklist(),
      fraudAPI.getCases(),
      fraudAPI.getFlaggedTransactions(),
    ]

    try {
      const results = await Promise.allSettled(requests)
      const failedSections = []

      const [dashRes, alertRes, ruleRes, blRes, caseRes, txRes] = results

      if (dashRes.status === 'fulfilled') {
        setDashboard(dashRes.value.data)
      } else {
        setDashboard(null)
        failedSections.push(labels[0])
      }

      if (alertRes.status === 'fulfilled') {
        setAlerts(alertRes.value.data)
      } else {
        setAlerts([])
        failedSections.push(labels[1])
      }

      if (ruleRes.status === 'fulfilled') {
        setRules(ruleRes.value.data)
      } else {
        setRules([])
        failedSections.push(labels[2])
      }

      if (blRes.status === 'fulfilled') {
        setBlacklist(blRes.value.data)
      } else {
        setBlacklist([])
        failedSections.push(labels[3])
      }

      if (caseRes.status === 'fulfilled') {
        setCases(caseRes.value.data)
      } else {
        setCases([])
        failedSections.push(labels[4])
      }

      if (txRes.status === 'fulfilled') {
        setFlaggedTransactions(txRes.value.data)
      } else {
        setFlaggedTransactions([])
        failedSections.push(labels[5])
      }

      if (failedSections.length > 0) {
        message.warning(`Some fraud sections could not load: ${failedSections.join(', ')}`)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  const dashboardCards = useMemo(() => {
    if (!dashboard) {
      return []
    }
    return [
      { title: 'Total Alerts', value: dashboard.total_alerts },
      { title: 'Open Alerts', value: dashboard.open_alerts },
      { title: 'Flagged', value: dashboard.flagged_count },
      { title: 'Declined', value: dashboard.declined_count },
      { title: 'Fraud Rate %', value: dashboard.fraud_rate },
    ]
  }, [dashboard])

  const handleAlertAction = async (id, action) => {
    try {
      await fraudAPI.actionAlert(id, { action })
      message.success(`Alert ${id} updated: ${action}`)
      await loadAll()
    } catch (error) {
      message.error(error?.response?.data?.message || 'Failed to update alert')
    }
  }

  const createRule = async (values) => {
    try {
      await fraudAPI.createRule(values)
      message.success('Fraud rule created')
      ruleForm.resetFields()
      await loadAll()
    } catch (error) {
      message.error(error?.response?.data?.message || 'Failed to create rule')
    }
  }

  const createBlacklist = async (values) => {
    try {
      await fraudAPI.createBlacklist(values)
      message.success('Blacklist entry created')
      blacklistForm.resetFields()
      await loadAll()
    } catch (error) {
      message.error(error?.response?.data?.message || 'Failed to create blacklist entry')
    }
  }

  const runCheck = async (values) => {
    try {
      const response = await fraudAPI.runCheck(values)
      setCheckResult(response.data)
      if (response.data.decision === 'DECLINE') {
        message.warning('Fraud check decision: DECLINE')
      } else if (response.data.decision === 'FLAG') {
        message.info('Fraud check decision: FLAG')
      } else {
        message.success('Fraud check decision: APPROVE')
      }
      await loadAll()
    } catch (error) {
      message.error(error?.response?.data?.message || 'Failed to run fraud check')
    }
  }

  const createCase = async (values) => {
    try {
      await fraudAPI.createCase(values)
      message.success('Fraud case created')
      caseForm.resetFields()
      await loadAll()
    } catch (error) {
      message.error(error?.response?.data?.message || 'Failed to create case')
    }
  }

  const alertColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'STAN', dataIndex: 'stan', key: 'stan', width: 120 },
    { title: 'RRN', dataIndex: 'rrn', key: 'rrn', width: 160 },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 120,
      render: (value) => <Tag color={severityColor[value] || 'default'}>{value}</Tag>,
    },
    { title: 'Score', dataIndex: 'risk_score', key: 'risk_score', width: 100 },
    { title: 'Decision', dataIndex: 'decision', key: 'decision', width: 120 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (value) => <Tag color={statusColor[value] || 'default'}>{value}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 220,
      render: (_, row) => (
        <Space>
          <Button size="small" onClick={() => handleAlertAction(row.id, 'ACK')}>ACK</Button>
          <Button size="small" onClick={() => handleAlertAction(row.id, 'ESCALATE')}>Escalate</Button>
          <Button size="small" danger onClick={() => handleAlertAction(row.id, 'CLOSE')}>Close</Button>
        </Space>
      ),
    },
  ]

  const ruleColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'rule_type', key: 'rule_type' },
    { title: 'Threshold', dataIndex: 'threshold', key: 'threshold' },
    { title: 'Window (sec)', dataIndex: 'window_seconds', key: 'window_seconds' },
    { title: 'Weight', dataIndex: 'weight', key: 'weight' },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value) => (value ? <Tag color="green">ACTIVE</Tag> : <Tag>OFF</Tag>),
    },
  ]

  const blacklistColumns = [
    { title: 'Type', dataIndex: 'entry_type', key: 'entry_type', width: 120 },
    { title: 'Value', dataIndex: 'value', key: 'value' },
    { title: 'Reason', dataIndex: 'reason', key: 'reason' },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (value) => (value ? <Tag color="green">YES</Tag> : <Tag>NO</Tag>),
    },
  ]

  const caseColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: 'Alert ID', dataIndex: 'alert_id', key: 'alert_id', width: 100 },
    { title: 'Status', dataIndex: 'status', key: 'status', width: 120 },
    { title: 'Assigned To', dataIndex: 'assigned_to', key: 'assigned_to', width: 140 },
    { title: 'Summary', dataIndex: 'summary', key: 'summary' },
  ]

  const flaggedTransactionColumns = [
    { title: 'Alert ID', dataIndex: 'alert_id', key: 'alert_id', width: 100 },
    { title: 'STAN', dataIndex: 'stan', key: 'stan', width: 120 },
    { title: 'RRN', dataIndex: 'rrn', key: 'rrn', width: 160 },
    { title: 'Decision', dataIndex: 'decision', key: 'decision', width: 120 },
    { title: 'Risk Score', dataIndex: 'risk_score', key: 'risk_score', width: 100 },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 120,
      render: (value) => <Tag color={severityColor[value] || 'default'}>{value}</Tag>,
    },
    { title: 'Terminal', dataIndex: 'terminal_id', key: 'terminal_id', width: 120 },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', width: 100 },
    { title: 'Rules Triggered', dataIndex: 'rule_hits', key: 'rule_hits' },
  ]

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card title="Fraud Management" loading={loading}>
        <Row gutter={[16, 16]}>
          {dashboardCards.map((item) => (
            <Col key={item.title} xs={24} sm={12} md={8} lg={4}>
              <Card size="small">
                <Statistic title={item.title} value={item.value} />
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      <Tabs
        items={[
          {
            key: 'alerts',
            label: 'Alerts',
            children: (
              <Card>
                <Table
                  rowKey="id"
                  columns={alertColumns}
                  dataSource={alerts}
                  size="small"
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 1100 }}
                />
              </Card>
            ),
          },
          {
            key: 'rules',
            label: 'Rules',
            children: (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Create Rule">
                  <Form form={ruleForm} layout="inline" onFinish={createRule}>
                    <Form.Item name="name" rules={[{ required: true }]}>
                      <Input placeholder="Rule Name" />
                    </Form.Item>
                    <Form.Item name="rule_type" rules={[{ required: true }]}>
                      <Select
                        style={{ width: 160 }}
                        options={[
                          { value: 'HIGH_AMOUNT', label: 'HIGH_AMOUNT' },
                          { value: 'VELOCITY', label: 'VELOCITY' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item name="threshold" rules={[{ required: true }]}>
                      <InputNumber placeholder="Threshold" min={1} />
                    </Form.Item>
                    <Form.Item name="window_seconds">
                      <InputNumber placeholder="Window sec" min={1} />
                    </Form.Item>
                    <Form.Item name="weight" initialValue={50}>
                      <InputNumber placeholder="Weight" min={0} max={100} />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Create</Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card title="Active Rules">
                  <Table rowKey="id" columns={ruleColumns} dataSource={rules} size="small" pagination={{ pageSize: 10 }} />
                </Card>
              </Space>
            ),
          },
          {
            key: 'blacklist',
            label: 'Blacklist',
            children: (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Create Blacklist Entry">
                  <Form form={blacklistForm} layout="inline" onFinish={createBlacklist}>
                    <Form.Item name="entry_type" rules={[{ required: true }]}>
                      <Select
                        style={{ width: 140 }}
                        options={[
                          { value: 'TERMINAL', label: 'TERMINAL' },
                          { value: 'BIN', label: 'BIN' },
                          { value: 'PAN', label: 'PAN' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item name="value" rules={[{ required: true }]}>
                      <Input placeholder="Value" />
                    </Form.Item>
                    <Form.Item name="reason">
                      <Input placeholder="Reason" />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Add</Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card title="Blacklist Entries">
                  <Table rowKey="id" columns={blacklistColumns} dataSource={blacklist} size="small" pagination={{ pageSize: 10 }} />
                </Card>
              </Space>
            ),
          },
          {
            key: 'check',
            label: 'Check',
            children: (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Run Fraud Check">
                  <Form form={checkForm} layout="inline" onFinish={runCheck}>
                    <Form.Item name="amount" rules={[{ required: true }]}>
                      <InputNumber min={1} placeholder="Amount (minor units)" />
                    </Form.Item>
                    <Form.Item name="terminal_id">
                      <Input placeholder="Terminal ID" />
                    </Form.Item>
                    <Form.Item name="pan">
                      <Input placeholder="PAN" />
                    </Form.Item>
                    <Form.Item name="stan">
                      <Input placeholder="STAN" />
                    </Form.Item>
                    <Form.Item name="rrn">
                      <Input placeholder="RRN" />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Check</Button>
                    </Form.Item>
                  </Form>
                </Card>
                {checkResult && (
                  <Alert
                    type={checkResult.decision === 'DECLINE' ? 'error' : checkResult.decision === 'FLAG' ? 'warning' : 'success'}
                    message={`Decision: ${checkResult.decision}`}
                    description={`Score=${checkResult.risk_score}, Severity=${checkResult.severity}, Triggers=${checkResult.triggers.join(', ') || 'None'}`}
                    showIcon
                  />
                )}
              </Space>
            ),
          },
          {
            key: 'cases',
            label: 'Cases',
            children: (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Create Case">
                  <Form form={caseForm} layout="inline" onFinish={createCase}>
                    <Form.Item name="alert_id">
                      <InputNumber min={1} placeholder="Alert ID" />
                    </Form.Item>
                    <Form.Item name="assigned_to">
                      <Input placeholder="Assigned to" />
                    </Form.Item>
                    <Form.Item name="summary" rules={[{ required: true }]}>
                      <Input placeholder="Summary" style={{ width: 280 }} />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Create</Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card title="Case Queue">
                  <Table rowKey="id" columns={caseColumns} dataSource={cases} size="small" pagination={{ pageSize: 10 }} />
                </Card>
              </Space>
            ),
          },
          {
            key: 'transactions',
            label: 'Transactions',
            children: (
              <Card title="Flagged Transactions">
                <Table
                  rowKey="alert_id"
                  columns={flaggedTransactionColumns}
                  dataSource={flaggedTransactions}
                  size="small"
                  pagination={{ pageSize: 10 }}
                  scroll={{ x: 1200 }}
                />
              </Card>
            ),
          },
        ]}
      />
    </Space>
  )
}
