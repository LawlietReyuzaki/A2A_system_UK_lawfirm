import { useState } from 'react'
import WorkflowResult from './WorkflowResult'

const sampleEmail = {
  email_id: "email_001",
  sender_email: "john.smith@techcorp.co.uk",
  sender_name: "John Smith",
  subject: "Urgent: Employment Contract Review Needed",
  body: `Dear BrightLaw Team,

I am the HR Director at TechCorp Ltd and we urgently need assistance with reviewing our standard employment contracts. We are planning to hire 15 new developers next month and want to ensure our contracts are compliant with current UK employment law.

Specifically, we need help with:
1. Non-compete clauses - are ours enforceable?
2. IP assignment provisions
3. Remote working policies
4. Garden leave provisions

We were referred to you by ABC Properties Ltd who spoke highly of your employment team.

Could someone please get back to me by end of this week? We have a board meeting on Monday where I need to present the updated contracts.

Best regards,
John Smith
HR Director, TechCorp Ltd
Company No: 12345678`,
  attachments: ["current_employment_contract.docx"]
}

function EmailWorkflow({ serverStatus }) {
  const [formData, setFormData] = useState({
    email_id: '',
    sender_email: '',
    sender_name: '',
    subject: '',
    body: '',
    attachments: ''
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const loadSampleData = () => {
    setFormData({
      email_id: sampleEmail.email_id,
      sender_email: sampleEmail.sender_email,
      sender_name: sampleEmail.sender_name,
      subject: sampleEmail.subject,
      body: sampleEmail.body,
      attachments: sampleEmail.attachments.join(', ')
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/workflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_type: 'email_processing',
          input_data: {
            ...formData,
            attachments: formData.attachments.split(',').map(a => a.trim()).filter(Boolean),
            received_at: new Date().toISOString(),
            is_reply: false
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process email')
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            Email Triage Workflow
          </h2>
          <button className="sample-data-btn" onClick={loadSampleData}>
            Load Sample Email
          </button>
        </div>

        {serverStatus.status !== 'online' && (
          <div className="alert alert-warning">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <div>
              <strong>Server not connected.</strong> Start the server with <code>python server.py</code> to process emails.
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Email ID</label>
              <input
                type="text"
                name="email_id"
                className="form-input"
                value={formData.email_id}
                onChange={handleChange}
                placeholder="email_001"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Sender Email</label>
              <input
                type="email"
                name="sender_email"
                className="form-input"
                value={formData.sender_email}
                onChange={handleChange}
                placeholder="john@example.com"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Sender Name</label>
              <input
                type="text"
                name="sender_name"
                className="form-input"
                value={formData.sender_name}
                onChange={handleChange}
                placeholder="John Smith"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Attachments (comma-separated)</label>
              <input
                type="text"
                name="attachments"
                className="form-input"
                value={formData.attachments}
                onChange={handleChange}
                placeholder="contract.pdf, invoice.docx"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Subject</label>
            <input
              type="text"
              name="subject"
              className="form-input"
              value={formData.subject}
              onChange={handleChange}
              placeholder="Email subject line"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email Body</label>
            <textarea
              name="body"
              className="form-textarea"
              value={formData.body}
              onChange={handleChange}
              placeholder="Paste the email content here..."
              required
              style={{ minHeight: '200px' }}
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading || serverStatus.status !== 'online'}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: '16px', height: '16px' }}></span>
                Processing...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Run Email Workflow
              </>
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="alert alert-error">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <div>
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      {result && <WorkflowResult result={result} workflowType="email_processing" />}

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            What This Workflow Does
          </h2>
        </div>
        
        <div style={{ display: 'grid', gap: '1rem' }}>
          {[
            { agent: 'Email Triage Agent', task: 'Classifies intent, urgency, and practice area', icon: '📧' },
            { agent: 'Client Intake Agent', task: 'Triggered if new client detected', icon: '👥' },
            { agent: 'Deadline Tracker Agent', task: 'Extracts any mentioned deadlines', icon: '⏰' },
            { agent: 'Response Generator Agent', task: 'Creates draft reply', icon: '✍️' },
          ].map((step, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              padding: '1rem',
              background: 'var(--bg-secondary)',
              borderRadius: '8px'
            }}>
              <div style={{
                width: '44px',
                height: '44px',
                background: 'var(--bg-card)',
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem'
              }}>
                {step.icon}
              </div>
              <div>
                <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{step.agent}</div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{step.task}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

export default EmailWorkflow
