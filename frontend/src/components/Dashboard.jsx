import { useState } from 'react'

const agentIcons = {
  'email_triage_agent': { icon: '📧', class: 'email' },
  'document_classification_agent': { icon: '📄', class: 'document' },
  'client_intake_agent': { icon: '👥', class: 'intake' },
  'deadline_tracker_agent': { icon: '⏰', class: 'deadline' },
  'response_generator_agent': { icon: '✍️', class: 'response' },
  'orchestrator_agent': { icon: '🎯', class: 'orchestrator' }
}

function Dashboard({ agents, serverStatus }) {
  const [selectedAgent, setSelectedAgent] = useState(null)

  if (serverStatus.status !== 'online') {
    return (
      <div className="card">
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <h3 style={{ marginBottom: '0.5rem' }}>Server Not Connected</h3>
          <p style={{ maxWidth: '400px', margin: '0 auto' }}>
            Start the FastAPI server to see registered agents and interact with workflows.
          </p>
          <div style={{ 
            marginTop: '1.5rem', 
            background: 'var(--bg-secondary)', 
            padding: '1rem', 
            borderRadius: '8px',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: '0.875rem'
          }}>
            <code style={{ color: 'var(--accent-cyan)' }}>python server.py</code>
            <br />
            <span style={{ color: 'var(--text-muted)' }}>or</span>
            <br />
            <code style={{ color: 'var(--accent-cyan)' }}>uvicorn server:app --reload</code>
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v6m0 6v10"/>
              <path d="M4.22 4.22l4.24 4.24m7.07 7.07l4.24 4.24"/>
              <path d="M1 12h6m6 0h10"/>
              <path d="M4.22 19.78l4.24-4.24m7.07-7.07l4.24-4.24"/>
            </svg>
            Registered Agents
          </h2>
          <span style={{ 
            background: 'var(--accent-emerald)', 
            color: 'white', 
            padding: '0.25rem 0.75rem', 
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: '600'
          }}>
            {agents.length} Active
          </span>
        </div>

        <div className="agent-grid">
          {agents.map(agent => {
            const iconData = agentIcons[agent.agent_id] || { icon: '🤖', class: 'document' }
            return (
              <div 
                key={agent.agent_id} 
                className="agent-card"
                onClick={() => setSelectedAgent(selectedAgent === agent.agent_id ? null : agent.agent_id)}
              >
                <div className="agent-card-header">
                  <div className={`agent-icon ${iconData.class}`}>
                    {iconData.icon}
                  </div>
                  <div>
                    <div className="agent-name">{agent.name}</div>
                    <div className="agent-id">{agent.agent_id}</div>
                  </div>
                </div>
                <p className="agent-description">{agent.description}</p>
                <div className="capability-list">
                  {agent.capabilities?.slice(0, 3).map((cap, idx) => (
                    <span key={idx} className="capability-tag">{cap.name}</span>
                  ))}
                  {agent.capabilities?.length > 3 && (
                    <span className="capability-tag">+{agent.capabilities.length - 3} more</span>
                  )}
                </div>

                {selectedAgent === agent.agent_id && (
                  <div style={{ 
                    marginTop: '1rem', 
                    paddingTop: '1rem', 
                    borderTop: '1px solid var(--border-color)' 
                  }}>
                    <h4 style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                      All Capabilities:
                    </h4>
                    {agent.capabilities?.map((cap, idx) => (
                      <div key={idx} style={{ 
                        background: 'var(--bg-card)', 
                        padding: '0.75rem', 
                        borderRadius: '6px',
                        marginBottom: '0.5rem'
                      }}>
                        <div style={{ fontWeight: '500', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                          {cap.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {cap.description}
                        </div>
                        <div style={{ 
                          display: 'flex', 
                          gap: '1rem', 
                          marginTop: '0.5rem',
                          fontSize: '0.7rem',
                          color: 'var(--text-muted)'
                        }}>
                          <span>⏱️ ~{cap.estimated_duration_seconds}s</span>
                          {cap.requires_human_review && <span>👁️ Review Required</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            Available Workflows
          </h2>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <WorkflowCard 
            title="Email Processing"
            description="Triage emails, extract info, and generate responses"
            steps={['Email Triage', 'Deadline Extraction', 'Response Generation']}
            color="var(--accent-blue)"
          />
          <WorkflowCard 
            title="Document Classification"
            description="Classify documents and extract key deadlines"
            steps={['Document Classification', 'Metadata Extraction', 'Deadline Analysis']}
            color="var(--accent-emerald)"
          />
          <WorkflowCard 
            title="Client Intake"
            description="Process new client inquiries end-to-end"
            steps={['Conflict Check', 'Risk Assessment', 'Fee Estimation']}
            color="var(--accent-purple)"
          />
        </div>
      </div>
    </>
  )
}

function WorkflowCard({ title, description, steps, color }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border-color)',
      borderRadius: '12px',
      padding: '1.25rem',
      borderLeft: `3px solid ${color}`
    }}>
      <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '0.5rem' }}>{title}</h3>
      <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        {description}
      </p>
      <div>
        {steps.map((step, idx) => (
          <div key={idx} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            marginBottom: '0.375rem'
          }}>
            <span style={{
              width: '18px',
              height: '18px',
              background: color,
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.625rem',
              color: 'white',
              fontWeight: '600'
            }}>
              {idx + 1}
            </span>
            {step}
          </div>
        ))}
      </div>
    </div>
  )
}

export default Dashboard
