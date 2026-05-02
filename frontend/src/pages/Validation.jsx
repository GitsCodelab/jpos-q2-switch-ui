import React, { useCallback, useEffect, useState } from 'react'
import {
  Badge,
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
  Tabs,
  message,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { validationAPI } from '../services/api'

const { Option } = Select
const { TabPane } = Tabs

// ─── helpers ──────────────────────────────────────────────────────────────────

const SCHEMES = ['*', 'LOCAL', 'VISA', 'MC']
const FORMATS = ['ANY', 'NUMERIC', 'ALPHA', 'ALPHANUMERIC']
const RULE_TYPES = [
  'MAX_AMOUNT',
  'MIN_AMOUNT',
  'CURRENCY_ALLOW',
  'PROC_CODE_ALLOW',
  'TERMINAL_BLOCK',
  'PAN_PREFIX_BLOCK',
]

const schemeColor = (s) => {
  if (!s || s === '*') return 'default'
  const map = { LOCAL: 'blue', VISA: 'gold', MC: 'volcano' }
  return map[s] || 'default'
}

const resultColor = (r) => (r === 'PASS' ? 'success' : 'error')

// ─── Validation Rules Tab ─────────────────────────────────────────────────────

function ValidationRulesTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [schemeFilter, setSchemeFilter] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (schemeFilter) params.scheme = schemeFilter
      const res = await validationAPI.getRules(params)
      setData(res.data)
    } catch {
      message.error('Failed to load validation rules')
    } finally {
      setLoading(false)
    }
  }, [schemeFilter])

  useEffect(() => { load() }, [load])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ scheme: 'LOCAL', format: 'ANY', enabled: true, mandatory: false, min_len: 0, max_len: 999 })
    setModalOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    form.setFieldsValue(row)
    setModalOpen(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    try {
      if (editing) {
        await validationAPI.updateRule(editing.id, values)
        message.success('Rule updated')
      } else {
        await validationAPI.createRule(values)
        message.success('Rule created')
      }
      setModalOpen(false)
      load()
    } catch {
      message.error('Failed to save rule')
    }
  }

  const handleDelete = async (id) => {
    try {
      await validationAPI.deleteRule(id)
      message.success('Rule deleted')
      load()
    } catch {
      message.error('Failed to delete rule')
    }
  }

  const toggleEnabled = async (row) => {
    try {
      await validationAPI.updateRule(row.id, { enabled: !row.enabled })
      load()
    } catch {
      message.error('Failed to update rule')
    }
  }

  const columns = [
    {
      title: 'Scheme',
      dataIndex: 'scheme',
      width: 90,
      render: (v) => <Tag color={schemeColor(v)}>{v}</Tag>,
    },
    { title: 'Field ID', dataIndex: 'field_id', width: 80, sorter: (a, b) => a.field_id - b.field_id },
    { title: 'Field Name', dataIndex: 'field_name', render: (v) => v || '—' },
    {
      title: 'Mandatory',
      dataIndex: 'mandatory',
      width: 100,
      render: (v) => v ? <Tag color="red">YES</Tag> : <Tag>NO</Tag>,
    },
    { title: 'Min Len', dataIndex: 'min_len', width: 80 },
    { title: 'Max Len', dataIndex: 'max_len', width: 80 },
    { title: 'Format', dataIndex: 'format', width: 110, render: (v) => <Tag>{v}</Tag> },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      width: 90,
      render: (v, row) => <Switch checked={v} size="small" onChange={() => toggleEnabled(row)} />,
    },
    {
      title: 'Actions',
      width: 100,
      render: (_, row) => (
        <Space size="small">
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(row)} />
          <Popconfirm title="Delete this rule?" onConfirm={() => handleDelete(row.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="ISO 8583 Field Validation Rules"
        extra={
          <Space>
            <Select
              allowClear
              placeholder="Filter by scheme"
              style={{ width: 140 }}
              onChange={setSchemeFilter}
              value={schemeFilter}
            >
              {SCHEMES.map((s) => <Option key={s} value={s}>{s}</Option>)}
            </Select>
            <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Add Rule</Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          size="small"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editing ? 'Edit Validation Rule' : 'New Validation Rule'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        okText="Save"
        width={520}
      >
        <Form form={form} layout="vertical">
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="scheme" label="Scheme" rules={[{ required: true }]}>
                <Select>{SCHEMES.map((s) => <Option key={s} value={s}>{s}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="field_id" label="Field ID (DE)" rules={[{ required: true }]}>
                <InputNumber min={1} max={128} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="field_name" label="Field Name">
            <Input placeholder="e.g. PAN, STAN, Terminal ID" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="format" label="Format">
                <Select>{FORMATS.map((f) => <Option key={f} value={f}>{f}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="min_len" label="Min Length">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_len" label="Max Length">
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="mandatory" label="Mandatory" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="enabled" label="Enabled" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </>
  )
}

// ─── Auth Rules Tab ───────────────────────────────────────────────────────────

function AuthRulesTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await validationAPI.getAuthRules()
      setData(res.data)
    } catch {
      message.error('Failed to load authorization rules')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ scheme: '*', rule_type: 'MAX_AMOUNT', enabled: true })
    setModalOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    form.setFieldsValue(row)
    setModalOpen(true)
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    try {
      if (editing) {
        await validationAPI.updateAuthRule(editing.id, values)
        message.success('Rule updated')
      } else {
        await validationAPI.createAuthRule(values)
        message.success('Rule created')
      }
      setModalOpen(false)
      load()
    } catch {
      message.error('Failed to save rule')
    }
  }

  const handleDelete = async (id) => {
    try {
      await validationAPI.deleteAuthRule(id)
      message.success('Rule deleted')
      load()
    } catch {
      message.error('Failed to delete rule')
    }
  }

  const toggleEnabled = async (row) => {
    try {
      await validationAPI.updateAuthRule(row.id, { enabled: !row.enabled })
      load()
    } catch {
      message.error('Failed to update rule')
    }
  }

  const columns = [
    { title: 'Name', dataIndex: 'rule_name' },
    {
      title: 'Scheme',
      dataIndex: 'scheme',
      width: 90,
      render: (v) => <Tag color={schemeColor(v)}>{v}</Tag>,
    },
    { title: 'Rule Type', dataIndex: 'rule_type', render: (v) => <Tag color="purple">{v}</Tag> },
    { title: 'Value', dataIndex: 'value', render: (v) => <code>{v}</code> },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      width: 90,
      render: (v, row) => <Switch checked={v} size="small" onChange={() => toggleEnabled(row)} />,
    },
    {
      title: 'Actions',
      width: 100,
      render: (_, row) => (
        <Space size="small">
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(row)} />
          <Popconfirm title="Delete this rule?" onConfirm={() => handleDelete(row.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="Authorization Rules"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Add Rule</Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          size="small"
          loading={loading}
          dataSource={data}
          columns={columns}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editing ? 'Edit Auth Rule' : 'New Authorization Rule'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        okText="Save"
        width={480}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="rule_name" label="Rule Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. VISA max amount" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="scheme" label="Scheme" rules={[{ required: true }]}>
                <Select>{SCHEMES.map((s) => <Option key={s} value={s}>{s}</Option>)}</Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="rule_type" label="Rule Type" rules={[{ required: true }]}>
                <Select>{RULE_TYPES.map((t) => <Option key={t} value={t}>{t}</Option>)}</Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="value" label="Value" rules={[{ required: true }]}>
            <Input placeholder="Numeric amount, currency code, proc code, terminal ID, or BIN prefix" />
          </Form.Item>
          <Form.Item name="enabled" label="Enabled" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// ─── Events Tab ───────────────────────────────────────────────────────────────

function EventsTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [resultFilter, setResultFilter] = useState(null)
  const [schemeFilter, setSchemeFilter] = useState(null)
  const [selectedEvent, setSelectedEvent] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { limit: 200 }
      if (resultFilter) params.result = resultFilter
      if (schemeFilter) params.scheme = schemeFilter
      const res = await validationAPI.getEvents(params)
      setData(res.data)
    } catch {
      message.error('Failed to load validation events')
    } finally {
      setLoading(false)
    }
  }, [resultFilter, schemeFilter])

  useEffect(() => { load() }, [load])

  const columns = [
    {
      title: 'Time',
      dataIndex: 'created_at',
      width: 170,
      render: (v) => v ? new Date(v).toLocaleString() : '—',
    },
    { title: 'STAN', dataIndex: 'stan', width: 100 },
    { title: 'MTI', dataIndex: 'mti', width: 70 },
    {
      title: 'Scheme',
      dataIndex: 'scheme',
      width: 80,
      render: (v) => v ? <Tag color={schemeColor(v)}>{v}</Tag> : '—',
    },
    { title: 'Type', dataIndex: 'validation_type', width: 140, render: (v) => <Tag>{v}</Tag> },
    {
      title: 'Result',
      dataIndex: 'result',
      width: 80,
      render: (v) => (
        <Badge
          status={resultColor(v)}
          text={v === 'PASS'
            ? <span style={{ color: '#52c41a' }}><CheckCircleOutlined /> PASS</span>
            : <span style={{ color: '#ff4d4f' }}><CloseCircleOutlined /> FAIL</span>}
        />
      ),
    },
    { title: 'RC', dataIndex: 'reject_code', width: 60, render: (v) => v ? <Tag color="red">{v}</Tag> : '—' },
    {
      title: 'Errors',
      dataIndex: 'errors',
      ellipsis: true,
      render: (v) => v || '—',
    },
  ]

  return (
    <Card
      title="Validation Event Log"
      extra={
        <Space>
          <Select
            allowClear
            placeholder="Result"
            style={{ width: 110 }}
            onChange={setResultFilter}
            value={resultFilter}
          >
            <Option value="PASS">PASS</Option>
            <Option value="FAIL">FAIL</Option>
          </Select>
          <Select
            allowClear
            placeholder="Scheme"
            style={{ width: 120 }}
            onChange={setSchemeFilter}
            value={schemeFilter}
          >
            {SCHEMES.filter((s) => s !== '*').map((s) => (
              <Option key={s} value={s}>{s}</Option>
            ))}
          </Select>
          <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
        </Space>
      }
    >
      <Table
        rowKey="id"
        size="small"
        loading={loading}
        dataSource={data}
        columns={columns}
        onRow={(row) => ({ onClick: () => setSelectedEvent(row), style: { cursor: 'pointer' } })}
        pagination={{ pageSize: 25 }}
      />
      <Modal
        title="Validation Event Detail"
        open={!!selectedEvent}
        onCancel={() => setSelectedEvent(null)}
        footer={null}
        width={560}
      >
        {selectedEvent && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="ID">{selectedEvent.id}</Descriptions.Item>
            <Descriptions.Item label="Time">
              {selectedEvent.created_at ? new Date(selectedEvent.created_at).toLocaleString() : '—'}
            </Descriptions.Item>
            <Descriptions.Item label="STAN">{selectedEvent.stan || '—'}</Descriptions.Item>
            <Descriptions.Item label="RRN">{selectedEvent.rrn || '—'}</Descriptions.Item>
            <Descriptions.Item label="MTI">{selectedEvent.mti || '—'}</Descriptions.Item>
            <Descriptions.Item label="Scheme">
              <Tag color={schemeColor(selectedEvent.scheme)}>{selectedEvent.scheme || '—'}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Type">{selectedEvent.validation_type}</Descriptions.Item>
            <Descriptions.Item label="Result">
              <Tag color={selectedEvent.result === 'PASS' ? 'green' : 'red'}>{selectedEvent.result}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Reject Code" span={2}>
              {selectedEvent.reject_code || '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Errors" span={2}>
              <pre style={{ fontSize: 12, margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {selectedEvent.errors || '—'}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Card>
  )
}

// ─── Stats Tab ────────────────────────────────────────────────────────────────

function StatsTab() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await validationAPI.getStats()
      setStats(res.data)
    } catch {
      message.error('Failed to load stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (!stats && !loading) return null

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Row gutter={16}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic title="Total Validation Events" value={stats?.total_events ?? 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Pass"
              value={stats?.pass_count ?? 0}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Fail"
              value={stats?.fail_count ?? 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="Pass Rate"
              value={stats?.pass_rate ?? 0}
              suffix="%"
              precision={2}
              valueStyle={{ color: (stats?.pass_rate ?? 0) >= 90 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Card title="Top Reject Codes" loading={loading} size="small">
            <Table
              rowKey="code"
              size="small"
              pagination={false}
              dataSource={stats?.top_reject_codes ?? []}
              columns={[
                { title: 'Code', dataIndex: 'code', render: (v) => <Tag color="red">{v}</Tag> },
                { title: 'Count', dataIndex: 'count', sorter: (a, b) => b.count - a.count },
              ]}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="By Scheme" loading={loading} size="small">
            <Table
              rowKey="scheme"
              size="small"
              pagination={false}
              dataSource={stats?.by_scheme ?? []}
              columns={[
                { title: 'Scheme', dataIndex: 'scheme', render: (v) => <Tag color={schemeColor(v)}>{v}</Tag> },
                { title: 'Events', dataIndex: 'count' },
              ]}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="By Validation Type" loading={loading} size="small">
            <Table
              rowKey="type"
              size="small"
              pagination={false}
              dataSource={stats?.by_validation_type ?? []}
              columns={[
                { title: 'Type', dataIndex: 'type', render: (v) => <Tag>{v}</Tag> },
                { title: 'Events', dataIndex: 'count' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </Space>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function Validation() {
  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ marginBottom: 16 }}>ISO Validation &amp; Authorization Rules</h2>
      <Tabs defaultActiveKey="rules" destroyInactiveTabPane>
        <TabPane tab="Validation Rules" key="rules">
          <ValidationRulesTab />
        </TabPane>
        <TabPane tab="Authorization Rules" key="auth">
          <AuthRulesTab />
        </TabPane>
        <TabPane tab="Validation Events" key="events">
          <EventsTab />
        </TabPane>
        <TabPane tab="Stats" key="stats">
          <StatsTab />
        </TabPane>
      </Tabs>
    </div>
  )
}
