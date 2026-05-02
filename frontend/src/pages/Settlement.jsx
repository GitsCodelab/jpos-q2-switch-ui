import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Modal, Statistic, Row, Col, message, Spin, Form, Input, DatePicker } from 'antd'
import { PlayCircleOutlined, ReloadOutlined, FileOutlined } from '@ant-design/icons'
import { settlementAPI } from '../services/api'

export default function Settlement() {
  const [batches, setBatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)
  const [filteredBatches, setFilteredBatches] = useState([])
  const [form] = Form.useForm()

  useEffect(() => {
    fetchBatches()
  }, [])

  const fetchBatches = async () => {
    setLoading(true)
    try {
      const response = await settlementAPI.getBatches({ limit: 100 })
      const items = Array.isArray(response.data) ? response.data : []
      setBatches(items)
      setFilteredBatches(items)
    } catch (error) {
      message.error('Failed to fetch settlement batches')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleRunSettlement = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      message.error('Login required. Please sign in again.')
      return
    }

    const settlementDate = form.getFieldValue('settlement_date')
    Modal.confirm({
      title: 'Run Settlement',
      content: 'Are you sure you want to run the settlement process? This will process all pending transactions.',
      okText: 'Run',
      cancelText: 'Cancel',
      onOk: async () => {
        setRunning(true)
        try {
          const params = {}
          if (settlementDate) {
            params.settlement_date = settlementDate.format('YYYY-MM-DD')
          }
          const response = await settlementAPI.run(params)
          message.success(`Settlement completed: ${response.data.settled_count} transactions settled`)
          fetchBatches()
        } catch (error) {
          message.error(error.response?.data?.message || 'Settlement failed')
          console.error(error)
        } finally {
          setRunning(false)
        }
      },
    })
  }

  const applyFilters = () => {
    const { batch_id, min_count } = form.getFieldsValue()
    const min = min_count ? Number(min_count) : null
    const filtered = batches.filter((b) => {
      if (batch_id && !String(b.batch_id || '').toLowerCase().includes(String(batch_id).toLowerCase())) {
        return false
      }
      if (min !== null && Number(b.total_count || 0) < min) {
        return false
      }
      return true
    })
    setFilteredBatches(filtered)
  }

  const resetFilters = () => {
    form.resetFields(['batch_id', 'min_count'])
    setFilteredBatches(batches)
  }

  const handleViewBatch = async (batchId) => {
    try {
      const response = await settlementAPI.getBatch(batchId)
      setSelectedBatch(response.data)
      setDetailsModalOpen(true)
    } catch (error) {
      message.error('Failed to fetch batch details')
      console.error(error)
    }
  }

  const columns = [
    {
      title: 'Batch ID',
      dataIndex: 'batch_id',
      key: 'batch_id',
      width: 120,
      render: (text) => <span style={{ fontSize: '11px' }}>{text}</span>,
    },
    {
      title: 'Settlement Type',
      dataIndex: 'settlement_type',
      key: 'settlement_type',
      width: 100,
      render: () => 'MANUAL',
    },
    {
      title: 'Total Count',
      dataIndex: 'total_count',
      key: 'total_count',
      width: 80,
      align: 'right',
    },
    {
      title: 'Total Amount',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      align: 'right',
      render: (text) => `$${parseFloat(text).toFixed(2)}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const value = status || 'COMPLETED'
        const colors = {
          COMPLETED: '#107e3e',
          PENDING: '#e3a821',
          FAILED: '#bb0000',
        }
        return (
          <span style={{ color: colors[value] || '#1d2d3e', fontWeight: '500' }}>
            {value}
          </span>
        )
      },
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      defaultSortOrder: 'descend',
      sorter: (a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0),
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button
          type="text"
          size="small"
          icon={<FileOutlined />}
          onClick={() => handleViewBatch(record.batch_id)}
        >
          View
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Card className="card" style={{ marginBottom: '16px' }}>
        <div className="card-title">Settlement Operations</div>
        <div style={{ fontSize: '12px', marginBottom: '16px' }}>
          Run the settlement process to batch and settle all pending transactions.
        </div>
        <Form form={form} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item label="Settlement Date" name="settlement_date">
            <DatePicker size="small" />
          </Form.Item>
          <Form.Item label="Batch ID" name="batch_id">
            <Input size="small" placeholder="Filter batch id" />
          </Form.Item>
          <Form.Item label="Min Count" name="min_count">
            <Input size="small" placeholder="0" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" size="small" onClick={applyFilters}>Apply Filters</Button>
              <Button size="small" onClick={resetFilters}>Reset Filters</Button>
            </Space>
          </Form.Item>
        </Form>
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            loading={running}
            onClick={handleRunSettlement}
          >
            {running ? 'Running Settlement...' : 'Run Settlement'}
          </Button>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={fetchBatches}
          >
            Refresh
          </Button>
        </Space>
      </Card>

      <Card className="card">
        <div className="card-title">Settlement Batches</div>
        <Table
          dataSource={filteredBatches}
          columns={columns}
          rowKey="batch_id"
          loading={loading}
          size="small"
          bordered
          pagination={{ pageSize: 50 }}
        />
      </Card>

      <Modal
        title="Settlement Batch Details"
        open={detailsModalOpen}
        onCancel={() => setDetailsModalOpen(false)}
        footer={null}
        width={700}
      >
        {selectedBatch ? (
          <Spin spinning={false}>
            <div style={{ fontSize: '12px' }}>
              <Row gutter={16} style={{ marginBottom: '16px' }}>
                <Col xs={12}>
                  <Statistic
                    title="Batch ID"
                    value={selectedBatch.batch_id}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Col>
                <Col xs={12}>
                  <Statistic
                    title="Status"
                    value={selectedBatch.status}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Col>
              </Row>
              <Row gutter={16} style={{ marginBottom: '16px' }}>
                <Col xs={12}>
                  <Statistic
                    title="Total Transactions"
                    value={selectedBatch.total_count}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Col>
                <Col xs={12}>
                  <Statistic
                    title="Total Amount"
                    value={`$${parseFloat(selectedBatch.total_amount).toFixed(2)}`}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Col>
              </Row>
              <div style={{ marginBottom: '12px' }}>
                <strong>Settlement Type:</strong> MANUAL
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong>Created At:</strong> {new Date(selectedBatch.created_at).toLocaleString()}
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong>Updated At:</strong> {selectedBatch.created_at ? new Date(selectedBatch.created_at).toLocaleString() : '-'}
              </div>
            </div>
          </Spin>
        ) : (
          <Spin />
        )}
      </Modal>
    </div>
  )
}
