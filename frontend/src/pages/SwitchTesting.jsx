import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Collapse,
  Input,
  message,
  Radio,
  Row,
  Space,
  Spin,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import { CopyOutlined, ReloadOutlined, SearchOutlined, SendOutlined } from '@ant-design/icons'
import { testingAPI } from '../services/api'

const FIELD_ORDER = ['mti', '2', '3', '4', '11', '22', '37', '41']

const FIELD_LABELS = {
  mti: 'MTI',
  '2': 'PAN (F2)',
  '3': 'Processing Code (F3)',
  '4': 'Amount (F4)',
  '11': 'STAN (F11)',
  '22': 'POS Entry Mode (F22)',
  '37': 'RRN (F37)',
  '41': 'Terminal ID (F41)',
}

function buildFieldsFromProfile(profile) {
  if (!profile) {
    return {}
  }
  const merged = {
    mti: profile.mti || '',
    ...(profile.fields || {}),
  }
  if (!merged['2']) {
    merged['2'] = '1234567890123456'
  }
  return merged
}

function amountHelper(value) {
  if (!value || !/^\d{12}$/.test(value)) {
    return null
  }
  const decimal = Number(value) / 100
  return decimal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function rcColor(rc) {
  return rc === '00' ? 'success' : 'error'
}

export default function SwitchTesting({ onNavigate }) {
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [profiles, setProfiles] = useState({})
  const [selectedProfile, setSelectedProfile] = useState('atm')
  const [fields, setFields] = useState({})
  const [response, setResponse] = useState(null)
  const [history, setHistory] = useState([])
  const [errorText, setErrorText] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [profileRes, historyRes] = await Promise.all([
        testingAPI.getProfiles(),
        testingAPI.getHistory(20),
      ])
      const profileMap = profileRes.data?.profiles || {}
      setProfiles(profileMap)
      const initialProfile = profileMap.atm ? 'atm' : Object.keys(profileMap)[0] || 'custom'
      setSelectedProfile(initialProfile)
      setFields(buildFieldsFromProfile(profileMap[initialProfile]))
      setHistory(historyRes.data?.history || [])
      setErrorText('')
    } catch (error) {
      console.error(error)
      setErrorText('Failed to load switch testing metadata')
    } finally {
      setLoading(false)
    }
  }

  const profileOptions = useMemo(() => {
    return Object.keys(profiles).map((name) => ({ label: name.toUpperCase(), value: name }))
  }, [profiles])

  const selectedProfileDescription = profiles[selectedProfile]?.description || 'No description available.'

  const onProfileChange = (nextProfile) => {
    setSelectedProfile(nextProfile)
    setFields(buildFieldsFromProfile(profiles[nextProfile]))
    setErrorText('')
  }

  const onFieldChange = (key, value) => {
    setFields((prev) => ({ ...prev, [key]: value }))
    setErrorText('')
  }

  const handleSend = async () => {
    setSending(true)
    setErrorText('')
    try {
      const payload = {
        profile: selectedProfile,
        fields: Object.fromEntries(
          Object.entries(fields)
            .map(([k, v]) => [k, typeof v === 'string' ? v.trim() : v])
            .filter(([, v]) => v !== '' && v !== null && v !== undefined)
        ),
      }
      const sendRes = await testingAPI.send(payload)
      setResponse(sendRes.data)
      const historyRes = await testingAPI.getHistory(20)
      setHistory(historyRes.data?.history || [])
      message.success('ISO transaction sent')
    } catch (error) {
      const detail = error?.response?.data?.detail
      const status = error?.response?.status
      if (status === 503) {
        setErrorText('Switch is not reachable. Is the switch container running?')
      } else {
        setErrorText(detail || 'Failed to send test transaction')
      }
    } finally {
      setSending(false)
    }
  }

  const handleClear = () => {
    setResponse(null)
    setErrorText('')
  }

  const copyResponse = async () => {
    if (!response) {
      return
    }
    await navigator.clipboard.writeText(JSON.stringify(response, null, 2))
    message.success('Response copied')
  }

  const replayFromHistory = async (entry) => {
    restoreFromHistory(entry)
    setSending(true)
    setErrorText('')
    try {
      const request = entry.request || {}
      const payload = {
        profile: entry.profile || 'custom',
        fields: Object.fromEntries(
          Object.entries({ ...(request.fields || {}), ...(request.mti ? { mti: request.mti } : {}) })
            .map(([k, v]) => [k, typeof v === 'string' ? v.trim() : v])
            .filter(([, v]) => v !== '' && v !== null && v !== undefined)
        ),
      }
      const sendRes = await testingAPI.send(payload)
      setResponse(sendRes.data)
      const historyRes = await testingAPI.getHistory(20)
      setHistory(historyRes.data?.history || [])
      message.success('Transaction replayed')
    } catch (error) {
      const detail = error?.response?.data?.detail
      const status = error?.response?.status
      if (status === 503) {
        setErrorText('Switch is not reachable. Is the switch container running?')
      } else {
        setErrorText(detail || 'Failed to replay transaction')
      }
    } finally {
      setSending(false)
    }
  }

  const responseRows = Object.entries(response?.response?.fields || {}).map(([k, v]) => ({ key: k, field: k, value: v }))

  const historyColumns = [
    { title: '#', dataIndex: 'id', key: 'id', width: 50 },
    {
      title: 'Sent At',
      dataIndex: 'sent_at',
      key: 'sent_at',
      render: (value) => (value ? new Date(value).toLocaleTimeString() : '-'),
      width: 110,
    },
    { title: 'Profile', dataIndex: 'profile', key: 'profile', width: 90 },
    {
      title: 'RC',
      dataIndex: 'rc',
      key: 'rc',
      width: 70,
      render: (rc) => <Tag color={rcColor(rc)}>{rc || '-'}</Tag>,
    },
    { title: 'STAN', dataIndex: 'stan', key: 'stan', width: 100 },
    { title: 'RRN', dataIndex: 'rrn', key: 'rrn', width: 140 },
    { title: 'ms', dataIndex: 'elapsed_ms', key: 'elapsed_ms', width: 70 },
    {
      title: '',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="Load fields from this transaction into the editor">
            <Button
              size="small"
              type="text"
              icon={<ReloadOutlined />}
              onClick={(e) => { e.stopPropagation(); restoreFromHistory(record) }}
            />
          </Tooltip>
          <Tooltip title="Replay: re-send this transaction immediately to the switch">
            <Button
              size="small"
              type="text"
              icon={<SendOutlined />}
              loading={sending}
              onClick={(e) => { e.stopPropagation(); replayFromHistory(record) }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  if (loading) {
    return <Spin spinning />
  }

  return (
    <div>
      <Card className="card" style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Typography.Title level={4} style={{ margin: 0 }}>Switch Testing</Typography.Title>
          <Space>
            <Tooltip title="Clear the current response panel">
              <Button onClick={handleClear}>Clear</Button>
            </Tooltip>
            <Tooltip title="Send the ISO 8583 message to the switch and view the authorisation response">
              <Button type="primary" icon={<SendOutlined />} loading={sending} onClick={handleSend}>
                Send
              </Button>
            </Tooltip>
          </Space>
        </Space>
      </Card>

      {errorText ? (
        <Alert type="error" message={errorText} style={{ marginBottom: 16 }} />
      ) : null}

      <Row gutter={16}>
        <Col xs={24} lg={8}>
          <Card className="card" title="Profile Selector" style={{ marginBottom: 16 }}>
            <Radio.Group
              style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
              options={profileOptions}
              onChange={(e) => onProfileChange(e.target.value)}
              value={selectedProfile}
            />
            <Typography.Paragraph style={{ marginTop: 12, marginBottom: 0 }}>
              {selectedProfileDescription}
            </Typography.Paragraph>
          </Card>

          <Card className="card" title="Field Editor">
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              {FIELD_ORDER.map((fieldKey) => (
                <div key={fieldKey}>
                  <Typography.Text>{FIELD_LABELS[fieldKey]}</Typography.Text>
                  <Input
                    value={fields[fieldKey] || ''}
                    onChange={(e) => onFieldChange(fieldKey, e.target.value)}
                    placeholder={fieldKey === '11' || fieldKey === '37' ? 'auto' : ''}
                  />
                  {fieldKey === '4' && fields['4'] ? (
                    <Typography.Text type="secondary">Amount: {amountHelper(fields['4']) || 'Invalid format'}</Typography.Text>
                  ) : null}
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card className="card" title="Response Panel" style={{ marginBottom: 16 }}>
            {response ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space wrap>
                  <Tag color={response.success ? 'success' : 'error'}>
                    RC: {response.response?.rc || '-'}
                  </Tag>
                  <Typography.Text>MTI: {response.response?.mti || '-'}</Typography.Text>
                  <Typography.Text>STAN: {response.response?.stan || '-'}</Typography.Text>
                  <Typography.Text>RRN: {response.response?.rrn || '-'}</Typography.Text>
                  <Typography.Text>Time: {response.elapsed_ms} ms</Typography.Text>
                </Space>

                <Table
                  size="small"
                  pagination={false}
                  rowKey="key"
                  dataSource={responseRows}
                  columns={[
                    { title: 'Field', dataIndex: 'field', key: 'field', width: 120 },
                    { title: 'Value', dataIndex: 'value', key: 'value' },
                  ]}
                />

                <Space wrap>
                  <Tooltip title="Copy the full JSON response to clipboard">
                    <Button icon={<CopyOutlined />} onClick={copyResponse}>
                      Copy Response
                    </Button>
                  </Tooltip>
                  {onNavigate && response.response?.stan ? (
                    <Tooltip title="Go to Transactions page — this test transaction has been logged by the switch">
                      <Button
                        icon={<SearchOutlined />}
                        onClick={() => onNavigate('transactions')}
                      >
                        View in Transactions (STAN: {response.response.stan})
                      </Button>
                    </Tooltip>
                  ) : null}
                  {onNavigate && selectedProfile === 'fraud' ? (
                    <Tooltip title="Go to Fraud page — high-risk test transactions may generate fraud alerts">
                      <Button onClick={() => onNavigate('fraud')}>
                        View Fraud Alerts
                      </Button>
                    </Tooltip>
                  ) : null}
                </Space>

                {response.raw ? (
                  <Collapse
                    size="small"
                    items={[
                      {
                        key: 'raw',
                        label: 'Raw ISO 8583 Hex',
                        children: (
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <div>
                              <Typography.Text strong>Request bytes ({(response.raw.request_hex.length / 2)} bytes):</Typography.Text>
                              <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, overflowX: 'auto', fontSize: 11, wordBreak: 'break-all', whiteSpace: 'pre-wrap', margin: '4px 0 0' }}>
                                {response.raw.request_hex.match(/.{1,32}/g)?.join('\n') || response.raw.request_hex}
                              </pre>
                            </div>
                            <div>
                              <Typography.Text strong>Response bytes ({(response.raw.response_hex.length / 2)} bytes):</Typography.Text>
                              <pre style={{ background: '#f5f5f5', padding: 8, borderRadius: 4, overflowX: 'auto', fontSize: 11, wordBreak: 'break-all', whiteSpace: 'pre-wrap', margin: '4px 0 0' }}>
                                {response.raw.response_hex.match(/.{1,32}/g)?.join('\n') || response.raw.response_hex}
                              </pre>
                            </div>
                          </Space>
                        ),
                      },
                    ]}
                  />
                ) : null}
              </Space>
            ) : (
              <Typography.Text type="secondary">Send a transaction to view response details.</Typography.Text>
            )}
          </Card>

          <Card className="card" title="History">
            <Table
              size="small"
              rowKey="id"
              dataSource={history}
              columns={historyColumns}
              onRow={(record) => ({
                onClick: () => restoreFromHistory(record),
                style: { cursor: 'pointer' },
              })}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
