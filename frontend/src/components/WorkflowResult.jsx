import { useState } from 'react'

const agentNames = {
  'email_triage_agent': 'Email Triage Agent',
  'document_classification_agent': 'Document Classification Agent',
  'client_intake_agent': 'Client Intake Agent',
  'deadline_tracker_agent': 'Deadline Tracker Agent',
  'response_generator_agent': 'Response Generator Agent',
  'orchestrator_agent': 'Orchestrator Agent'
}

function WorkflowResult({ result, workflowType }) {
  const [showRaw, setShowRaw] = useState(false)
  const [expandedSteps, setExpandedSteps] = useState({})

  const toggleStep = (stepId) => {
    setExpandedSteps(prev => ({
      ...prev,
      [stepId]: !prev[stepId]
    }))
  }

  const steps = result.result?.steps || []
  const finalResult = result.result?.final_result || {}

  return (
    <div className="workflow-result">
      <div className="workflow-header">
        <div className={`workflow-status ${result.status}`}>
          {result.status === 'completed' ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          )}
          {result.status?.toUpperCase() || 'UNKNOWN'}
        </div>
        <div className="workflow-meta">
          <span>⏱️ {result.execution_time_ms || result.result?.total_duration_ms || 0}ms</span>
          <span>🤖 {result.result?.agents_used?.length || 0} agents</span>
          {result.requires_human_review && (
            <span style={{ color: 'var(--accent-amber)' }}>👁️ Review Required</span>
          )}
        </div>
      </div>

      {/* Workflow Steps */}
      <div className="workflow-steps">
        <h3 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
          Execution Steps ({steps.length})
        </h3>
        
        {steps.map((step, idx) => (
          <div key={step.step_id || idx} className="step-item">
            <div className={`step-number ${step.status}`}>
              {step.status === 'completed' ? '✓' : step.status === 'failed' ? '✗' : idx + 1}
            </div>
            <div className="step-content">
              <div className="step-header">
                <span className="step-agent">
                  {agentNames[step.agent_id] || step.agent_id}
                </span>
                <span className="step-duration">{step.duration_ms}ms</span>
              </div>
              <div className="step-task">
                Task: <code style={{ color: 'var(--accent-cyan)' }}>{step.task_type}</code>
              </div>
              
              {step.result && (
                <button
                  onClick={() => toggleStep(step.step_id || idx)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-blue)',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    padding: '0.25rem 0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}
                >
                  {expandedSteps[step.step_id || idx] ? '▼ Hide' : '▶ Show'} Result
                </button>
              )}
              
              {expandedSteps[step.step_id || idx] && step.result && (
                <div className="step-result">
                  <pre style={{ margin: 0 }}>
                    {JSON.stringify(step.result, null, 2)}
                  </pre>
                </div>
              )}
              
              {step.error && (
                <div style={{ 
                  background: 'rgba(244, 63, 94, 0.1)', 
                  padding: '0.5rem', 
                  borderRadius: '4px',
                  color: 'var(--accent-rose)',
                  fontSize: '0.8125rem',
                  marginTop: '0.5rem'
                }}>
                  Error: {step.error}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Final Result Summary */}
      <div className="final-result">
        <div className="final-result-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '0.5rem' }}>
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Final Result
        </div>
        <div className="final-result-content">
          {renderFinalResult(finalResult, workflowType)}
          
          <div style={{ marginTop: '1.5rem' }}>
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="btn btn-secondary"
              style={{ fontSize: '0.8125rem', padding: '0.5rem 1rem' }}
            >
              {showRaw ? 'Hide' : 'Show'} Raw JSON
            </button>
            
            {showRaw && (
              <div className="result-json" style={{ marginTop: '1rem' }}>
                {JSON.stringify(result, null, 2)}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function renderFinalResult(finalResult, workflowType) {
  switch (workflowType) {
    case 'email_processing':
      return <EmailResult data={finalResult} />
    case 'document_processing':
      return <DocumentResult data={finalResult} />
    case 'new_client_intake':
      return <IntakeResult data={finalResult} />
    default:
      return (
        <div className="result-json">
          {JSON.stringify(finalResult, null, 2)}
        </div>
      )
  }
}

function EmailResult({ data }) {
  const triage = data.triage || {}
  const draftResponse = data.draft_response || {}
  const deadlines = data.deadlines || {}

  return (
    <>
      {/* Triage Results */}
      {triage.classification && (
        <div className="result-section">
          <h4 className="result-section-title">📧 Email Classification</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <ResultBadge label="Intent" value={triage.classification.intent} color="var(--accent-blue)" />
            <ResultBadge label="Urgency" value={triage.classification.urgency} color={
              triage.classification.urgency === 'critical' ? 'var(--accent-rose)' :
              triage.classification.urgency === 'high' ? 'var(--accent-amber)' : 'var(--accent-emerald)'
            } />
            <ResultBadge label="Practice Area" value={triage.classification.practice_area} color="var(--accent-purple)" />
            <ResultBadge label="Confidence" value={`${Math.round((triage.classification.confidence || 0) * 100)}%`} color="var(--accent-cyan)" />
          </div>
        </div>
      )}

      {/* Extracted Data */}
      {triage.extracted_data && Object.keys(triage.extracted_data).length > 0 && (
        <div className="result-section">
          <h4 className="result-section-title">📋 Extracted Information</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            {Object.entries(triage.extracted_data).map(([key, value]) => (
              value && (
                <div key={key} className="result-item">
                  <span className="result-label">{key.replace(/_/g, ' ')}</span>
                  <span className="result-value">{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Deadlines */}
      {deadlines.deadlines && deadlines.deadlines.length > 0 && (
        <div className="result-section">
          <h4 className="result-section-title">⏰ Deadlines Found ({deadlines.deadlines.length})</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            {deadlines.deadlines.slice(0, 5).map((dl, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '0.5rem 0',
                borderBottom: idx < Math.min(deadlines.deadlines.length - 1, 4) ? '1px solid var(--border-color)' : 'none'
              }}>
                <span style={{ 
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.8125rem',
                  color: 'var(--accent-amber)'
                }}>
                  {dl.date}
                </span>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {dl.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Draft Response */}
      {draftResponse.body && (
        <div className="result-section">
          <h4 className="result-section-title">✍️ Generated Response Draft</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            {draftResponse.subject && (
              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Subject:</span>
                <div style={{ fontWeight: '500' }}>{draftResponse.subject}</div>
              </div>
            )}
            <div style={{ 
              whiteSpace: 'pre-wrap', 
              fontSize: '0.875rem', 
              color: 'var(--text-secondary)',
              lineHeight: '1.7'
            }}>
              {draftResponse.body}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function DocumentResult({ data }) {
  const classification = data.classification || {}
  const deadlines = data.deadlines || {}

  return (
    <>
      {/* Classification */}
      {classification.classification && (
        <div className="result-section">
          <h4 className="result-section-title">📄 Document Classification</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <ResultBadge label="Type" value={classification.classification.document_type} color="var(--accent-emerald)" />
            <ResultBadge label="Subtype" value={classification.classification.document_subtype} color="var(--accent-cyan)" />
            <ResultBadge label="Practice Area" value={classification.classification.practice_area} color="var(--accent-purple)" />
            <ResultBadge label="Confidence" value={`${Math.round((classification.classification.confidence || 0) * 100)}%`} color="var(--accent-blue)" />
          </div>
        </div>
      )}

      {/* Metadata */}
      {classification.metadata && Object.keys(classification.metadata).length > 0 && (
        <div className="result-section">
          <h4 className="result-section-title">📋 Extracted Metadata</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            {Object.entries(classification.metadata).map(([key, value]) => (
              value && (
                <div key={key} className="result-item">
                  <span className="result-label">{key.replace(/_/g, ' ')}</span>
                  <span className="result-value">
                    {Array.isArray(value) ? value.join(', ') : value}
                  </span>
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Flags */}
      {classification.flags && Object.values(classification.flags).some(v => v) && (
        <div className="result-section">
          <h4 className="result-section-title">⚠️ Sensitivity Flags</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {Object.entries(classification.flags).map(([key, value]) => (
              value && key !== 'flagged_clauses' && (
                <span key={key} style={{
                  background: 'rgba(244, 63, 94, 0.2)',
                  color: 'var(--accent-rose)',
                  padding: '0.375rem 0.75rem',
                  borderRadius: '6px',
                  fontSize: '0.8125rem'
                }}>
                  {key.replace(/_/g, ' ')}
                </span>
              )
            ))}
          </div>
        </div>
      )}

      {/* Deadlines */}
      {deadlines.deadlines && deadlines.deadlines.length > 0 && (
        <div className="result-section">
          <h4 className="result-section-title">⏰ Key Dates & Deadlines</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            {deadlines.deadlines.map((dl, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '0.5rem 0',
                borderBottom: idx < deadlines.deadlines.length - 1 ? '1px solid var(--border-color)' : 'none'
              }}>
                <span style={{ 
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: '0.8125rem',
                  color: 'var(--accent-amber)',
                  minWidth: '100px'
                }}>
                  {dl.date}
                </span>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {dl.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}

function IntakeResult({ data }) {
  const intake = data.intake || {}

  return (
    <>
      {/* Conflict Check */}
      {intake.conflict_check && (
        <div className="result-section">
          <h4 className="result-section-title">🔍 Conflict Check</h4>
          <div style={{ 
            background: intake.conflict_check.can_proceed 
              ? 'rgba(16, 185, 129, 0.1)' 
              : 'rgba(244, 63, 94, 0.1)',
            borderRadius: '8px',
            padding: '1rem',
            border: `1px solid ${intake.conflict_check.can_proceed ? 'var(--accent-emerald)' : 'var(--accent-rose)'}`
          }}>
            <div style={{ 
              fontSize: '1.25rem', 
              fontWeight: '600',
              color: intake.conflict_check.can_proceed ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              marginBottom: '0.5rem'
            }}>
              {intake.conflict_check.can_proceed ? '✓ Clear - Can Proceed' : '✗ Conflicts Found'}
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Status: {intake.conflict_check.status}
            </div>
          </div>
        </div>
      )}

      {/* Risk Assessment */}
      {intake.risk_assessment && (
        <div className="result-section">
          <h4 className="result-section-title">⚖️ Risk Assessment</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
            <ResultBadge 
              label="Overall Risk" 
              value={intake.risk_assessment.overall_risk?.toUpperCase()} 
              color={
                intake.risk_assessment.overall_risk === 'high' ? 'var(--accent-rose)' :
                intake.risk_assessment.overall_risk === 'medium' ? 'var(--accent-amber)' : 'var(--accent-emerald)'
              } 
            />
            <ResultBadge 
              label="Senior Review" 
              value={intake.risk_assessment.requires_senior_review ? 'Required' : 'Not Required'} 
              color={intake.risk_assessment.requires_senior_review ? 'var(--accent-amber)' : 'var(--accent-emerald)'} 
            />
          </div>
          {intake.risk_assessment.risk_factors && intake.risk_assessment.risk_factors.length > 0 && (
            <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Risk Factors:</div>
              {intake.risk_assessment.risk_factors.map((factor, idx) => (
                <div key={idx} style={{ 
                  fontSize: '0.875rem', 
                  color: 'var(--text-secondary)',
                  padding: '0.25rem 0',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.5rem'
                }}>
                  <span style={{ color: 'var(--accent-amber)' }}>•</span>
                  {factor}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Fee Estimate */}
      {intake.fee_estimate && (
        <div className="result-section">
          <h4 className="result-section-title">💰 Fee Estimate</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: '700',
              color: 'var(--accent-emerald)',
              marginBottom: '0.5rem'
            }}>
              £{(intake.fee_estimate.low_estimate_gbp || 0).toLocaleString()} - £{(intake.fee_estimate.high_estimate_gbp || 0).toLocaleString()}
              <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: '400' }}> + VAT</span>
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Type: {intake.fee_estimate.estimate_type}
            </div>
            {intake.fee_estimate.assumptions && (
              <div style={{ marginTop: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Assumptions:</div>
                {intake.fee_estimate.assumptions.map((assumption, idx) => (
                  <div key={idx} style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                    • {assumption}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Next Steps */}
      {intake.next_steps && intake.next_steps.length > 0 && (
        <div className="result-section">
          <h4 className="result-section-title">📋 Next Steps</h4>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '1rem' }}>
            {intake.next_steps.map((step, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '0.5rem 0',
                borderBottom: idx < intake.next_steps.length - 1 ? '1px solid var(--border-color)' : 'none'
              }}>
                <span style={{
                  width: '24px',
                  height: '24px',
                  background: 'var(--accent-blue)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  color: 'white',
                  flexShrink: 0
                }}>
                  {idx + 1}
                </span>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decision */}
      {intake.can_proceed !== undefined && (
        <div className="result-section">
          <h4 className="result-section-title">✅ Intake Decision</h4>
          <div style={{
            background: intake.can_proceed 
              ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.1))'
              : 'rgba(244, 63, 94, 0.1)',
            borderRadius: '12px',
            padding: '1.5rem',
            textAlign: 'center',
            border: `2px solid ${intake.can_proceed ? 'var(--accent-emerald)' : 'var(--accent-rose)'}`
          }}>
            <div style={{ 
              fontSize: '1.5rem', 
              fontWeight: '700',
              color: intake.can_proceed ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              marginBottom: '0.5rem'
            }}>
              {intake.can_proceed ? '✓ APPROVED' : '✗ DECLINED'}
            </div>
            <div style={{ fontSize: '0.9375rem', color: 'var(--text-secondary)' }}>
              {intake.can_proceed 
                ? 'Proceed with client onboarding'
                : intake.decline_reason || 'See risk assessment for details'}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function ResultBadge({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: '8px',
      padding: '0.875rem',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: '1rem', fontWeight: '600', color: color || 'var(--text-primary)' }}>
        {value || 'N/A'}
      </div>
    </div>
  )
}

export default WorkflowResult
