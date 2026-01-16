import { useState } from 'react'

const TYPE_ICONS = {
  email: '📧',
  voice_call: '📞',
  chat: '💬',
  document: '📄'
}

const URGENCY_COLORS = {
  critical: '#f43f5e',
  high: '#f59e0b',
  normal: '#10b981',
  low: '#64748b'
}

function CaseDetailScreen({ caseData, onBack }) {
  const [activeSection, setActiveSection] = useState('overview')
  
  if (!caseData) return null

  const {
    case_id,
    case_type,
    status,
    input_data = {},
    processing_result = {},
    classification = {},
    created_at,
    processed_at,
    processing_duration_ms,
    customer_name,
    customer_email,
    requires_human_review,
    escalation_reason,
    attachments = []
  } = caseData

  const finalResult = processing_result?.final_result || {}
  const steps = processing_result?.steps || []
  const agentsUsed = processing_result?.agents_used || []

  // Document specific
  const docClassification = finalResult?.classification?.classification || classification || {}
  const docMetadata = finalResult?.classification?.metadata || {}
  const docFlags = finalResult?.classification?.flags || {}
  const deadlinesData = finalResult?.deadlines || {}
  const deadlines = deadlinesData?.deadlines || []
  const reminderSchedules = deadlinesData?.reminder_schedules || []
  const calendarEntries = deadlinesData?.calendar_entries || []
  const deadlineAnalysis = deadlinesData?.analysis || {}

  // Email specific
  const emailTriage = finalResult?.triage || {}
  const draftResponse = finalResult?.draft_response || {}

  const sections = [
    { id: 'overview', label: '📋 Overview', icon: '📋' },
    { id: 'classification', label: '🏷️ Classification', icon: '🏷️' },
    { id: 'content', label: '📝 Content', icon: '📝' },
    { id: 'deadlines', label: '⏰ Deadlines', icon: '⏰' },
    { id: 'processing', label: '🤖 Agent Trace', icon: '🤖' },
  ]

  return (
    <div className="case-detail-screen">
      {/* Header */}
      <div className="detail-screen-header">
        <button className="back-btn" onClick={onBack}>
          ← Back to Cases
        </button>
        <div className="header-info">
          <div className="header-type">
            <span className="type-icon-large">{TYPE_ICONS[case_type] || '📁'}</span>
            <div>
              <h1>{input_data.subject || input_data.filename || `${case_type?.replace('_', ' ')} Case`}</h1>
              <div className="header-meta">
                <span className="case-id">ID: {case_id?.slice(0, 8)}...</span>
                <span className={`status-pill ${status}`}>{status}</span>
                {requires_human_review && <span className="review-pill">⚠️ Needs Review</span>}
              </div>
            </div>
          </div>
          <div className="header-stats">
            <div className="stat-box">
              <span className="stat-label">Created</span>
              <span className="stat-value">{new Date(created_at).toLocaleString()}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Processed</span>
              <span className="stat-value">{processing_duration_ms ? `${processing_duration_ms}ms` : 'N/A'}</span>
            </div>
            <div className="stat-box">
              <span className="stat-label">Agents</span>
              <span className="stat-value">{agentsUsed.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="detail-nav">
        {sections.map(section => (
          <button
            key={section.id}
            className={`nav-item ${activeSection === section.id ? 'active' : ''}`}
            onClick={() => setActiveSection(section.id)}
          >
            {section.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="detail-screen-content">
        {activeSection === 'overview' && (
          <OverviewSection
            caseData={caseData}
            docClassification={docClassification}
            docMetadata={docMetadata}
            docFlags={docFlags}
            emailTriage={emailTriage}
            deadlineAnalysis={deadlineAnalysis}
          />
        )}
        
        {activeSection === 'classification' && (
          <ClassificationSection
            caseType={case_type}
            docClassification={docClassification}
            docMetadata={docMetadata}
            docFlags={docFlags}
            emailTriage={emailTriage}
          />
        )}
        
        {activeSection === 'content' && (
          <ContentSection
            inputData={input_data}
            caseType={case_type}
            draftResponse={draftResponse}
          />
        )}
        
        {activeSection === 'deadlines' && (
          <DeadlinesSection
            deadlines={deadlines}
            reminderSchedules={reminderSchedules}
            calendarEntries={calendarEntries}
            analysis={deadlineAnalysis}
          />
        )}
        
        {activeSection === 'processing' && (
          <ProcessingSection
            steps={steps}
            agentsUsed={agentsUsed}
            totalDuration={processing_duration_ms}
          />
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Overview Section
// =============================================================================

function OverviewSection({ caseData, docClassification, docMetadata, docFlags, emailTriage, deadlineAnalysis }) {
  const classification = emailTriage?.classification || docClassification || {}
  
  return (
    <div className="section-content">
      {/* Quick Stats */}
      <div className="overview-grid">
        <div className="overview-card highlight">
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <span className="card-label">Practice Area</span>
            <span className="card-value">{classification.practice_area || 'N/A'}</span>
          </div>
        </div>
        
        <div className="overview-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <span className="card-label">Confidence</span>
            <span className="card-value">{classification.confidence ? `${Math.round(classification.confidence * 100)}%` : 'N/A'}</span>
          </div>
        </div>
        
        <div className="overview-card">
          <div className="card-icon">📁</div>
          <div className="card-content">
            <span className="card-label">Document Type</span>
            <span className="card-value">{classification.document_type || classification.intent || 'N/A'}</span>
          </div>
        </div>
        
        <div className="overview-card">
          <div className="card-icon">⏰</div>
          <div className="card-content">
            <span className="card-label">Deadlines Found</span>
            <span className="card-value">{deadlineAnalysis?.total_deadlines || 0}</span>
          </div>
        </div>
      </div>

      {/* Parties */}
      {docMetadata.parties && docMetadata.parties.length > 0 && (
        <div className="info-section">
          <h3>👥 Parties Involved</h3>
          <div className="parties-grid">
            {docMetadata.parties.map((party, idx) => (
              <div key={idx} className="party-card">
                <span className="party-icon">{idx === 0 ? '🏢' : '🏪'}</span>
                <span className="party-name">{party}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Terms */}
      {docMetadata.key_terms && docMetadata.key_terms.length > 0 && (
        <div className="info-section">
          <h3>📋 Key Terms</h3>
          <div className="key-terms-list">
            {docMetadata.key_terms.map((term, idx) => (
              <div key={idx} className="key-term">
                <span className="term-bullet">•</span>
                <span className="term-text">{term}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Flags */}
      {Object.values(docFlags).some(v => v === true) && (
        <div className="info-section">
          <h3>🚩 Flags & Warnings</h3>
          <div className="flags-grid">
            {Object.entries(docFlags).map(([key, value]) => {
              if (value === true && key !== 'flagged_clauses') {
                return (
                  <div key={key} className={`flag-badge ${key.includes('sensitive') || key.includes('confidential') ? 'warning' : 'info'}`}>
                    {key.includes('financial') && '💰'}
                    {key.includes('pii') && '🔐'}
                    {key.includes('time') && '⏱️'}
                    {key.includes('witness') && '✍️'}
                    {key.replace(/_/g, ' ')}
                  </div>
                )
              }
              return null
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Classification Section
// =============================================================================

function ClassificationSection({ caseType, docClassification, docMetadata, docFlags, emailTriage }) {
  const isDocument = caseType === 'document'
  const classification = isDocument ? docClassification : (emailTriage?.classification || {})
  const extractedData = emailTriage?.extracted_data || {}

  return (
    <div className="section-content">
      {/* Main Classification */}
      <div className="classification-hero">
        <div className="class-main">
          <span className="class-type">{classification.document_type || classification.intent || 'Unknown'}</span>
          {classification.document_subtype && (
            <span className="class-subtype">{classification.document_subtype}</span>
          )}
        </div>
        <div className="class-meta">
          <div className="meta-item">
            <span className="meta-label">Practice Area</span>
            <span className="meta-value accent">{classification.practice_area || 'N/A'}</span>
          </div>
          <div className="meta-item">
            <span className="meta-label">Confidence</span>
            <div className="confidence-bar">
              <div 
                className="confidence-fill" 
                style={{ width: `${(classification.confidence || 0) * 100}%` }}
              />
              <span className="confidence-text">{Math.round((classification.confidence || 0) * 100)}%</span>
            </div>
          </div>
          {classification.urgency && (
            <div className="meta-item">
              <span className="meta-label">Urgency</span>
              <span className="urgency-badge" style={{ background: URGENCY_COLORS[classification.urgency] }}>
                {classification.urgency}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Reasoning */}
      {classification.reasoning && (
        <div className="info-section">
          <h3>💭 AI Reasoning</h3>
          <div className="reasoning-box">
            {classification.reasoning}
          </div>
        </div>
      )}

      {/* Document Status */}
      {isDocument && (
        <div className="info-section">
          <h3>📊 Document Status</h3>
          <div className="status-grid">
            <StatusBadge label="Template" value={classification.is_template} />
            <StatusBadge label="Executed" value={classification.is_executed} />
            <StatusBadge label="Draft" value={classification.is_draft} />
            <StatusBadge label="Language" value={classification.language} isText />
          </div>
        </div>
      )}

      {/* Metadata Table */}
      {docMetadata && Object.keys(docMetadata).length > 0 && (
        <div className="info-section">
          <h3>📑 Document Metadata</h3>
          <div className="metadata-table">
            {docMetadata.title && <MetadataRow label="Title" value={docMetadata.title} />}
            {docMetadata.date && <MetadataRow label="Date" value={docMetadata.date} />}
            {docMetadata.effective_date && <MetadataRow label="Effective Date" value={docMetadata.effective_date} />}
            {docMetadata.expiry_date && <MetadataRow label="Expiry Date" value={docMetadata.expiry_date} />}
            {docMetadata.jurisdiction && <MetadataRow label="Jurisdiction" value={docMetadata.jurisdiction} />}
            {docMetadata.governing_law && <MetadataRow label="Governing Law" value={docMetadata.governing_law} />}
            {docMetadata.references && docMetadata.references.length > 0 && (
              <MetadataRow label="References" value={docMetadata.references.join(', ')} />
            )}
          </div>
        </div>
      )}

      {/* Extracted Data (for emails) */}
      {Object.keys(extractedData).length > 0 && (
        <div className="info-section">
          <h3>📋 Extracted Information</h3>
          <div className="metadata-table">
            {Object.entries(extractedData).map(([key, value]) => {
              if (value && typeof value !== 'object') {
                return <MetadataRow key={key} label={key.replace(/_/g, ' ')} value={value} />
              }
              return null
            })}
          </div>
        </div>
      )}

      {/* Suggested Actions */}
      {docClassification?.next_actions && docClassification.next_actions.length > 0 && (
        <div className="info-section">
          <h3>📌 Suggested Next Actions</h3>
          <div className="actions-list">
            {docClassification.next_actions.map((action, idx) => (
              <div key={idx} className="action-item">
                <span className="action-number">{idx + 1}</span>
                <span className="action-text">{action.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Content Section
// =============================================================================

function ContentSection({ inputData, caseType, draftResponse }) {
  const content = inputData.body || inputData.content || ''
  
  return (
    <div className="section-content">
      {/* Original Content */}
      <div className="info-section">
        <h3>📄 Original {caseType === 'document' ? 'Document' : 'Message'} Content</h3>
        <div className="content-viewer">
          <div className="content-header">
            {inputData.filename && <span>📁 {inputData.filename}</span>}
            {inputData.subject && <span>📧 {inputData.subject}</span>}
            {inputData.file_type && <span className="file-type">{inputData.file_type.toUpperCase()}</span>}
            {inputData.page_count && <span>{inputData.page_count} pages</span>}
          </div>
          <pre className="content-body">{content}</pre>
        </div>
      </div>

      {/* Draft Response (for emails) */}
      {draftResponse?.body && (
        <div className="info-section">
          <h3>✍️ AI Generated Response Draft</h3>
          <div className="draft-response">
            {draftResponse.subject && (
              <div className="draft-subject">
                <strong>Subject:</strong> {draftResponse.subject}
              </div>
            )}
            <div className="draft-body">{draftResponse.body}</div>
          </div>
        </div>
      )}

      {/* Attachments */}
      {inputData.attachments && inputData.attachments.length > 0 && (
        <div className="info-section">
          <h3>📎 Attachments ({inputData.attachments.length})</h3>
          <div className="attachments-grid">
            {inputData.attachments.map((att, idx) => (
              <div key={idx} className="attachment-card">
                <span className="att-icon">
                  {att.endsWith('.pdf') ? '📕' : 
                   att.endsWith('.docx') ? '📘' : 
                   att.endsWith('.xlsx') ? '📗' : '📄'}
                </span>
                <span className="att-name">{att}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Deadlines Section
// =============================================================================

function DeadlinesSection({ deadlines, reminderSchedules, calendarEntries, analysis }) {
  const [expandedDeadline, setExpandedDeadline] = useState(null)

  if (deadlines.length === 0) {
    return (
      <div className="section-content">
        <div className="empty-deadlines">
          <span className="empty-icon">📅</span>
          <h3>No Deadlines Found</h3>
          <p>The AI agent did not detect any deadlines in this document.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="section-content">
      {/* Deadline Stats */}
      <div className="deadline-stats">
        <div className="deadline-stat">
          <span className="stat-number">{analysis.total_deadlines || deadlines.length}</span>
          <span className="stat-text">Total Deadlines</span>
        </div>
        <div className="deadline-stat critical">
          <span className="stat-number">{analysis.by_priority?.critical || 0}</span>
          <span className="stat-text">Critical</span>
        </div>
        <div className="deadline-stat high">
          <span className="stat-number">{analysis.by_priority?.high || 0}</span>
          <span className="stat-text">High Priority</span>
        </div>
        <div className="deadline-stat">
          <span className="stat-number">{analysis.upcoming_30_days || 0}</span>
          <span className="stat-text">Next 30 Days</span>
        </div>
      </div>

      {/* Timeline */}
      <div className="info-section">
        <h3>📅 Deadline Timeline</h3>
        <div className="deadline-timeline">
          {deadlines.sort((a, b) => new Date(a.date) - new Date(b.date)).map((dl, idx) => {
            const isExpanded = expandedDeadline === dl.deadline_id
            const reminders = reminderSchedules.find(r => r.deadline_id === dl.deadline_id)?.reminders || []
            
            return (
              <div 
                key={dl.deadline_id} 
                className={`timeline-item ${isExpanded ? 'expanded' : ''}`}
                onClick={() => setExpandedDeadline(isExpanded ? null : dl.deadline_id)}
              >
                <div className="timeline-marker">
                  <div className="marker-dot" />
                  {idx < deadlines.length - 1 && <div className="marker-line" />}
                </div>
                <div className="timeline-content">
                  <div className="timeline-header">
                    <span className="timeline-date">{dl.date}</span>
                    <span className={`deadline-type ${dl.date_type}`}>{dl.date_type}</span>
                  </div>
                  <h4 className="timeline-title">{dl.description}</h4>
                  <div className="timeline-meta">
                    {dl.related_party && <span>👤 {dl.related_party}</span>}
                    <span>🎯 {Math.round((dl.confidence || 0) * 100)}% confidence</span>
                  </div>
                  
                  {isExpanded && (
                    <div className="timeline-expanded">
                      {dl.source_text && (
                        <div className="source-text">
                          <strong>Source:</strong> "{dl.source_text}"
                        </div>
                      )}
                      {dl.consequence_of_missing && (
                        <div className="consequence">
                          <strong>⚠️ If Missed:</strong> {dl.consequence_of_missing}
                        </div>
                      )}
                      {reminders.length > 0 && (
                        <div className="reminders">
                          <strong>📢 Scheduled Reminders:</strong>
                          <div className="reminder-list">
                            {reminders.map((r, rIdx) => (
                              <div key={rIdx} className="reminder-item">
                                <span className="reminder-date">{r.date}</span>
                                <span className="reminder-days">{r.days_before}d before</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Calendar Export */}
      {calendarEntries.length > 0 && (
        <div className="info-section">
          <h3>📆 Calendar Entries</h3>
          <div className="calendar-entries">
            {calendarEntries.map((entry, idx) => (
              <div key={idx} className="calendar-card">
                <div className="cal-date">{entry.date}</div>
                <div className="cal-title">{entry.title}</div>
                <div className="cal-desc">{entry.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// Processing Section
// =============================================================================

function ProcessingSection({ steps, agentsUsed, totalDuration }) {
  const [expandedStep, setExpandedStep] = useState(null)

  const agentNames = {
    'email_triage_agent': { name: 'Email Triage Agent', icon: '📧' },
    'document_classification_agent': { name: 'Document Classification Agent', icon: '📄' },
    'client_intake_agent': { name: 'Client Intake Agent', icon: '👥' },
    'deadline_tracker_agent': { name: 'Deadline Tracker Agent', icon: '⏰' },
    'response_generator_agent': { name: 'Response Generator Agent', icon: '✍️' },
    'orchestrator_agent': { name: 'Orchestrator Agent', icon: '🎯' }
  }

  return (
    <div className="section-content">
      {/* Processing Summary */}
      <div className="processing-summary">
        <div className="proc-stat">
          <span className="proc-value">{steps.length}</span>
          <span className="proc-label">Steps Executed</span>
        </div>
        <div className="proc-stat">
          <span className="proc-value">{agentsUsed.length}</span>
          <span className="proc-label">Agents Involved</span>
        </div>
        <div className="proc-stat">
          <span className="proc-value">{totalDuration || 0}ms</span>
          <span className="proc-label">Total Duration</span>
        </div>
      </div>

      {/* Agents Used */}
      <div className="info-section">
        <h3>🤖 Agents Invoked</h3>
        <div className="agents-row">
          {agentsUsed.map((agentId, idx) => {
            const agent = agentNames[agentId] || { name: agentId, icon: '🤖' }
            return (
              <div key={agentId} className="agent-badge">
                <span className="agent-icon">{agent.icon}</span>
                <span className="agent-name">{agent.name}</span>
                {idx < agentsUsed.length - 1 && <span className="agent-arrow">→</span>}
              </div>
            )
          })}
        </div>
      </div>

      {/* Step by Step */}
      <div className="info-section">
        <h3>📋 Execution Steps</h3>
        <div className="steps-list">
          {steps.map((step, idx) => {
            const agent = agentNames[step.agent_id] || { name: step.agent_id, icon: '🤖' }
            const isExpanded = expandedStep === step.step_id

            return (
              <div 
                key={step.step_id} 
                className={`step-card ${step.status} ${isExpanded ? 'expanded' : ''}`}
              >
                <div className="step-header" onClick={() => setExpandedStep(isExpanded ? null : step.step_id)}>
                  <div className="step-left">
                    <span className={`step-number ${step.status}`}>
                      {step.status === 'completed' ? '✓' : step.status === 'failed' ? '✗' : idx + 1}
                    </span>
                    <div className="step-info">
                      <span className="step-agent-name">{agent.icon} {agent.name}</span>
                      <span className="step-task">{step.task_type?.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                  <div className="step-right">
                    <span className="step-duration">{step.duration_ms}ms</span>
                    <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                  </div>
                </div>
                
                {isExpanded && step.result && (
                  <div className="step-result">
                    <pre>{JSON.stringify(step.result, null, 2)}</pre>
                  </div>
                )}
                
                {step.error && (
                  <div className="step-error">
                    ❌ Error: {step.error}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// Helper Components
// =============================================================================

function StatusBadge({ label, value, isText }) {
  if (isText) {
    return (
      <div className="status-item">
        <span className="status-label">{label}</span>
        <span className="status-value">{value || 'N/A'}</span>
      </div>
    )
  }
  return (
    <div className="status-item">
      <span className="status-label">{label}</span>
      <span className={`status-indicator ${value ? 'yes' : 'no'}`}>
        {value ? '✓ Yes' : '✗ No'}
      </span>
    </div>
  )
}

function MetadataRow({ label, value }) {
  return (
    <div className="metadata-row">
      <span className="meta-label">{label}</span>
      <span className="meta-value">{value}</span>
    </div>
  )
}

export default CaseDetailScreen
