import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Timeline,
  Typography,
} from 'antd'
import { fraudAPI } from '../services/api'

const { Text } = Typography

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
  ACTIVE: 'green',
  DEACTIVATED: 'default',
  INVESTIGATING: 'purple',
  BLOCKED: 'volcano',
  APPROVED: 'cyan',
}

const actionColor = {
  FLAG: 'orange',
  DECLINE: 'red',
  BLOCK: 'volcano',
}

export default function Fraud() {
  const [loading, setLoading] = useState(false)
  const [dashboard, setDashboard] = useState(null)
  const [trends, setTrends] = useState([])
  const [breakdown, setBreakdown] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [rules, setRules] = useState([])
  const [blacklist, setBlacklist] = useState([])
  const [cases, setCases] = useState([])
  const [flaggedTransactions, setFlaggedTransactions] = useState([])
  const [auditLog, setAuditLog] = useState([])
  const [checkResult, setCheckResult] = useState(null)

  const [timelineVisible, setTimelineVisible] = useState(false)
  const [timelineCase, setTimelineCase] = useState(null)
  const [timelineEntries, setTimelineEntries] = useState([])

  const [ruleForm] = Form.useForm()
  const [blacklistForm] = Form.useForm()
  const [checkForm] = Form.useForm()
  const [caseForm] = Form.useForm()

  const loadAll = async () => {
    setLoading(true)
    const requests = [
      fraudAPI.getDashboard(),
      fraudAPI.getAlerts(),
      fraudAPI.getRules(),
      fraudAPI.getBlacklist(),
      fraudAPI.getCases(),
      fraudAPI.getFlaggedTransactions(),
      fraudAPI.getDashboardTrends(),
      fraudAPI.getDashboardBreakdown(),
      fraudAPI.getAuditLog().catch(() => ({ data: [] })),
    ]

    try {
      const results = await Promise.allSettled(requests)
      const failed = []
      const labels = ['dashboard', 'alerts', 'rules', 'blacklist', 'cases', 'flagged', 'trends', 'breakdown', 'audit']

      const set = (res, setter, label) => {
        if (res.status === 'fulfilled') setter(res.value.data)
        else { setter(label === 'dashboard' || label === 'breakdown' ? null : []); failed.push(label) }
      }

      set(results[0], setDashboard, 'dashboard')
      set(results[1], setAlerts, 'alerts')
      set(results[2], setRules, 'rules')
      set(results[3], setBlacklist, 'blacklist')
      set(results[4], setCases, 'cases')
      set(results[5], setFlaggedTransactions, 'flagged')
      set(results[6], setTrends, 'trends')
      set(results[7], setBreakdown, 'breakdown')
      if (results[8].status === 'fulfilled') setAuditLog(results[8].value.data)

      if (failed.length) message.warning(`Could not load: ${failed.join(', ')}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAll() }, [])

  const dashboardCards = useMemo(() => {
    if (!dashboard) return []
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
      message.success(`Alert ${id}: ${action}`)
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed')
    }
  }

  const createRule = async (values) => {
    try {
      await fraudAPI.createRule({ ...values, is_active: true })
      message.success('Fraud rule created')
      ruleForm.resetFields()
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed to create rule')
    }
  }

  const createBlacklist = async (values) => {
    const data = { ...values, is_active: true }
    if (values.expiry_date) data.expiry_date = values.expiry_date.format('YYYY-MM-DD')
    try {
      await fraudAPI.createBlacklist(data)
      message.success('Blacklist entry created')
      blacklistForm.resetFields()
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed to create blacklist entry')
    }
  }

  const runCheck = async (values) => {
    try {
      const res = await fraudAPI.runCheck(values)
      setCheckResult(res.data)
      const d = res.data.decision
      if (d === 'DECLINE') message.warning('Decision: DECLINE')
      else if (d === 'FLAG') message.info('Decision: FLAG')
      else message.success('Decision: APPROVE')
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed to run check')
    }
  }

  const createCase = async (values) => {
    try {
      await fraudAPI.createCase(values)
      message.success('Case created')
      caseForm.resetFields()
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed to create case')
    }
  }

  const updateCase = async (row) => {
    const summary = window.prompt('Update case summary', row.summary || '')
    if (summary === null) return
    const s = summary.trim()
    if (!s) { message.error('Summary cannot be empty'); return }
    const assignedTo = window.prompt('Update assignee (optional)', row.assigned_to || '')
    if (assignedTo === null) return
    const notes = window.prompt('Update notes (optional)', row.notes || '')
    if (notes === null) return
    try {
      await fraudAPI.updateCase(row.id, {
        alert_id: row.alert_id,
        summary: s,
        assigned_to: assignedTo.trim() || null,
        notes: notes.trim() || null,
      })
      message.success(`Case ${row.id} updated`)
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed to update case')
    }
  }

  const setCaseStatus = async (id, status) => {
    try {
      await fraudAPI.updateCaseStatus(id, status)
      message.success(`Case ${id} → ${status}`)
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed')
    }
  }

  const deleteCase = async (id) => {
    if (!window.confirm(`Delete case ${id}? This cannot be undone.`)) return
    try {
      await fraudAPI.deleteCase(id)
      message.success(`Case ${id} deleted`)
      await loadAll()
    } catch (err) {
      message.error(err?.response?.data?.detail || 'Failed to delete case')
    }
  }

  const openTimeline = async (row) => {
    try {
      const res = await fraudAPI.getCaseTimeline(row.id)
      setTimelineCase(row)
      setTimelineEntries(res.data)
      setTimelineVisible(true)
    } catch (err) {
      message.error('Could not load case timeline')
    }
  }

  // ── Column definitions ────────────────────────────────────────────────────

  const alertColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    { title: 'STAN', dataIndex: 'stan', key: 'stan', width: 110 },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (v) => <Tag color={severityColor[v] || 'default'}>{v}</Tag>,
    },
    { title: 'Score', dataIndex: 'risk_score', key: 'risk_score', width: 80 },
    { title: 'Decision', dataIndex: 'decision', key: 'decision', width: 100 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (v) => <Tag color={statusColor[v] || 'default'}>{v}</Tag>,
    },
    { title: 'Rules Hit', dataIndex: 'rule_hits', key: 'rule_hits' },
    {
      title: 'Actions',
      key: 'actions',
      width: 380,
      render: (_, row) => (
        <Space wrap>
          <Button size="small" onClick={() => handleAlertAction(row.id, 'ACK')}>ACK</Button>
          <Button size="small" onClick={() => handleAlertAction(row.id, 'ESCALATE')}>Escalate</Button>
          <Button size="small" type="primary" onClick={() => handleAlertAction(row.id, 'APPROVE')}>Approve</Button>
          <Button size="small" danger onClick={() => handleAlertAction(row.id, 'BLOCK_CARD')}>Block Card</Button>
          <Button size="small" danger onClick={() => handleAlertAction(row.id, 'BLOCK_TERMINAL')}>Block Terminal</Button>
          <Button size="small" onClick={() => handleAlertAction(row.id, 'CLOSE')}>Close</Button>
        </Space>
      ),
    },
  ]

  const ruleColumns = [
    { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 80 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Type', dataIndex: 'rule_type', key: 'rule_type', width: 130 },
    { title: 'Threshold', dataIndex: 'threshold', key: 'threshold', width: 100 },
    { title: 'Window (sec)', dataIndex: 'window_seconds', key: 'window_seconds', width: 110 },
    { title: 'Weight', dataIndex: 'weight', key: 'weight', width: 80 },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (v) => <Tag color={severityColor[v] || 'default'}>{v || 'MEDIUM'}</Tag>,
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (v) => <Tag color={actionColor[v] || 'blue'}>{v || 'FLAG'}</Tag>,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (v) => (v ? <Tag color="green">ON</Tag> : <Tag>OFF</Tag>),
    },
  ]

  const blacklistColumns = [
    { title: 'Type', dataIndex: 'entry_type', key: 'entry_type', width: 110 },
    { title: 'Value', dataIndex: 'value', key: 'value' },
    { title: 'Reason', dataIndex: 'reason', key: 'reason' },
    { title: 'Expiry', dataIndex: 'expiry_date', key: 'expiry_date', width: 110 },
    { title: 'Created By', dataIndex: 'created_by', key: 'created_by', width: 120 },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (v) => (v ? <Tag color="green">YES</Tag> : <Tag>NO</Tag>),
    },
  ]

  const caseColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    { title: 'Alert ID', dataIndex: 'alert_id', key: 'alert_id', width: 90 },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      render: (v) => <Tag color={statusColor[v] || 'default'}>{v}</Tag>,
    },
    { title: 'Assigned To', dataIndex: 'assigned_to', key: 'assigned_to', width: 130 },
    { title: 'Summary', dataIndex: 'summary', key: 'summary' },
    {
      title: 'Notes',
      dataIndex: 'notes',
      key: 'notes',
      width: 160,
      render: (v) => v ? <Text ellipsis style={{ maxWidth: 140 }}>{v}</Text> : <Text type="secondary">—</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 420,
      render: (_, row) => (
        <Space wrap>
          <Button size="small" onClick={() => updateCase(row)}>Edit</Button>
          <Button size="small" onClick={() => setCaseStatus(row.id, 'OPEN')}>Open</Button>
          <Button size="small" onClick={() => setCaseStatus(row.id, 'INVESTIGATING')}>Investigate</Button>
          <Button size="small" type="primary" onClick={() => setCaseStatus(row.id, 'CLOSED')}>Close</Button>
          <Button size="small" onClick={() => openTimeline(row)}>Timeline</Button>
          <Button size="small" danger onClick={() => deleteCase(row.id)}>Delete</Button>
        </Space>
      ),
    },
  ]

  const flaggedTransactionColumns = [
    { title: 'Alert ID', dataIndex: 'alert_id', key: 'alert_id', width: 90 },
    { title: 'STAN', dataIndex: 'stan', key: 'stan', width: 110 },
    { title: 'Decision', dataIndex: 'decision', key: 'decision', width: 100 },
    { title: 'Risk Score', dataIndex: 'risk_score', key: 'risk_score', width: 90 },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (v) => <Tag color={severityColor[v] || 'default'}>{v}</Tag>,
    },
    { title: 'Terminal', dataIndex: 'terminal_id', key: 'terminal_id', width: 120 },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', width: 100 },
    { title: 'Rules', dataIndex: 'rule_hits', key: 'rule_hits' },
  ]

  const trendColumns = [
    { title: 'Date', dataIndex: 'date', key: 'date', width: 130 },
    { title: 'Flagged', dataIndex: 'flagged', key: 'flagged', width: 90 },
    { title: 'Declined', dataIndex: 'declined', key: 'declined', width: 90 },
    { title: 'Total', dataIndex: 'total', key: 'total', width: 90 },
  ]

  const breakdownCols = [
    { title: 'Label', dataIndex: 'label', key: 'label' },
    { title: 'Count', dataIndex: 'count', key: 'count', width: 90 },
  ]

  const auditColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    { title: 'Entity', dataIndex: 'entity_type', key: 'entity_type', width: 100 },
    { title: 'Entity ID', dataIndex: 'entity_id', key: 'entity_id', width: 90 },
    { title: 'Action', dataIndex: 'action', key: 'action', width: 130 },
    { title: 'By', dataIndex: 'performed_by', key: 'performed_by', width: 130 },
    { title: 'Detail', dataIndex: 'detail', key: 'detail' },
    {
      title: 'At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '—',
    },
  ]

  const scoreBreakdownCols = [
    { title: 'Rule', dataIndex: 'rule', key: 'rule' },
    { title: 'Contribution', dataIndex: 'contribution', key: 'contribution', width: 130 },
  ]

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <Space direction="vertical" size={16} className="card" style={{ width: '100%' }}>
      {/* KPI cards */}
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
          // ── Alerts ───────────────────────────────────────────────────
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
                  scroll={{ x: 1200 }}
                />
              </Card>
            ),
          },

          // ── Rules ────────────────────────────────────────────────────
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
                      <Select style={{ width: 150 }} options={[
                        { value: 'HIGH_AMOUNT', label: 'HIGH_AMOUNT' },
                        { value: 'VELOCITY', label: 'VELOCITY' },
                      ]} />
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
                    <Form.Item name="severity" initialValue="MEDIUM" rules={[{ required: true }]}>
                      <Select style={{ width: 110 }} options={[
                        { value: 'LOW', label: 'LOW' },
                        { value: 'MEDIUM', label: 'MEDIUM' },
                        { value: 'HIGH', label: 'HIGH' },
                      ]} />
                    </Form.Item>
                    <Form.Item name="action" initialValue="FLAG" rules={[{ required: true }]}>
                      <Select style={{ width: 110 }} options={[
                        { value: 'FLAG', label: 'FLAG' },
                        { value: 'DECLINE', label: 'DECLINE' },
                        { value: 'BLOCK', label: 'BLOCK' },
                      ]} />
                    </Form.Item>
                    <Form.Item name="priority" initialValue={100}>
                      <InputNumber placeholder="Priority" min={1} />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Create</Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card title="Active Rules">
                  <Table rowKey="id" columns={ruleColumns} dataSource={rules} size="small" pagination={{ pageSize: 10 }} scroll={{ x: 900 }} />
                </Card>
              </Space>
            ),
          },

          // ── Blacklist ─────────────────────────────────────────────────
          {
            key: 'blacklist',
            label: 'Blacklist',
            children: (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Card title="Create Blacklist Entry">
                  <Form form={blacklistForm} layout="inline" onFinish={createBlacklist}>
                    <Form.Item name="entry_type" rules={[{ required: true }]}>
                      <Select style={{ width: 130 }} options={[
                        { value: 'TERMINAL', label: 'TERMINAL' },
                        { value: 'BIN', label: 'BIN' },
                        { value: 'PAN', label: 'PAN' },
                      ]} />
                    </Form.Item>
                    <Form.Item name="value" rules={[{ required: true }]}>
                      <Input placeholder="Value" />
                    </Form.Item>
                    <Form.Item name="reason">
                      <Input placeholder="Reason" />
                    </Form.Item>
                    <Form.Item name="expiry_date">
                      <DatePicker placeholder="Expiry date" />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Add</Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card title="Blacklist Entries">
                  <Table rowKey="id" columns={blacklistColumns} dataSource={blacklist} size="small" pagination={{ pageSize: 10 }} scroll={{ x: 800 }} />
                </Card>
              </Space>
            ),
          },

          // ── Fraud Check ───────────────────────────────────────────────
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
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Check</Button>
                    </Form.Item>
                  </Form>
                </Card>
                {checkResult && (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                      type={checkResult.decision === 'DECLINE' ? 'error' : checkResult.decision === 'FLAG' ? 'warning' : 'success'}
                      message={`Decision: ${checkResult.decision}`}
                      description={`Score=${checkResult.risk_score}  |  Severity=${checkResult.severity}  |  Triggers: ${checkResult.triggers.join(', ') || 'None'}`}
                      showIcon
                    />
                    {checkResult.score_breakdown?.length > 0 && (
                      <Card title="Score Breakdown" size="small">
                        <Table
                          rowKey="rule"
                          columns={scoreBreakdownCols}
                          dataSource={checkResult.score_breakdown}
                          size="small"
                          pagination={false}
                        />
                      </Card>
                    )}
                  </Space>
                )}
              </Space>
            ),
          },

          // ── Cases ─────────────────────────────────────────────────────
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
                      <Input placeholder="Summary" style={{ width: 240 }} />
                    </Form.Item>
                    <Form.Item name="notes">
                      <Input placeholder="Notes (optional)" style={{ width: 200 }} />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit">Create</Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card title="Case Queue">
                  <Table rowKey="id" columns={caseColumns} dataSource={cases} size="small" pagination={{ pageSize: 10 }} scroll={{ x: 1300 }} />
                </Card>
              </Space>
            ),
          },

          // ── Transactions ──────────────────────────────────────────────
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
                  scroll={{ x: 1100 }}
                />
              </Card>
            ),
          },

          // ── Dashboard Trends & Breakdown ──────────────────────────────
          {
            key: 'analytics',
            label: 'Analytics',
            children: (
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Daily Trend (last 30 days)">
                    <Table
                      rowKey="date"
                      columns={trendColumns}
                      dataSource={trends}
                      size="small"
                      pagination={{ pageSize: 10 }}
                    />
                  </Card>
                </Col>
                <Col xs={24} lg={6}>
                  <Card title="By Rule">
                    <Table
                      rowKey="label"
                      columns={breakdownCols}
                      dataSource={breakdown?.by_rule || []}
                      size="small"
                      pagination={{ pageSize: 10 }}
                    />
                  </Card>
                </Col>
                <Col xs={24} lg={6}>
                  <Card title="By Terminal">
                    <Table
                      rowKey="label"
                      columns={breakdownCols}
                      dataSource={breakdown?.by_terminal || []}
                      size="small"
                      pagination={{ pageSize: 10 }}
                    />
                  </Card>
                </Col>
              </Row>
            ),
          },

          // ── Audit Log ─────────────────────────────────────────────────
          {
            key: 'audit',
            label: 'Audit Log',
            children: (
              <Card title="Audit Trail">
                <Table
                  rowKey="id"
                  columns={auditColumns}
                  dataSource={auditLog}
                  size="small"
                  pagination={{ pageSize: 20 }}
                  scroll={{ x: 1100 }}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* Case Timeline Modal */}
      <Modal
        title={`Case #${timelineCase?.id} — Timeline`}
        open={timelineVisible}
        onCancel={() => setTimelineVisible(false)}
        footer={<Button onClick={() => setTimelineVisible(false)}>Close</Button>}
        width={600}
      >
        {timelineEntries.length === 0 ? (
          <Text type="secondary">No timeline entries yet.</Text>
        ) : (
          <Timeline
            items={timelineEntries.map((e) => ({
              key: e.id,
              children: (
                <div>
                  <strong>{e.action}</strong>
                  {e.performed_by && <Text type="secondary"> by {e.performed_by}</Text>}
                  {e.detail && <div><Text type="secondary">{e.detail}</Text></div>}
                  <div><Text type="secondary" style={{ fontSize: 12 }}>{e.created_at ? new Date(e.created_at).toLocaleString() : ''}</Text></div>
                </div>
              ),
            }))}
          />
        )}
      </Modal>
    </Space>
  )
}
