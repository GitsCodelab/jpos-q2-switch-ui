import { useEffect, useState } from 'react'
import { Card, Table, Form, Input, Button, Space, Select, Statistic, Row, Col, message } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { netSettlementAPI } from '../services/api'

export default function NetSettlement() {
  const [rows, setRows] = useState([])
  const [summary, setSummary] = useState([])
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchData({})
  }, [])

  const fetchData = async (params = {}) => {
    setLoading(true)
    try {
      const [listRes, summaryRes] = await Promise.all([
        params.batch_id
          ? netSettlementAPI.getByBatch(params.batch_id)
          : netSettlementAPI.list({ party_id: params.party_id || undefined, limit: 100, offset: 0 }),
        netSettlementAPI.getSummary(),
      ])
      setRows(Array.isArray(listRes.data) ? listRes.data : [])
      setSummary(Array.isArray(summaryRes.data) ? summaryRes.data : [])
    } catch (error) {
      message.error('Failed to fetch net settlement data')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: 'Party', dataIndex: 'party_id', key: 'party_id', width: 120 },
    {
      title: 'Net Amount',
      dataIndex: 'net_amount',
      key: 'net_amount',
      width: 140,
      render: (value) => {
        const amount = Number(value || 0)
        const color = amount >= 0 ? '#107e3e' : '#bb0000'
        return <span style={{ color, fontWeight: 600 }}>{amount}</span>
      },
    },
    { title: 'Settlement Date', dataIndex: 'settlement_date', key: 'settlement_date', width: 140 },
    { title: 'Batch ID', dataIndex: 'batch_id', key: 'batch_id', width: 180 },
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

  const totalNet = summary.reduce((acc, item) => acc + Number(item.total_net_amount || 0), 0)

  return (
    <div>
      <Card className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Net Settlement Filters</div>
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            <Form.Item label="Party ID" name="party_id">
              <Input size="small" placeholder="e.g. BANK_A" />
            </Form.Item>
            <Form.Item label="Batch ID" name="batch_id">
              <Input size="small" placeholder="e.g. BATCH-XXXXXXXXXXXX" />
            </Form.Item>
            <Form.Item label="Quick Party" name="quick_party">
              <Select
                size="small"
                allowClear
                placeholder="Optional quick select"
                options={[
                  { value: 'BANK_A', label: 'BANK_A' },
                  { value: 'BANK_B', label: 'BANK_B' },
                  { value: 'BANK_C', label: 'BANK_C' },
                ]}
                onChange={(value) => form.setFieldValue('party_id', value || undefined)}
              />
            </Form.Item>
          </div>
          <Space>
            <Button type="primary" size="small" icon={<SearchOutlined />} onClick={() => fetchData(form.getFieldsValue())}>
              Apply
            </Button>
            <Button size="small" icon={<ReloadOutlined />} onClick={() => { form.resetFields(); fetchData({}); }}>
              Reset
            </Button>
          </Space>
        </Form>
      </Card>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8}>
          <Card className="card"><Statistic title="Rows" value={rows.length} /></Card>
        </Col>
        <Col xs={12} sm={8}>
          <Card className="card"><Statistic title="Summary Parties" value={summary.length} /></Card>
        </Col>
        <Col xs={12} sm={8}>
          <Card className="card"><Statistic title="Net Sum" value={totalNet} /></Card>
        </Col>
      </Row>

      <Card className="card">
        <div className="card-title">Net Settlement Positions</div>
        <Table
          dataSource={rows}
          columns={columns}
          rowKey={(r) => `${r.party_id}-${r.batch_id}-${r.id}`}
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      </Card>
    </div>
  )
}
