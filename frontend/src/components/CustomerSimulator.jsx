import { useState } from 'react'

// =============================================================================
// Prebuilt Scenarios
// =============================================================================

const EMAIL_SCENARIOS = [
  {
    id: 'urgent-contract',
    label: '📑 Urgent Contract Review',
    sender_name: 'John Smith',
    sender_email: 'john.smith@techcorp.co.uk',
    subject: 'Urgent: Employment Contract Review Needed',
    body: `Dear BrightLaw Team,

I am the HR Director at TechCorp Ltd and we urgently need assistance with reviewing our standard employment contracts. We are planning to hire 15 new developers next month and want to ensure our contracts are compliant with current UK employment law.

Specifically, we need help with:
1. Non-compete clauses - are ours enforceable?
2. IP assignment provisions
3. Remote working policies
4. Garden leave provisions

Could someone please get back to me by end of this week? We have a board meeting on Monday.

Best regards,
John Smith
HR Director, TechCorp Ltd`,
    attachments: ['employment_contract_v2.docx', 'company_policy.pdf']
  },
  {
    id: 'case-update',
    label: '📋 Case Status Update Request',
    sender_name: 'Sarah Jones',
    sender_email: 'sarah.jones@gmail.com',
    subject: 'Case Update Request - Matter Ref M2024-002',
    body: `Hi,

I'm writing to request an update on my unfair dismissal claim against my former employer.

My matter reference is M2024-002. I haven't heard anything since our last meeting two weeks ago and the tribunal hearing is scheduled for March 15th.

Could you please let me know:
- Have you received the employer's response yet?
- What documents do I need to prepare?
- When can we meet to prepare my witness statement?

I'm getting quite anxious about the upcoming hearing.

Thanks,
Sarah`,
    attachments: []
  },
  {
    id: 'complaint',
    label: '😠 Client Complaint',
    sender_name: 'Michael Brown',
    sender_email: 'michael.brown@email.com',
    subject: 'COMPLAINT - Slow Response Times',
    body: `To Whom It May Concern,

I am extremely disappointed with the service I have received regarding my property purchase at 42 Oak Lane, Bristol.

I have been waiting over 3 weeks for a response to my queries about the local authority search results. Every time I call, I'm told someone will get back to me 'soon' but nobody ever does.

My mortgage offer expires on February 1st and if we don't complete by then, I will lose my dream home.

I expect an immediate response and escalation to a senior partner. If I do not hear back within 24 hours, I will be filing a complaint with the Legal Ombudsman.

Michael Brown
Matter: Property Purchase - 42 Oak Lane`,
    attachments: ['mortgage_offer.pdf']
  },
  {
    id: 'new-inquiry',
    label: '🆕 New Legal Inquiry',
    sender_name: 'Emma Wilson',
    sender_email: 'emma.wilson@startup.io',
    subject: 'New Company Formation Inquiry',
    body: `Hello,

I'm looking to set up a new technology company and need legal advice on the following:

1. Best corporate structure (Ltd vs LLP)
2. Shareholder agreements for my 3 co-founders
3. Employee share option scheme
4. Standard NDAs and contractor agreements

We're hoping to raise seed funding in Q2, so we need to get this sorted quickly.

Could you let me know your availability for an initial consultation and your fee structure?

Thanks,
Emma Wilson`,
    attachments: ['business_plan_summary.pdf']
  }
]

const VOICE_SCENARIOS = [
  {
    id: 'urgent-callback',
    label: '📞 Urgent Callback Request',
    caller_name: 'David Chen',
    caller_phone: '+44 7700 900123',
    transcript: `Hello, this is David Chen calling about my commercial lease dispute. I just received a letter from the landlord's solicitors threatening to terminate our lease next week if we don't pay the disputed service charges. This is absolutely outrageous - we've been disputing these charges for months because they include items that aren't even in our lease agreement. I need someone to call me back urgently. My business is at stake here. The deadline they've given is Friday. Please, this is critical. My number is 07700 900123. Thank you.`,
    duration: 45
  },
  {
    id: 'consultation-request',
    label: '💼 Consultation Booking',
    caller_name: 'Lisa Thompson',
    caller_phone: '+44 7700 900456',
    transcript: `Hi there, my name is Lisa Thompson and I'm calling to book a consultation regarding my divorce proceedings. My husband and I have decided to separate after 15 years of marriage. We have two children aged 10 and 12, and we own a property jointly. I'd like to understand my options regarding custody arrangements and how the assets would be divided. I'm available most afternoons next week. Could someone please call me back to arrange a suitable time? My number is 07700 900456. Thank you.`,
    duration: 38
  },
  {
    id: 'existing-client',
    label: '📂 Existing Client Follow-up',
    caller_name: 'Robert Williams',
    caller_phone: '+44 7700 900789',
    transcript: `Good morning, Robert Williams here, client reference WIL-2024-001. I'm just calling to check on the status of my personal injury claim. The last I heard, you were waiting for the medical report. Has that come through yet? Also, I wanted to let you know that I've had another doctor's appointment and they've now said I'll need physiotherapy for at least another 6 months. I've got the documentation here if you need it. Please give me a call when you can. Thanks.`,
    duration: 32
  }
]

const CHAT_SCENARIOS = [
  {
    id: 'website-inquiry',
    label: '💬 Website Live Chat',
    customer_name: 'Anonymous Visitor',
    customer_email: 'visitor@temp.com',
    messages: `[14:32] Visitor: Hi, I found your website through Google. I need help with a landlord dispute.

[14:32] Bot: Hello! Welcome to BrightLaw. I'd be happy to help connect you with one of our property law specialists. Could you tell me a bit more about your situation?

[14:33] Visitor: My landlord is trying to evict me but I don't think they've followed the proper process. They just put a note under my door saying I have 2 weeks to leave.

[14:33] Bot: I understand this must be very stressful. A proper eviction in the UK requires specific legal procedures. Can you tell me - are you renting privately or through a housing association?

[14:34] Visitor: Private rental. I've been here 3 years with no problems until now.

[14:34] Bot: Thank you for that information. With 3 years of tenancy, you likely have significant protections. Would you like me to arrange for one of our housing specialists to call you?

[14:35] Visitor: Yes please. My name is actually James Morrison and my email is james.morrison@email.com

[14:35] Bot: Thank you James. I've noted your details. Someone will be in touch within 24 hours. Is there anything else I can help with today?

[14:36] James: No that's all. Thanks for your help.`
  },
  {
    id: 'document-question',
    label: '📄 Document Question',
    customer_name: 'Patricia Green',
    customer_email: 'p.green@company.com',
    messages: `[10:15] Patricia: Hello, I have a question about a contract I received.

[10:15] Support: Good morning Patricia! How can I help you today?

[10:16] Patricia: I received an employment contract from a new job offer but there's a non-compete clause that seems very broad. It says I can't work for any competitor within 100 miles for 2 years after leaving.

[10:17] Support: That does sound quite restrictive. Non-compete clauses in the UK need to be reasonable to be enforceable. Would you like our employment team to review the contract?

[10:18] Patricia: Yes please. How much would that cost?

[10:18] Support: A standard contract review is typically £350-500 + VAT depending on complexity. We can provide a fixed quote once we see the document.

[10:19] Patricia: OK, that sounds reasonable. How do I send it over?

[10:19] Support: You can email it to contracts@brightlaw.co.uk or upload it through our secure portal. Shall I send you the link?

[10:20] Patricia: Yes please, and can someone call me to discuss once they've reviewed it?

[10:20] Support: Absolutely. I'll make a note for a callback. What's the best number to reach you?

[10:21] Patricia: 07700 123456. Thanks!`
  }
]

const DOCUMENT_SCENARIOS = [
  {
    id: 'employment-contract',
    label: '📝 Employment Contract',
    filename: 'employment_contract_template.docx',
    file_type: 'docx',
    page_count: 12,
    content: `EMPLOYMENT CONTRACT

Between: TechCorp Limited (Company No. 12345678) ('the Employer')
And: [Employee Name] ('the Employee')

Date: [Date]

1. COMMENCEMENT AND JOB TITLE
1.1 Your employment will commence on [Start Date].
1.2 Your job title will be Senior Software Developer.
1.3 You will report to the CTO.

2. PROBATIONARY PERIOD
2.1 Your employment is subject to a probationary period of 6 months.
2.2 During this period, either party may terminate with 1 week's notice.

3. REMUNERATION
3.1 Your annual salary will be £75,000 payable monthly in arrears.
3.2 Salary reviews will take place annually in April.

4. WORKING HOURS
4.1 Normal working hours are 37.5 hours per week, Monday to Friday.
4.2 You may be required to work additional hours as reasonably necessary.

5. HOLIDAY ENTITLEMENT
5.1 You are entitled to 25 days paid holiday plus bank holidays.

6. NOTICE PERIODS
6.1 After probation, either party must give 3 months' notice.

7. CONFIDENTIALITY
7.1 You must not disclose any confidential information during or after employment.

8. INTELLECTUAL PROPERTY
8.1 All IP created during employment belongs to the Employer.

9. RESTRICTIVE COVENANTS
9.1 Non-compete: For 12 months after termination, you shall not work for a competitor within 50 miles.
9.2 Non-solicitation: For 12 months, you shall not solicit clients or employees.

10. GOVERNING LAW
This contract is governed by the laws of England and Wales.`
  },
  {
    id: 'lease-agreement',
    label: '🏢 Commercial Lease',
    filename: 'commercial_lease_agreement.pdf',
    file_type: 'pdf',
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

GOVERNING LAW: England and Wales`
  },
  {
    id: 'nda',
    label: '🔒 Non-Disclosure Agreement',
    filename: 'mutual_nda.pdf',
    file_type: 'pdf',
    page_count: 5,
    content: `MUTUAL NON-DISCLOSURE AGREEMENT

This Agreement is made on [Date]

BETWEEN:
(1) Company A Limited ("First Party")
(2) Company B Limited ("Second Party")

BACKGROUND:
The parties wish to explore a potential business relationship and in connection with this will need to share certain confidential information.

1. DEFINITIONS
"Confidential Information" means all information disclosed by one party to the other, whether in writing, orally or by any other means, that is designated as confidential or that reasonably should be understood to be confidential.

2. OBLIGATIONS
2.1 Each party agrees to keep confidential all Confidential Information received from the other party.
2.2 Neither party shall disclose Confidential Information to any third party without prior written consent.
2.3 Each party shall use Confidential Information only for the Purpose.

3. EXCEPTIONS
This Agreement does not apply to information that:
(a) is or becomes publicly available through no fault of the receiving party
(b) was rightfully in possession of the receiving party before disclosure
(c) is independently developed by the receiving party

4. TERM
This Agreement shall remain in effect for 3 years from the date of signature.

5. GOVERNING LAW
This Agreement is governed by the laws of England and Wales.`
  }
]

// =============================================================================
// Main Component
// =============================================================================

function CustomerSimulator({ serverStatus, onCaseSubmitted }) {
  const [activeTab, setActiveTab] = useState('email')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  // TTS state
  const [isSpeaking, setIsSpeaking] = useState(false)

  const tabs = [
    { id: 'email', label: 'Email', icon: '📧' },
    { id: 'voice', label: 'Voice Call', icon: '📞' },
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'document', label: 'Document', icon: '📄' },
  ]

  const handleSubmit = async (type, data) => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      let endpoint = '/api/workflow'
      let body = {}

      switch (type) {
        case 'email':
          body = {
            workflow_type: 'email_processing',
            case_type: 'email',
            input_data: {
              email_id: `email_${Date.now()}`,
              sender_email: data.sender_email,
              sender_name: data.sender_name,
              subject: data.subject,
              body: data.body,
              attachments: data.attachments || [],
              received_at: new Date().toISOString(),
              is_reply: false
            }
          }
          break
        case 'voice':
          body = {
            workflow_type: 'voice_call_processing',
            case_type: 'voice_call',
            input_data: {
              email_id: `call_${Date.now()}`,
              sender_email: data.caller_phone,
              sender_name: data.caller_name,
              subject: `Voice Call from ${data.caller_name}`,
              body: data.transcript,
              attachments: [],
              received_at: new Date().toISOString(),
              is_reply: false,
              call_duration_seconds: data.duration,
              source_type: 'voice_call'
            }
          }
          break
        case 'chat':
          body = {
            workflow_type: 'chat_processing',
            case_type: 'chat',
            input_data: {
              email_id: `chat_${Date.now()}`,
              sender_email: data.customer_email,
              sender_name: data.customer_name,
              subject: `Chat with ${data.customer_name}`,
              body: data.messages,
              attachments: [],
              received_at: new Date().toISOString(),
              is_reply: false,
              source_type: 'chat'
            }
          }
          break
        case 'document':
          body = {
            workflow_type: 'document_processing',
            case_type: 'document',
            input_data: {
              document_id: `doc_${Date.now()}`,
              filename: data.filename,
              content: data.content,
              file_type: data.file_type,
              page_count: data.page_count,
              source: 'customer_upload'
            }
          }
          break
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to process')
      }

      setSuccess(`Successfully submitted! Case ID: ${result.case_id || result.request_id}`)
      
      if (onCaseSubmitted) {
        onCaseSubmitted(result)
      }

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Text-to-Speech function
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      utterance.onerror = () => setIsSpeaking(false)
      window.speechSynthesis.speak(utterance)
    } else {
      alert('Text-to-speech is not supported in your browser')
    }
  }

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }

  return (
    <div className="customer-panel">
      <div className="customer-header">
        <h2>
          <span className="customer-icon">👤</span>
          Customer Portal
        </h2>
        <p>Simulate client communications - emails, calls, chats, and documents</p>
      </div>

      {/* Tabs */}
      <div className="customer-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`customer-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Status Messages */}
      {error && (
        <div className="alert alert-error">
          <span>❌</span>
          <div>{error}</div>
        </div>
      )}
      {success && (
        <div className="alert alert-success">
          <span>✅</span>
          <div>{success}</div>
        </div>
      )}

      {serverStatus.status !== 'online' && (
        <div className="alert alert-warning">
          <span>⚠️</span>
          <div>Server not connected. Start with <code>python server.py</code></div>
        </div>
      )}

      {/* Tab Content */}
      <div className="customer-content">
        {activeTab === 'email' && (
          <EmailForm 
            scenarios={EMAIL_SCENARIOS} 
            onSubmit={(data) => handleSubmit('email', data)}
            loading={loading}
            disabled={serverStatus.status !== 'online'}
          />
        )}
        {activeTab === 'voice' && (
          <VoiceForm 
            scenarios={VOICE_SCENARIOS} 
            onSubmit={(data) => handleSubmit('voice', data)}
            loading={loading}
            disabled={serverStatus.status !== 'online'}
            onSpeak={speakText}
            onStopSpeaking={stopSpeaking}
            isSpeaking={isSpeaking}
          />
        )}
        {activeTab === 'chat' && (
          <ChatForm 
            scenarios={CHAT_SCENARIOS} 
            onSubmit={(data) => handleSubmit('chat', data)}
            loading={loading}
            disabled={serverStatus.status !== 'online'}
          />
        )}
        {activeTab === 'document' && (
          <DocumentForm 
            scenarios={DOCUMENT_SCENARIOS} 
            onSubmit={(data) => handleSubmit('document', data)}
            loading={loading}
            disabled={serverStatus.status !== 'online'}
          />
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Form Components
// =============================================================================

function EmailForm({ scenarios, onSubmit, loading, disabled }) {
  const [selectedScenario, setSelectedScenario] = useState('')
  const [formData, setFormData] = useState({
    sender_name: '',
    sender_email: '',
    subject: '',
    body: '',
    attachments: []
  })

  const handleScenarioChange = (e) => {
    const scenario = scenarios.find(s => s.id === e.target.value)
    setSelectedScenario(e.target.value)
    if (scenario) {
      setFormData({
        sender_name: scenario.sender_name,
        sender_email: scenario.sender_email,
        subject: scenario.subject,
        body: scenario.body,
        attachments: scenario.attachments
      })
    }
  }

  return (
    <div className="customer-form">
      <div className="scenario-selector">
        <label>📋 Select a prebuilt scenario:</label>
        <select value={selectedScenario} onChange={handleScenarioChange}>
          <option value="">-- Choose a scenario --</option>
          {scenarios.map(s => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Sender Name</label>
          <input
            type="text"
            value={formData.sender_name}
            onChange={(e) => setFormData({...formData, sender_name: e.target.value})}
            placeholder="John Smith"
          />
        </div>
        <div className="form-group">
          <label>Sender Email</label>
          <input
            type="email"
            value={formData.sender_email}
            onChange={(e) => setFormData({...formData, sender_email: e.target.value})}
            placeholder="john@example.com"
          />
        </div>
      </div>

      <div className="form-group">
        <label>Subject</label>
        <input
          type="text"
          value={formData.subject}
          onChange={(e) => setFormData({...formData, subject: e.target.value})}
          placeholder="Email subject"
        />
      </div>

      <div className="form-group">
        <label>Email Body</label>
        <textarea
          value={formData.body}
          onChange={(e) => setFormData({...formData, body: e.target.value})}
          placeholder="Email content..."
          rows={10}
        />
      </div>

      {formData.attachments.length > 0 && (
        <div className="attachments-preview">
          <label>📎 Attachments:</label>
          <div className="attachment-chips">
            {formData.attachments.map((a, i) => (
              <span key={i} className="attachment-chip">{a}</span>
            ))}
          </div>
        </div>
      )}

      <button 
        className="btn btn-customer"
        onClick={() => onSubmit(formData)}
        disabled={loading || disabled || !formData.body}
      >
        {loading ? '⏳ Sending...' : '📤 Send Email'}
      </button>
    </div>
  )
}

function VoiceForm({ scenarios, onSubmit, loading, disabled, onSpeak, onStopSpeaking, isSpeaking }) {
  const [selectedScenario, setSelectedScenario] = useState('')
  const [formData, setFormData] = useState({
    caller_name: '',
    caller_phone: '',
    transcript: '',
    duration: 0
  })

  const handleScenarioChange = (e) => {
    const scenario = scenarios.find(s => s.id === e.target.value)
    setSelectedScenario(e.target.value)
    if (scenario) {
      setFormData({
        caller_name: scenario.caller_name,
        caller_phone: scenario.caller_phone,
        transcript: scenario.transcript,
        duration: scenario.duration
      })
    }
  }

  return (
    <div className="customer-form">
      <div className="scenario-selector">
        <label>📋 Select a prebuilt scenario:</label>
        <select value={selectedScenario} onChange={handleScenarioChange}>
          <option value="">-- Choose a scenario --</option>
          {scenarios.map(s => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Caller Name</label>
          <input
            type="text"
            value={formData.caller_name}
            onChange={(e) => setFormData({...formData, caller_name: e.target.value})}
            placeholder="John Smith"
          />
        </div>
        <div className="form-group">
          <label>Phone Number</label>
          <input
            type="tel"
            value={formData.caller_phone}
            onChange={(e) => setFormData({...formData, caller_phone: e.target.value})}
            placeholder="+44 7700 900123"
          />
        </div>
      </div>

      <div className="form-group">
        <label>Call Transcript</label>
        <textarea
          value={formData.transcript}
          onChange={(e) => setFormData({...formData, transcript: e.target.value})}
          placeholder="Transcribed voice message..."
          rows={8}
        />
      </div>

      {/* TTS Controls */}
      <div className="tts-controls">
        <span className="tts-label">🔊 Text-to-Speech Simulation:</span>
        {isSpeaking ? (
          <button className="btn btn-secondary btn-small" onClick={onStopSpeaking}>
            ⏹️ Stop
          </button>
        ) : (
          <button 
            className="btn btn-secondary btn-small" 
            onClick={() => onSpeak(formData.transcript)}
            disabled={!formData.transcript}
          >
            ▶️ Play Voice
          </button>
        )}
      </div>

      <div className="form-group">
        <label>Call Duration (seconds)</label>
        <input
          type="number"
          value={formData.duration}
          onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value) || 0})}
          min="0"
        />
      </div>

      <button 
        className="btn btn-customer"
        onClick={() => onSubmit(formData)}
        disabled={loading || disabled || !formData.transcript}
      >
        {loading ? '⏳ Processing...' : '📞 Submit Voice Call'}
      </button>
    </div>
  )
}

function ChatForm({ scenarios, onSubmit, loading, disabled }) {
  const [selectedScenario, setSelectedScenario] = useState('')
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    messages: ''
  })

  const handleScenarioChange = (e) => {
    const scenario = scenarios.find(s => s.id === e.target.value)
    setSelectedScenario(e.target.value)
    if (scenario) {
      setFormData({
        customer_name: scenario.customer_name,
        customer_email: scenario.customer_email,
        messages: scenario.messages
      })
    }
  }

  return (
    <div className="customer-form">
      <div className="scenario-selector">
        <label>📋 Select a prebuilt scenario:</label>
        <select value={selectedScenario} onChange={handleScenarioChange}>
          <option value="">-- Choose a scenario --</option>
          {scenarios.map(s => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Customer Name</label>
          <input
            type="text"
            value={formData.customer_name}
            onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
            placeholder="Customer name"
          />
        </div>
        <div className="form-group">
          <label>Customer Email</label>
          <input
            type="email"
            value={formData.customer_email}
            onChange={(e) => setFormData({...formData, customer_email: e.target.value})}
            placeholder="customer@email.com"
          />
        </div>
      </div>

      <div className="form-group">
        <label>Chat Transcript</label>
        <textarea
          value={formData.messages}
          onChange={(e) => setFormData({...formData, messages: e.target.value})}
          placeholder="Chat messages..."
          rows={12}
          className="chat-transcript"
        />
      </div>

      <button 
        className="btn btn-customer"
        onClick={() => onSubmit(formData)}
        disabled={loading || disabled || !formData.messages}
      >
        {loading ? '⏳ Processing...' : '💬 Submit Chat'}
      </button>
    </div>
  )
}

function DocumentForm({ scenarios, onSubmit, loading, disabled }) {
  const [selectedScenario, setSelectedScenario] = useState('')
  const [formData, setFormData] = useState({
    filename: '',
    file_type: 'pdf',
    page_count: 1,
    content: ''
  })

  const handleScenarioChange = (e) => {
    const scenario = scenarios.find(s => s.id === e.target.value)
    setSelectedScenario(e.target.value)
    if (scenario) {
      setFormData({
        filename: scenario.filename,
        file_type: scenario.file_type,
        page_count: scenario.page_count,
        content: scenario.content
      })
    }
  }

  return (
    <div className="customer-form">
      <div className="scenario-selector">
        <label>📋 Select a prebuilt scenario:</label>
        <select value={selectedScenario} onChange={handleScenarioChange}>
          <option value="">-- Choose a scenario --</option>
          {scenarios.map(s => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Filename</label>
          <input
            type="text"
            value={formData.filename}
            onChange={(e) => setFormData({...formData, filename: e.target.value})}
            placeholder="document.pdf"
          />
        </div>
        <div className="form-group">
          <label>File Type</label>
          <select
            value={formData.file_type}
            onChange={(e) => setFormData({...formData, file_type: e.target.value})}
          >
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
            <option value="doc">DOC</option>
            <option value="txt">TXT</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label>Page Count</label>
        <input
          type="number"
          value={formData.page_count}
          onChange={(e) => setFormData({...formData, page_count: parseInt(e.target.value) || 1})}
          min="1"
        />
      </div>

      <div className="form-group">
        <label>Document Content</label>
        <textarea
          value={formData.content}
          onChange={(e) => setFormData({...formData, content: e.target.value})}
          placeholder="Document text content..."
          rows={12}
        />
      </div>

      <button 
        className="btn btn-customer"
        onClick={() => onSubmit(formData)}
        disabled={loading || disabled || !formData.content}
      >
        {loading ? '⏳ Processing...' : '📄 Submit Document'}
      </button>
    </div>
  )
}

export default CustomerSimulator
