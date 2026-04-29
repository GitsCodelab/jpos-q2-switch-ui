import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Modal, Form, Input, message, Select, Tabs } from 'antd'
import { SearchOutlined, EyeOutlined } from '@ant-design/icons'
import { transactionAPI } from '../services/api'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const [selectedTx, setSelectedTx] = useState(null)
  const [events, setEvents] = useState([])
  const [eventsLoading, setEventsLoading] = useState(false)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)

  useEffect(() => {
    fetchTransactions()
  }, [])

  const fetchTransactions = async (params = {}) => {
    setLoading(true)
    try {
      const hasDirectSearch = !!(params.stan || params.rrn)
      const response = hasDirectSearch
        ? await transactionAPI.search({
            stan: params.stan || undefined,
            rrn: params.rrn || undefined,
            limit: params.limit || 50,
            offset: 0,
          })
        : await transactionAPI.list({
            status: params.status || undefined,
            scheme: params.scheme || undefined,
            issuer_id: params.issuer_id || undefined,
            settled: typeof params.settled === 'boolean' ? params.settled : undefined,
            limit: params.limit || 50,
            offset: 0,
          })
      setTransactions(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      message.error('Failed to fetch transactions')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    const values = form.getFieldsValue()
    fetchTransactions(values)
  }

  const handleViewDetails = (record) => {
    setSelectedTx(record)
    loadEvents(record.id)
    setDetailsModalOpen(true)
  }

  const loadEvents = async (id) => {
    setEventsLoading(true)
    try {
      const response = await transactionAPI.getEvents(id)
      setEvents(Array.isArray(response.data) ? response.data : [])
    } catch (error) {
      setEvents([])
      message.error('Failed to load transaction events')
    } finally {
      setEventsLoading(false)
    }
  }

  const columns = [
    {
      title: 'Transaction ID',
      dataIndex: 'id',
      key: 'id',
      width: 150,
      render: (text) => <span style={{ fontSize: '11px' }}>{text}</span>,
    },
    {
      title: 'STAN',
      dataIndex: 'stan',
      key: 'stan',
      width: 80,
    },
    {
      title: 'RRN',
      dataIndex: 'rrn',
      key: 'rrn',
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
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colors = {
          APPROVED: '#107e3e',
          REJECTED: '#bb0000',
          PENDING: '#e3a821',
          REVERSED: '#999999',
        }
        return (
          <span style={{ color: colors[status] || '#1d2d3e', fontWeight: '500' }}>
            {status}
          </span>
        )
      },
    },
    {
      title: 'Response Code',
      dataIndex: 'rc',
      key: 'rc',
      width: 120,
    },
    {
      title: 'Retry Count',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 80,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button
          type="text"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetails(record)}
        >
          View
        </Button>
      ),
    },
  ]

  const eventColumns = [
    { title: 'Type', dataIndex: 'event_type', key: 'event_type', width: 140 },
    { title: 'MTI', dataIndex: 'mti', key: 'mti', width: 90 },
    { title: 'RC', dataIndex: 'rc', key: 'rc', width: 80 },
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text) => new Date(text).toLocaleString(),
    },
  ]

  return (
    <div>
      <Card className="card" style={{ marginBottom: '16px' }}>
        <div className="card-title">Search Transactions</div>
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            <Form.Item label="STAN" name="stan">
              <Input size="small" placeholder="Filter by STAN" />
            </Form.Item>
            <Form.Item label="RRN" name="rrn">
              <Input size="small" placeholder="Filter by RRN" />
            </Form.Item>
            <Form.Item label="Status" name="status">
              <Select
                size="small"
                allowClear
                placeholder="Select status"
                options={[
                  { value: 'APPROVED', label: 'APPROVED' },
                  { value: 'DECLINED', label: 'DECLINED' },
                  { value: 'SECURITY_DECLINE', label: 'SECURITY_DECLINE' },
                  { value: 'TIMEOUT', label: 'TIMEOUT' },
                  { value: 'REQUEST_RECEIVED', label: 'REQUEST_RECEIVED' },
                  { value: 'AUTHORIZED', label: 'AUTHORIZED' },
                ]}
              />
            </Form.Item>
            <Form.Item label="Scheme" name="scheme">
              <Select
                size="small"
                allowClear
                placeholder="Select scheme"
                options={[
                  { value: 'LOCAL', label: 'LOCAL' },
                  { value: 'VISA', label: 'VISA' },
                  { value: 'MC', label: 'MC' },
                ]}
              />
            </Form.Item>
            <Form.Item label="Issuer ID" name="issuer_id">
              <Input size="small" placeholder="e.g. BANK_A" />
            </Form.Item>
            <Form.Item label="Settled" name="settled">
              <Select
                size="small"
                allowClear
                placeholder="All"
                options={[
                  { value: true, label: 'Settled' },
                  { value: false, label: 'Unsettled' },
                ]}
              />
            </Form.Item>
            <Form.Item label="Limit" name="limit" initialValue={50}>
              <Input size="small" placeholder="50" />
            </Form.Item>
          </div>
          <div>
            <Space>
              <Button type="primary" size="small" icon={<SearchOutlined />} onClick={handleSearch}>
                Search
              </Button>
              <Button size="small" onClick={() => { form.resetFields(); fetchTransactions(); }}>
                Reset
              </Button>
            </Space>
          </div>
        </Form>
      </Card>

      <Card className="card">
        <div className="card-title">Transactions List</div>
        <Table
          dataSource={transactions}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50, position: ['bottomCenter'] }}
        />
      </Card>

      <Modal
        title="Transaction Details"
        open={detailsModalOpen}
        onCancel={() => setDetailsModalOpen(false)}
        footer={null}
        width={700}
      >
        {selectedTx && (
          <Tabs
            items={[
              {
                key: 'details',
                label: 'Details',
                children: (
                  <div style={{ fontSize: '12px' }}>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Transaction ID:</strong> {selectedTx.id}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>STAN:</strong> {selectedTx.stan}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>RRN:</strong> {selectedTx.rrn}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Amount:</strong> ${parseFloat(selectedTx.amount).toFixed(2)}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Status:</strong> {selectedTx.status}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Response Code:</strong> {selectedTx.rc}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Retry Count:</strong> {selectedTx.retry_count}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Created At:</strong> {new Date(selectedTx.created_at).toLocaleString()}
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                      <strong>Updated At:</strong> {new Date(selectedTx.updated_at).toLocaleString()}
                    </div>
                  </div>
                ),
              },
              {
                key: 'events',
                label: `Events (${events.length})`,
                children: (
                  <Table
                    dataSource={events}
                    columns={eventColumns}
                    rowKey="id"
                    loading={eventsLoading}
                    size="small"
                    bordered
                    pagination={{ pageSize: 10 }}
                  />
                ),
              },
            ]}
          />
        )}
      </Modal>
    </div>
  )
}
