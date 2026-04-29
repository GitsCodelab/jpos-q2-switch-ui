import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Modal, Form, Input, message } from 'antd'
import { SearchOutlined, EyeOutlined } from '@ant-design/icons'
import { transactionAPI } from '../services/api'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const [selectedTx, setSelectedTx] = useState(null)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)

  useEffect(() => {
    fetchTransactions()
  }, [])

  const fetchTransactions = async (params = {}) => {
    setLoading(true)
    try {
      const response = await transactionAPI.list(params)
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
    setDetailsModalOpen(true)
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

  return (
    <div>
      <Card className="card" style={{ marginBottom: '16px' }}>
        <div className="card-title">Search Transactions</div>
        <Form form={form} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            <Form.Item label="Transaction ID" name="transaction_id">
              <Input size="small" placeholder="Filter by ID" />
            </Form.Item>
            <Form.Item label="STAN" name="stan">
              <Input size="small" placeholder="Filter by STAN" />
            </Form.Item>
            <Form.Item label="Status" name="status">
              <Input size="small" placeholder="Filter by status" />
            </Form.Item>
            <Form.Item label="Response Code" name="response_code">
              <Input size="small" placeholder="Filter by response code" />
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
        )}
      </Modal>
    </div>
  )
}
