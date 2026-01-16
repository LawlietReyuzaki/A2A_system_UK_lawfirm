import { useState, useEffect } from 'react'
import CustomerSimulator from './components/CustomerSimulator'
import AdminConsole from './components/AdminConsole'
import './index.css'

function App() {
  const [mode, setMode] = useState('customer') // 'customer' or 'admin'
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [serverStatus, setServerStatus] = useState({ status: 'checking', agents: 0 })
  const [agents, setAgents] = useState([])

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  // Check server health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/health')
        const data = await response.json()
        setServerStatus({
          status: data.status === 'healthy' ? 'online' : 'initializing',
          agents: data.agents_registered,
          cases: data.cases_stored || 0
        })
      } catch (error) {
        setServerStatus({ status: 'offline', agents: 0, cases: 0 })
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  // Fetch agents
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch('/api/agents')
        const data = await response.json()
        setAgents(data.agents || [])
      } catch (error) {
        console.error('Failed to fetch agents:', error)
      }
    }

    if (serverStatus.status === 'online') {
      fetchAgents()
    }
  }, [serverStatus.status])

  const handleCaseSubmitted = (result) => {
    // Switch to admin mode to show the processed case
    setMode('admin')
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">⚡</div>
            <h1>BrightLaw A2A</h1>
          </div>

          {/* Mode Switch */}
          <div className="mode-switch">
            <button 
              className={`mode-btn ${mode === 'customer' ? 'active customer' : ''}`}
              onClick={() => setMode('customer')}
            >
              👤 Customer
            </button>
            <button 
              className={`mode-btn ${mode === 'admin' ? 'active admin' : ''}`}
              onClick={() => setMode('admin')}
            >
              ⚙️ Admin
            </button>
          </div>

          <div className="header-right">
            {/* Theme Toggle */}
            <button 
              className="theme-toggle"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>

            {/* Status Badge */}
            <div className="status-badge">
              <span className={`status-dot ${serverStatus.status === 'online' ? '' : 'offline'}`}></span>
              <span>
                {serverStatus.status === 'online' 
                  ? `${serverStatus.agents} Agents • ${serverStatus.cases || 0} Cases` 
                  : serverStatus.status === 'checking'
                    ? 'Connecting...'
                    : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-container">
        {mode === 'customer' ? (
          <CustomerSimulator 
            serverStatus={serverStatus} 
            onCaseSubmitted={handleCaseSubmitted}
          />
        ) : (
          <AdminConsole 
            agents={agents} 
            serverStatus={serverStatus}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <span>BrightLaw Multi-Agent System</span>
          <span>•</span>
          <span>A2A Architecture Demo</span>
          <span>•</span>
          <span className={mode === 'customer' ? 'mode-indicator customer' : 'mode-indicator admin'}>
            {mode === 'customer' ? '👤 Customer View' : '⚙️ Admin View'}
          </span>
        </div>
      </footer>
    </div>
  )
}

export default App
