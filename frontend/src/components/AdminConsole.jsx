import { useState, useEffect } from 'react'
import CaseDetailScreen from './CaseDetailScreen'

const TYPE_ICONS = {
  email: '📧',
  voice_call: '📞',
  chat: '💬',
  document: '📄'
}

const TYPE_COLORS = {
  email: 'var(--accent-blue)',
  voice_call: 'var(--accent-purple)',
  chat: 'var(--accent-cyan)',
  document: 'var(--accent-emerald)'
}

const URGENCY_COLORS = {
  critical: 'var(--accent-rose)',
  high: 'var(--accent-amber)',
  normal: 'var(--accent-emerald)',
  low: 'var(--text-muted)'
}

function AdminConsole({ agents, serverStatus }) {
  const [cases, setCases] = useState([])
  const [stats, setStats] = useState(null)
  const [selectedCase, setSelectedCase] = useState(null)
  const [filterType, setFilterType] = useState('all')
  const [activeTab, setActiveTab] = useState('inbox')
  const [viewMode, setViewMode] = useState('list') // 'list' or 'detail'

  // Fetch cases on mount and periodically
  useEffect(() => {
    if (serverStatus.status === 'online') {
      fetchCases()
      fetchStats()
      const interval = setInterval(() => {
        fetchCases()
        fetchStats()
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [serverStatus.status])

  const fetchCases = async () => {
    try {
      const url = filterType === 'all' 
        ? '/api/cases?limit=100'
        : `/api/cases?case_type=${filterType}&limit=100`
      const response = await fetch(url)
      const data = await response.json()
      setCases(data.cases || [])
    } catch (error) {
      console.error('Failed to fetch cases:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/cases/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  useEffect(() => {
    if (serverStatus.status === 'online') {
      fetchCases()
    }
  }, [filterType])

  const deleteCase = async (caseId) => {
    if (!confirm('Are you sure you want to delete this case?')) return
    try {
      await fetch(`/api/cases/${caseId}`, { method: 'DELETE' })
      fetchCases()
      fetchStats()
      if (selectedCase?.case_id === caseId) {
        setSelectedCase(null)
        setViewMode('list')
      }
    } catch (error) {
      console.error('Failed to delete case:', error)
    }
  }

  const openCaseDetail = (caseData) => {
    setSelectedCase(caseData)
    setViewMode('detail')
  }

  const closeCaseDetail = () => {
    setViewMode('list')
  }

  // Group cases by type
  const groupedByType = cases.reduce((acc, c) => {
    const type = c.case_type || 'unknown'
    if (!acc[type]) acc[type] = []
    acc[type].push(c)
    return acc
  }, {})

  // Group cases by practice area
  const groupedByPractice = cases.reduce((acc, c) => {
    const pa = c.classification?.practice_area || 'unclassified'
    if (!acc[pa]) acc[pa] = []
    acc[pa].push(c)
    return acc
  }, {})

  // Show detail screen if viewing a case
  if (viewMode === 'detail' && selectedCase) {
    return (
      <CaseDetailScreen 
        caseData={selectedCase} 
        onBack={closeCaseDetail} 
      />
    )
  }

  if (serverStatus.status !== 'online') {
    return (
      <div className="admin-panel">
        <div className="admin-header">
          <h2><span className="admin-icon">⚙️</span> Admin Console</h2>
        </div>
        <div className="card">
          <div className="empty-state">
            <span style={{ fontSize: '3rem' }}>🔌</span>
            <h3>Server Not Connected</h3>
            <p>Start the server with <code>python server.py</code></p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h2><span className="admin-icon">⚙️</span> Admin Console</h2>
        <p>All processed communications - stored and categorized by the multi-agent system</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Cases</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.by_type?.email || 0}</div>
            <div className="stat-label">📧 Emails</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.by_type?.voice_call || 0}</div>
            <div className="stat-label">📞 Voice Calls</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.by_type?.chat || 0}</div>
            <div className="stat-label">💬 Chats</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.by_type?.document || 0}</div>
            <div className="stat-label">📄 Documents</div>
          </div>
          <div className="stat-card highlight">
            <div className="stat-value">{stats.requires_review || 0}</div>
            <div className="stat-label">⚠️ Needs Review</div>
          </div>
        </div>
      )}

      {/* Admin Tabs */}
      <div className="admin-tabs">
        <button 
          className={`admin-tab ${activeTab === 'inbox' ? 'active' : ''}`}
          onClick={() => setActiveTab('inbox')}
        >
          📥 All Cases
        </button>
        <button 
          className={`admin-tab ${activeTab === 'by-type' ? 'active' : ''}`}
          onClick={() => setActiveTab('by-type')}
        >
          📊 By Type
        </button>
        <button 
          className={`admin-tab ${activeTab === 'by-practice' ? 'active' : ''}`}
          onClick={() => setActiveTab('by-practice')}
        >
          ⚖️ By Practice Area
        </button>
        <button 
          className={`admin-tab ${activeTab === 'agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('agents')}
        >
          🤖 Agents
        </button>
      </div>

      {/* Tab Content */}
      <div className="admin-content">
        {activeTab === 'inbox' && (
          <div className="admin-inbox-full">
            {/* Filter */}
            <div className="filter-bar">
              <label>Filter by type:</label>
              <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                <option value="all">All Types</option>
                <option value="email">📧 Emails</option>
                <option value="voice_call">📞 Voice Calls</option>
                <option value="chat">💬 Chats</option>
                <option value="document">📄 Documents</option>
              </select>
              <button className="btn btn-secondary btn-small" onClick={fetchCases}>
                🔄 Refresh
              </button>
            </div>

            {/* Case Grid */}
            <div className="case-grid">
              {cases.length === 0 ? (
                <div className="empty-state">
                  <span style={{ fontSize: '2rem' }}>📭</span>
                  <p>No cases yet. Submit something from the Customer Portal!</p>
                </div>
              ) : (
                cases.map(c => (
                  <CaseCard 
                    key={c.case_id} 
                    caseData={c} 
                    onSelect={() => openCaseDetail(c)}
                    onDelete={() => deleteCase(c.case_id)}
                  />
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'by-type' && (
          <div className="grouped-view">
            {Object.entries(groupedByType).map(([type, typeCases]) => (
              <div key={type} className="group-section">
                <h3 className="group-title">
                  <span>{TYPE_ICONS[type] || '📁'}</span>
                  {type.replace('_', ' ').toUpperCase()}
                  <span className="group-count">{typeCases.length}</span>
                </h3>
                <div className="group-cases">
                  {typeCases.map(c => (
                    <CaseCard 
                      key={c.case_id} 
                      caseData={c} 
                      compact
                      onSelect={() => openCaseDetail(c)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'by-practice' && (
          <div className="grouped-view">
            {Object.entries(groupedByPractice).map(([practice, practiceCases]) => (
              <div key={practice} className="group-section">
                <h3 className="group-title">
                  <span>⚖️</span>
                  {practice.toUpperCase()}
                  <span className="group-count">{practiceCases.length}</span>
                </h3>
                <div className="group-cases">
                  {practiceCases.map(c => (
                    <CaseCard 
                      key={c.case_id} 
                      caseData={c} 
                      compact
                      onSelect={() => openCaseDetail(c)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="agents-view">
            <h3>🤖 Registered Agents</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              These agents process all incoming communications
            </p>
            <div className="agent-grid">
              {agents.map(agent => (
                <div key={agent.agent_id} className="agent-card-admin">
                  <div className="agent-header">
                    <span className="agent-icon-large">
                      {agent.agent_id.includes('email') ? '📧' :
                       agent.agent_id.includes('document') ? '📄' :
                       agent.agent_id.includes('intake') ? '👥' :
                       agent.agent_id.includes('deadline') ? '⏰' :
                       agent.agent_id.includes('response') ? '✍️' :
                       agent.agent_id.includes('orchestrator') ? '🎯' : '🤖'}
                    </span>
                    <div>
                      <div className="agent-name">{agent.name}</div>
                      <div className="agent-id">{agent.agent_id}</div>
                    </div>
                  </div>
                  <p className="agent-description">{agent.description}</p>
                  <div className="agent-capabilities">
                    <strong>Capabilities:</strong>
                    {agent.capabilities?.map((cap, i) => (
                      <div key={i} className="capability-item">
                        <span className="cap-name">{cap.name}</span>
                        <span className="cap-time">~{cap.estimated_duration_seconds}s</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Case Card Component
// =============================================================================

function CaseCard({ caseData, onSelect, onDelete, compact }) {
  const classification = caseData.classification || {}
  const inputData = caseData.input_data || {}
  
  const typeIcon = TYPE_ICONS[caseData.case_type] || '📁'
  const typeColor = TYPE_COLORS[caseData.case_type] || 'var(--text-muted)'
  const urgency = classification.urgency || 'normal'
  const urgencyColor = URGENCY_COLORS[urgency] || URGENCY_COLORS.normal

  const title = inputData.subject || inputData.filename || `${caseData.case_type} case`
  const from = caseData.customer_name || inputData.sender_name || inputData.caller_name || 'Unknown'
  const time = new Date(caseData.created_at).toLocaleString()

  return (
    <div className={`case-card-new ${compact ? 'compact' : ''}`} onClick={onSelect}>
      <div className="card-top">
        <span className="case-type-badge" style={{ background: typeColor }}>
          {typeIcon} {caseData.case_type?.replace('_', ' ')}
        </span>
        {classification.practice_area && (
          <span className="practice-badge">{classification.practice_area}</span>
        )}
      </div>
      
      <h3 className="card-title">{title}</h3>
      <p className="card-from">From: {from}</p>
      
      <div className="card-badges">
        {classification.intent && (
          <span className="mini-badge intent">{classification.intent}</span>
        )}
        {classification.urgency && (
          <span className="mini-badge" style={{ background: urgencyColor }}>{urgency}</span>
        )}
        {caseData.requires_human_review && (
          <span className="mini-badge review">⚠️ Review</span>
        )}
      </div>
      
      {caseData.attachments?.length > 0 && (
        <div className="card-attachments">
          📎 {caseData.attachments.length} attachment(s)
        </div>
      )}
      
      <div className="card-footer">
        <span className="card-time">{time}</span>
        <span className={`card-status ${caseData.status}`}>
          {caseData.status}
        </span>
      </div>

      {onDelete && (
        <button 
          className="delete-btn" 
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          title="Delete case"
        >
          🗑️
        </button>
      )}
      
      <div className="view-detail-hint">Click to view details →</div>
    </div>
  )
}

export default AdminConsole
