import { useEffect, useState } from 'react'
import { Card, Table, Form, Input, Button, Space, Select, message } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { configAPI } from '../services/api'

export default function Routing() {
  const [bins, setBins] = useState([])
  const [terminals, setTerminals] = useState([])
  const [decision, setDecision] = useState(null)
  const [loading, setLoading] = useState(false)

  const [binForm] = Form.useForm()
  const [terminalForm] = Form.useForm()
  const [routingForm] = Form.useForm()

  useEffect(() => {
    fetchBins({})
    fetchTerminals({})
  }, [])

  const fetchBins = async (params) => {
    setLoading(true)
    try {
      const res = await configAPI.listBins({
        scheme: params.scheme || undefined,
        issuer_id: params.issuer_id || undefined,
        limit: 100,
        offset: 0,
      })
      setBins(Array.isArray(res.data) ? res.data : [])
    } catch (error) {
      message.error('Failed to fetch BIN mappings')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const fetchTerminals = async (params) => {
    setLoading(true)
    try {
      const res = await configAPI.listTerminals({
        acquirer_id: params.acquirer_id || undefined,
        limit: 100,
        offset: 0,
      })
      setTerminals(Array.isArray(res.data) ? res.data : [])
    } catch (error) {
      message.error('Failed to fetch terminal mappings')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const runRoutingDecision = async () => {
    const pan = routingForm.getFieldValue('pan')
    if (!pan) {
      message.warning('Please enter a PAN')
      return
    }
    setLoading(true)
    try {
      const res = await configAPI.getRoutingDecision(pan)
      setDecision(res.data)
    } catch (error) {
      message.error(error.response?.data?.message || 'Routing decision failed')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const binColumns = [
    { title: 'BIN', dataIndex: 'bin', key: 'bin', width: 120 },
    { title: 'Scheme', dataIndex: 'scheme', key: 'scheme', width: 120 },
    { title: 'Issuer ID', dataIndex: 'issuer_id', key: 'issuer_id', width: 140 },
  ]

  const terminalColumns = [
    { title: 'Terminal ID', dataIndex: 'terminal_id', key: 'terminal_id', width: 160 },
    { title: 'Acquirer ID', dataIndex: 'acquirer_id', key: 'acquirer_id', width: 140 },
  ]

  return (
    <div>
      <Card className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">Routing Debug</div>
        <Form form={routingForm} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: '2fr auto', gap: 16 }}>
            <Form.Item label="PAN" name="pan">
              <Input size="small" placeholder="Enter PAN (at least 6 digits)" />
            </Form.Item>
            <Form.Item label=" ">
              <Button type="primary" size="small" icon={<SearchOutlined />} onClick={runRoutingDecision} loading={loading}>
                Check Routing
              </Button>
            </Form.Item>
          </div>
        </Form>
        {decision && (
          <div style={{ fontSize: 12, marginTop: 8 }}>
            <div><strong>BIN:</strong> {decision.bin}</div>
            <div><strong>Scheme:</strong> {decision.scheme || '-'}</div>
            <div><strong>Issuer:</strong> {decision.issuer_id || '-'}</div>
            <div><strong>Message:</strong> {decision.message}</div>
          </div>
        )}
      </Card>

      <Card className="card" style={{ marginBottom: 16 }}>
        <div className="card-title">BIN Mapping</div>
        <Form form={binForm} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item label="Scheme" name="scheme">
            <Select
              size="small"
              allowClear
              style={{ width: 140 }}
              options={[{ value: 'LOCAL', label: 'LOCAL' }, { value: 'VISA', label: 'VISA' }, { value: 'MC', label: 'MC' }]}
            />
          </Form.Item>
          <Form.Item label="Issuer" name="issuer_id">
            <Input size="small" placeholder="BANK_A" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" size="small" onClick={() => fetchBins(binForm.getFieldsValue())}>Apply</Button>
              <Button size="small" icon={<ReloadOutlined />} onClick={() => { binForm.resetFields(); fetchBins({}); }}>Reset</Button>
            </Space>
          </Form.Item>
        </Form>
        <Table
          dataSource={bins}
          columns={binColumns}
          rowKey="bin"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      </Card>

      <Card className="card">
        <div className="card-title">Terminal Mapping</div>
        <Form form={terminalForm} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item label="Acquirer" name="acquirer_id">
            <Input size="small" placeholder="BANK_B" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" size="small" onClick={() => fetchTerminals(terminalForm.getFieldsValue())}>Apply</Button>
              <Button size="small" icon={<ReloadOutlined />} onClick={() => { terminalForm.resetFields(); fetchTerminals({}); }}>Reset</Button>
            </Space>
          </Form.Item>
        </Form>
        <Table
          dataSource={terminals}
          columns={terminalColumns}
          rowKey="terminal_id"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      </Card>
    </div>
  )
}
