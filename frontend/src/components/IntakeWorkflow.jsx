import { useState } from 'react'
import WorkflowResult from './WorkflowResult'

const sampleIntake = {
  inquiry_id: "inq_001",
  client_name: "Emma Wilson",
  client_type: "individual",
  contact_email: "emma.wilson@email.com",
  contact_phone: "07700 900123",
  matter_description: `I was dismissed from my job at Global Finance Ltd last week after raising concerns about irregular accounting practices. I believe this is unfair dismissal and possibly whistleblower retaliation. I was employed there for 5 years as a Senior Accountant. They claim it was redundancy but nobody else was made redundant and they've already advertised my role. I need advice on whether I have a claim and what the time limits are.`,
  practice_area: "employment",
  urgency: "high",
  opposing_parties: "Global Finance Ltd",
  referral_source: "Google search",
  budget_indication: "Up to £10,000"
}

function IntakeWorkflow({ serverStatus }) {
  const [formData, setFormData] = useState({
    inquiry_id: '',
    client_name: '',
    client_type: 'individual',
    contact_email: '',
    contact_phone: '',
    matter_description: '',
    practice_area: '',
    urgency: 'normal',
    opposing_parties: '',
    referral_source: '',
    budget_indication: ''
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
    setFormData(sampleIntake)
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
          workflow_type: 'new_client_intake',
          input_data: {
            ...formData,
            opposing_parties: formData.opposing_parties.split(',').map(p => p.trim()).filter(Boolean),
            source: 'frontend'
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process intake')
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
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Client Intake Workflow
          </h2>
          <button className="sample-data-btn" onClick={loadSampleData}>
            Load Sample Inquiry
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
              <strong>Server not connected.</strong> Start the server with <code>python server.py</code> to process intakes.
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Inquiry ID</label>
              <input
                type="text"
                name="inquiry_id"
                className="form-input"
                value={formData.inquiry_id}
                onChange={handleChange}
                placeholder="inq_001"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Client Name</label>
              <input
                type="text"
                name="client_name"
                className="form-input"
                value={formData.client_name}
                onChange={handleChange}
                placeholder="John Smith"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Client Type</label>
              <select
                name="client_type"
                className="form-select"
                value={formData.client_type}
                onChange={handleChange}
              >
                <option value="individual">Individual</option>
                <option value="company">Company</option>
                <option value="partnership">Partnership</option>
                <option value="charity">Charity</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Urgency</label>
              <select
                name="urgency"
                className="form-select"
                value={formData.urgency}
                onChange={handleChange}
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                name="contact_email"
                className="form-input"
                value={formData.contact_email}
                onChange={handleChange}
                placeholder="client@email.com"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone</label>
              <input
                type="tel"
                name="contact_phone"
                className="form-input"
                value={formData.contact_phone}
                onChange={handleChange}
                placeholder="+44 7700 900123"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Practice Area</label>
              <select
                name="practice_area"
                className="form-select"
                value={formData.practice_area}
                onChange={handleChange}
              >
                <option value="">-- Select --</option>
                <option value="employment">Employment</option>
                <option value="commercial">Commercial</option>
                <option value="property">Property</option>
                <option value="litigation">Litigation</option>
                <option value="corporate">Corporate</option>
                <option value="family">Family</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Budget Indication</label>
              <input
                type="text"
                name="budget_indication"
                className="form-input"
                value={formData.budget_indication}
                onChange={handleChange}
                placeholder="Up to £5,000"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Opposing Parties (comma-separated)</label>
            <input
              type="text"
              name="opposing_parties"
              className="form-input"
              value={formData.opposing_parties}
              onChange={handleChange}
              placeholder="Company Ltd, John Doe"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Referral Source</label>
            <input
              type="text"
              name="referral_source"
              className="form-input"
              value={formData.referral_source}
              onChange={handleChange}
              placeholder="Google, Referral, etc."
            />
          </div>

          <div className="form-group">
            <label className="form-label">Matter Description</label>
            <textarea
              name="matter_description"
              className="form-textarea"
              value={formData.matter_description}
              onChange={handleChange}
              placeholder="Describe the legal matter in detail..."
              required
              style={{ minHeight: '150px' }}
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
                Run Intake Workflow
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

      {result && <WorkflowResult result={result} workflowType="new_client_intake" />}

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
            { agent: 'Client Intake Agent', task: 'Runs conflict check, risk assessment, and fee estimation', icon: '👥' },
            { agent: 'Response Generator Agent', task: 'Creates engagement letter if approved', icon: '✍️' },
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

export default IntakeWorkflow
