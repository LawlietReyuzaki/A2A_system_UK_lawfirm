function Architecture() {
  return (
    <>
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"/>
              <polyline points="2 17 12 22 22 17"/>
              <polyline points="2 12 12 17 22 12"/>
            </svg>
            System Architecture
          </h2>
        </div>

        <div className="architecture-diagram">
          <h3 style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            How main.py and server.py Connect
          </h3>
          
          <div className="diagram-flow">
            <div className="diagram-node api">
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🖥️</div>
              <div style={{ fontWeight: '600' }}>main.py</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CLI Demo</div>
            </div>
            
            <div className="diagram-arrow">→</div>
            
            <div className="diagram-node orchestrator">
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🎯</div>
              <div style={{ fontWeight: '600' }}>Orchestrator</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Coordinates Agents</div>
            </div>
            
            <div className="diagram-arrow">←</div>
            
            <div className="diagram-node api">
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🌐</div>
              <div style={{ fontWeight: '600' }}>server.py</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>REST API</div>
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
            Both <code style={{ color: 'var(--accent-cyan)' }}>main.py</code> and 
            <code style={{ color: 'var(--accent-cyan)' }}> server.py</code> are 
            <strong> separate entry points</strong> to the same multi-agent system.
            They share the same agents and core modules.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            Agent Communication Flow
          </h2>
        </div>

        <div style={{ padding: '1rem' }}>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            {[
              { num: 1, title: 'Request Received', desc: 'Frontend sends workflow request to server.py API' },
              { num: 2, title: 'Orchestrator Routes', desc: 'Orchestrator analyzes request and selects agents' },
              { num: 3, title: 'Agents Execute', desc: 'Sub-agents process their specific tasks in sequence' },
              { num: 4, title: 'Results Aggregated', desc: 'Orchestrator combines all agent outputs' },
              { num: 5, title: 'Response Sent', desc: 'Final result returned to frontend with all details' },
            ].map(step => (
              <div key={step.num} style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '10px',
                padding: '1.25rem',
                textAlign: 'center'
              }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  background: 'var(--accent-gradient)',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 0.75rem',
                  fontWeight: '700',
                  fontSize: '1rem'
                }}>
                  {step.num}
                </div>
                <h4 style={{ fontSize: '0.9375rem', marginBottom: '0.5rem' }}>{step.title}</h4>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            Entry Points Comparison
          </h2>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '0.875rem'
          }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-color)' }}>
                <th style={{ padding: '1rem', textAlign: 'left', color: 'var(--text-muted)' }}>Feature</th>
                <th style={{ padding: '1rem', textAlign: 'left', color: 'var(--accent-blue)' }}>main.py (CLI)</th>
                <th style={{ padding: '1rem', textAlign: 'left', color: 'var(--accent-emerald)' }}>server.py (API)</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['Purpose', 'Demo & Testing', 'Production REST API'],
                ['How to Run', 'python main.py', 'python server.py'],
                ['Interface', 'Command Line', 'HTTP Endpoints'],
                ['Use Case', 'Quick demos', 'Web apps, Integrations'],
                ['Output', 'Console logs', 'JSON responses'],
                ['Interactive', 'No (runs once)', 'Yes (continuous)'],
              ].map(([feature, cli, api], idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.875rem 1rem', fontWeight: '500' }}>{feature}</td>
                  <td style={{ padding: '0.875rem 1rem', color: 'var(--text-secondary)' }}>
                    <code style={{ 
                      background: 'var(--bg-secondary)', 
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '4px',
                      fontSize: '0.8125rem'
                    }}>{cli}</code>
                  </td>
                  <td style={{ padding: '0.875rem 1rem', color: 'var(--text-secondary)' }}>
                    <code style={{ 
                      background: 'var(--bg-secondary)', 
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '4px',
                      fontSize: '0.8125rem'
                    }}>{api}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            How to Invoke Sub-Agents
          </h2>
        </div>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--accent-cyan)' }}>
              1. Via Orchestrated Workflow (Recommended)
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Send a workflow request and let the Orchestrator automatically invoke the right agents:
            </p>
            <pre style={{
              background: 'var(--bg-secondary)',
              padding: '1rem',
              borderRadius: '8px',
              overflow: 'auto',
              fontSize: '0.8125rem',
              fontFamily: "'JetBrains Mono', monospace"
            }}>
              <code style={{ color: 'var(--accent-cyan)' }}>{`POST /api/workflow
{
  "workflow_type": "email_processing",
  "input_data": {
    "email_id": "email_001",
    "sender_email": "john@example.com",
    "subject": "Contract Review",
    "body": "Please review the attached..."
  }
}`}</code>
            </pre>
          </div>

          <div>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--accent-purple)' }}>
              2. Direct Agent Invocation
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Call a specific agent directly for fine-grained control:
            </p>
            <pre style={{
              background: 'var(--bg-secondary)',
              padding: '1rem',
              borderRadius: '8px',
              overflow: 'auto',
              fontSize: '0.8125rem',
              fontFamily: "'JetBrains Mono', monospace"
            }}>
              <code style={{ color: 'var(--accent-purple)' }}>{`POST /api/agent/email_triage_agent
{
  "agent_id": "email_triage_agent",
  "task_type": "email_full_triage",
  "input_data": {
    "email_id": "email_001",
    "body": "...",
    "subject": "..."
  }
}`}</code>
            </pre>
          </div>

          <div>
            <h3 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--accent-emerald)' }}>
              3. Available Agent IDs
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {[
                'email_triage_agent',
                'document_classification_agent', 
                'client_intake_agent',
                'deadline_tracker_agent',
                'response_generator_agent',
                'orchestrator_agent'
              ].map(id => (
                <code key={id} style={{
                  background: 'var(--bg-secondary)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontFamily: "'JetBrains Mono', monospace",
                  color: 'var(--accent-cyan)'
                }}>{id}</code>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default Architecture
