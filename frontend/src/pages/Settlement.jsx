import { useState, useEffect } from 'react'
import { Card, Table, Button, Space, Modal, Statistic, Row, Col, message, Spin } from 'antd'
import { PlayCircleOutlined, ReloadOutlined, FileOutlined } from '@ant-design/icons'
import { settlementAPI } from '../services/api'

export default function Settlement() {
  const [batches, setBatches] = useState([])
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [detailsModalOpen, setDetailsModalOpen] = useState(false)

  useEffect(() => {
    fetchBatches()
  }, [])

  const fetchBatches = async () => {
    setLoading(true)
    try {
      const response = await settlementAPI.getBatches({ limit: 100 })
      setBatches(response.data.batches || [])
    } catch (error) {
      message.error('Failed to fetch settlement batches')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleRunSettlement = async () => {
    Modal.confirm({
      title: 'Run Settlement',
      content: 'Are you sure you want to run the settlement process? This will process all pending transactions.',
      okText: 'Run',
      cancelText: 'Cancel',
      onOk: async () => {
        setRunning(true)
        try {
          const response = await settlementAPI.run()
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
        const colors = {
          COMPLETED: '#107e3e',
          PENDING: '#e3a821',
          FAILED: '#bb0000',
        }
        return (
          <span style={{ color: colors[status] || '#1d2d3e', fontWeight: '500' }}>
            {status}
          </span>
        )
      },
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
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
          dataSource={batches}
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
                <strong>Settlement Type:</strong> {selectedBatch.settlement_type}
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong>Created At:</strong> {new Date(selectedBatch.created_at).toLocaleString()}
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong>Updated At:</strong> {new Date(selectedBatch.updated_at).toLocaleString()}
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
