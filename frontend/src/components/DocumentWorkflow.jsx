import { useState } from 'react'
import WorkflowResult from './WorkflowResult'

const sampleDocument = {
  document_id: "doc_002",
  filename: "commercial_lease_agreement.pdf",
  file_type: "pdf",
  page_count: 45,
  content: `LEASE OF COMMERCIAL PREMISES

Date: 1 January 2024

PARTIES:
(1) PROPERTY HOLDINGS PLC (Company No. 87654321) ('the Landlord')
(2) RETAIL VENTURES LIMITED (Company No. 11223344) ('the Tenant')

PREMISES: Unit 5, Riverside Business Park, London SE1 9PP

TERM: 10 years from 1 February 2024 to 31 January 2034

RENT: £150,000 per annum (exclusive of VAT)

RENT REVIEW: On the 5th anniversary (1 February 2029)

BREAK CLAUSE: The Tenant may terminate on the 5th anniversary by giving 6 months' prior written notice (notice to be served by 1 August 2028)

REPAIR: Full repairing and insuring lease

USE: Retail (Class E)

ALIENATION: Assignment permitted with Landlord's consent (not to be unreasonably withheld)

KEY DATES:
- Completion: 15 January 2024
- Term commencement: 1 February 2024
- First rent payment: 1 February 2024
- Break notice deadline: 1 August 2028
- Break date: 1 February 2029
- Rent review: 1 February 2029
- Term expiry: 31 January 2034

SERVICE CHARGE: Estimated at £25,000 per annum

DEPOSIT: £75,000 (3 months' rent)

GOVERNING LAW: England and Wales

Land Registry Title Number: NGL123456`
}

function DocumentWorkflow({ serverStatus }) {
  const [formData, setFormData] = useState({
    document_id: '',
    filename: '',
    file_type: 'pdf',
    page_count: 1,
    content: ''
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
      document_id: sampleDocument.document_id,
      filename: sampleDocument.filename,
      file_type: sampleDocument.file_type,
      page_count: sampleDocument.page_count,
      content: sampleDocument.content
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
          workflow_type: 'document_processing',
          input_data: {
            ...formData,
            page_count: parseInt(formData.page_count),
            source: 'frontend'
          }
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process document')
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
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
            Document Classification Workflow
          </h2>
          <button className="sample-data-btn" onClick={loadSampleData}>
            Load Sample Document
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
              <strong>Server not connected.</strong> Start the server with <code>python server.py</code> to process documents.
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Document ID</label>
              <input
                type="text"
                name="document_id"
                className="form-input"
                value={formData.document_id}
                onChange={handleChange}
                placeholder="doc_001"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Filename</label>
              <input
                type="text"
                name="filename"
                className="form-input"
                value={formData.filename}
                onChange={handleChange}
                placeholder="contract.pdf"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">File Type</label>
              <select
                name="file_type"
                className="form-select"
                value={formData.file_type}
                onChange={handleChange}
              >
                <option value="pdf">PDF</option>
                <option value="docx">DOCX</option>
                <option value="doc">DOC</option>
                <option value="txt">TXT</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Page Count</label>
              <input
                type="number"
                name="page_count"
                className="form-input"
                value={formData.page_count}
                onChange={handleChange}
                min="1"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Document Content</label>
            <textarea
              name="content"
              className="form-textarea"
              value={formData.content}
              onChange={handleChange}
              placeholder="Paste the document text content here..."
              required
              style={{ minHeight: '250px' }}
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
                Run Document Workflow
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

      {result && <WorkflowResult result={result} workflowType="document_processing" />}

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
            { agent: 'Document Classification Agent', task: 'Identifies document type, practice area, and extracts metadata', icon: '📄' },
            { agent: 'Deadline Tracker Agent', task: 'Extracts all dates and deadlines from the document', icon: '⏰' },
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

export default DocumentWorkflow
