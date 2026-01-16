"""
Client Intake Agent

Responsible for:
- Processing new client inquiries
- Performing conflict checks
- Gathering required client information
- Risk assessment for new matters
- Fee estimation and engagement letter generation

Task Flow:
1. Receive new client inquiry (from email triage or portal)
2. Extract client and matter details
3. Perform conflict check against existing clients/matters
4. Assess matter complexity and risk
5. Generate fee estimate based on matter type
6. Prepare client intake checklist
7. Draft engagement letter or decline letter
8. Route to appropriate lawyer for review
"""

import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

import sys
sys.path.insert(0, '/home/claude/brightlaw-a2a')

from core.a2a_protocol import (
    BaseAgent, AgentCard, AgentCapability, TaskRequest, TaskResponse,
    TaskState, TaskArtifact, Priority
)
from core.llm_client import GeminiClient, AgentLLM


# =============================================================================
# Client Intake Data Models
# =============================================================================

class ConflictStatus(str, Enum):
    CLEAR = "clear"
    POTENTIAL = "potential"
    CONFIRMED = "confirmed"
    WAIVABLE = "waivable"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ClientType(str, Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    PARTNERSHIP = "partnership"
    CHARITY = "charity"
    TRUST = "trust"
    PUBLIC_BODY = "public_body"


class InquiryInput(BaseModel):
    """Input schema for client intake"""
    inquiry_id: str
    source: str  # email, phone, portal, referral
    
    # Client information
    client_name: str
    client_type: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    company_name: Optional[str] = None
    company_number: Optional[str] = None
    
    # Matter information
    matter_description: str
    practice_area: Optional[str] = None
    urgency: Optional[str] = None
    opposing_parties: List[str] = Field(default_factory=list)
    
    # Additional context
    referral_source: Optional[str] = None
    budget_indication: Optional[str] = None
    preferred_lawyer: Optional[str] = None
    raw_inquiry_text: Optional[str] = None


class ConflictCheckResult(BaseModel):
    """Result of conflict check"""
    status: str
    conflicts_found: List[Dict[str, Any]] = Field(default_factory=list)
    related_matters: List[Dict[str, Any]] = Field(default_factory=list)
    recommendation: str
    can_proceed: bool
    requires_waiver: bool = False
    waiver_parties: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Risk assessment for new matter"""
    overall_risk: str
    risk_factors: List[str] = Field(default_factory=list)
    mitigating_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    requires_senior_review: bool = False
    aml_check_required: bool = True
    enhanced_due_diligence: bool = False


class FeeEstimate(BaseModel):
    """Fee estimate for matter"""
    estimate_type: str  # fixed, hourly, capped, contingency
    low_estimate_gbp: float
    high_estimate_gbp: float
    hourly_rate_gbp: Optional[float] = None
    estimated_hours: Optional[float] = None
    disbursements_estimate_gbp: float = 0
    vat_applicable: bool = True
    assumptions: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)


class IntakeChecklist(BaseModel):
    """Required documents and information checklist"""
    required_documents: List[str]
    required_information: List[str]
    aml_requirements: List[str]
    optional_documents: List[str] = Field(default_factory=list)


class IntakeResult(BaseModel):
    """Complete intake result"""
    inquiry_id: str
    client_type: str
    practice_area: str
    matter_type: str
    
    conflict_check: ConflictCheckResult
    risk_assessment: RiskAssessment
    fee_estimate: FeeEstimate
    checklist: IntakeChecklist
    
    recommended_lawyer: Optional[str] = None
    recommended_team: Optional[str] = None
    
    can_proceed: bool
    decline_reason: Optional[str] = None
    
    draft_engagement_letter: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)


# =============================================================================
# Client Intake Agent
# =============================================================================

SYSTEM_PROMPT = """You are the Client Intake Agent for BrightLaw, a UK legal services firm.

Your responsibilities:
1. PROCESS new client inquiries and extract key information
2. PERFORM conflict checks against existing clients and matters
3. ASSESS risk level and complexity of new matters
4. ESTIMATE fees based on matter type and complexity
5. PREPARE intake checklists and engagement documentation

PRACTICE AREAS & MATTER TYPES:

CORPORATE:
- Company formation and structuring
- Mergers and acquisitions (M&A)
- Shareholder agreements and disputes
- Commercial contracts
- Corporate governance

EMPLOYMENT:
- Employment contracts and policies
- Tribunal claims (unfair dismissal, discrimination)
- Settlement agreements (COT3, settlement)
- TUPE transfers
- Disciplinary and grievance

PROPERTY:
- Residential conveyancing (sale, purchase)
- Commercial property (lease, sale, purchase)
- Property disputes
- Landlord and tenant

LITIGATION:
- Commercial disputes
- Debt recovery
- Professional negligence
- Injunctions

CONFLICT CHECK GUIDELINES:
- Check client names against existing client database
- Check opposing parties against current and former clients
- Consider related parties (directors, shareholders, family)
- Check for matter-type conflicts (acting for both sides)

RISK ASSESSMENT FACTORS:
- Client type and reputation
- Matter complexity
- Potential exposure/liability
- Time pressure and deadlines
- Opposing party (known difficult, SRA concerns)
- Fee recovery risk
- Reputational risk

FEE ESTIMATION:
- Consider matter complexity
- Typical hours for matter type
- Seniority mix required
- Disbursements (counsel, searches, court fees)
- Apply UK VAT (20%) where applicable

AML/KYC REQUIREMENTS:
- All new clients require ID verification
- Companies require Companies House checks
- Source of funds for transactions over £10,000
- Enhanced due diligence for high-risk clients

Always recommend declining matters with confirmed conflicts or excessive risk.
Be conservative with estimates and transparent about assumptions.
"""


class ClientIntakeAgent(BaseAgent):
    """
    Agent responsible for processing new client inquiries.
    
    Capabilities:
    - Client information extraction
    - Conflict checking
    - Risk assessment
    - Fee estimation
    - Intake documentation
    """
    
    def __init__(self, llm_client: GeminiClient):
        super().__init__(
            agent_id="client_intake_agent",
            name="Client Intake Agent",
            llm_client=llm_client
        )
        self.agent_llm = AgentLLM(
            client=llm_client,
            agent_name=self.name,
            system_prompt=SYSTEM_PROMPT
        )
        
        # Simulated existing client database for conflict checks
        self.existing_clients = [
            {"name": "TechCorp Ltd", "type": "company", "matters": ["M2023-001", "M2024-015"]},
            {"name": "Smith Holdings", "type": "company", "matters": ["M2023-045"]},
            {"name": "John Wilson", "type": "individual", "matters": ["M2024-002"]},
            {"name": "ABC Properties Ltd", "type": "company", "matters": ["M2023-078", "M2024-033"]},
        ]
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description="Processes new client inquiries including conflict checks, risk assessment, and fee estimation",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="conflict_check",
                    description="Check for conflicts with existing clients and matters",
                    input_schema=InquiryInput.model_json_schema(),
                    output_schema=ConflictCheckResult.model_json_schema(),
                    estimated_duration_seconds=5,
                    requires_human_review=True
                ),
                AgentCapability(
                    name="risk_assessment",
                    description="Assess risk level of new matter",
                    input_schema=InquiryInput.model_json_schema(),
                    output_schema=RiskAssessment.model_json_schema(),
                    estimated_duration_seconds=10,
                    requires_human_review=True
                ),
                AgentCapability(
                    name="fee_estimation",
                    description="Generate fee estimate for matter",
                    input_schema=InquiryInput.model_json_schema(),
                    output_schema=FeeEstimate.model_json_schema(),
                    estimated_duration_seconds=10,
                    requires_human_review=True
                ),
                AgentCapability(
                    name="full_intake",
                    description="Complete new client intake process",
                    input_schema=InquiryInput.model_json_schema(),
                    output_schema=IntakeResult.model_json_schema(),
                    estimated_duration_seconds=30,
                    requires_human_review=True
                )
            ],
            supported_input_types=["inquiry", "client_data"],
            supported_output_types=["conflict_check", "risk_assessment", "fee_estimate", "intake_result"]
        )
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process a client intake task"""
        start_time = time.time()
        
        try:
            inquiry = InquiryInput(**task.input_data)
            
            if task.task_type == "conflict_check":
                result = await self._perform_conflict_check(inquiry)
                artifact = TaskArtifact(
                    artifact_type="conflict_check",
                    content=result.model_dump()
                )
                
            elif task.task_type == "risk_assessment":
                result = await self._assess_risk(inquiry)
                artifact = TaskArtifact(
                    artifact_type="risk_assessment",
                    content=result.model_dump()
                )
                
            elif task.task_type == "fee_estimation":
                result = await self._estimate_fees(inquiry)
                artifact = TaskArtifact(
                    artifact_type="fee_estimate",
                    content=result.model_dump()
                )
                
            elif task.task_type == "full_intake":
                result = await self._full_intake(inquiry)
                artifact = TaskArtifact(
                    artifact_type="intake_result",
                    content=result.model_dump()
                )
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.COMPLETED,
                result=result.model_dump() if hasattr(result, 'model_dump') else result,
                artifacts=[artifact],
                confidence_score=0.85,
                requires_human_review=True,  # Intake always requires human review
                escalation_reason="New client intake requires lawyer approval",
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _perform_conflict_check(self, inquiry: InquiryInput) -> ConflictCheckResult:
        """Perform conflict check"""
        # Check against simulated database
        potential_conflicts = []
        related_matters = []
        
        for client in self.existing_clients:
            # Simple name matching (in production would use fuzzy matching)
            if inquiry.client_name.lower() in client["name"].lower() or \
               client["name"].lower() in inquiry.client_name.lower():
                related_matters.append({
                    "client": client["name"],
                    "matters": client["matters"],
                    "relationship": "same_client"
                })
            
            # Check opposing parties
            for opposing in inquiry.opposing_parties:
                if opposing.lower() in client["name"].lower() or \
                   client["name"].lower() in opposing.lower():
                    potential_conflicts.append({
                        "existing_client": client["name"],
                        "opposing_party": opposing,
                        "matters": client["matters"],
                        "conflict_type": "opposing_party_is_client"
                    })
        
        # Use LLM for additional analysis
        prompt = f"""Analyze potential conflicts for this new client inquiry:

New Client: {inquiry.client_name}
Company: {inquiry.company_name or 'N/A'}
Matter: {inquiry.matter_description}
Opposing Parties: {', '.join(inquiry.opposing_parties) if inquiry.opposing_parties else 'None specified'}

Existing Clients in Database:
{[c['name'] for c in self.existing_clients]}

Potential Conflicts Found: {potential_conflicts}
Related Matters: {related_matters}

Provide analysis in JSON:
{{
    "status": "clear|potential|confirmed|waivable",
    "recommendation": "<detailed recommendation>",
    "can_proceed": <true/false>,
    "requires_waiver": <true/false>,
    "waiver_parties": ["<parties needing waiver>"],
    "additional_checks_needed": ["<any additional checks>"]
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )
        
        result = response.structured_output
        
        return ConflictCheckResult(
            status=result.get("status", "potential"),
            conflicts_found=potential_conflicts,
            related_matters=related_matters,
            recommendation=result.get("recommendation", ""),
            can_proceed=result.get("can_proceed", False),
            requires_waiver=result.get("requires_waiver", False),
            waiver_parties=result.get("waiver_parties", [])
        )
    
    async def _assess_risk(self, inquiry: InquiryInput) -> RiskAssessment:
        """Assess risk of new matter"""
        prompt = f"""Assess the risk level for this new matter:

Client: {inquiry.client_name}
Client Type: {inquiry.client_type or 'Unknown'}
Company: {inquiry.company_name or 'N/A'}

Matter Description:
{inquiry.matter_description}

Practice Area: {inquiry.practice_area or 'To be determined'}
Urgency: {inquiry.urgency or 'Normal'}
Opposing Parties: {', '.join(inquiry.opposing_parties) if inquiry.opposing_parties else 'None'}
Budget Indication: {inquiry.budget_indication or 'Not provided'}
Referral Source: {inquiry.referral_source or 'Direct inquiry'}

Assess risks including:
- Client risk (creditworthiness, reputation, difficult client indicators)
- Matter complexity risk
- Financial exposure risk
- Time pressure risk
- Reputational risk
- Regulatory/compliance risk

Respond with JSON:
{{
    "overall_risk": "low|medium|high|very_high",
    "risk_factors": ["<identified risks>"],
    "mitigating_factors": ["<positive factors>"],
    "recommendations": ["<risk mitigation steps>"],
    "requires_senior_review": <true/false>,
    "aml_check_required": <true/false>,
    "enhanced_due_diligence": <true/false>
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2
        )
        
        return RiskAssessment(**response.structured_output)
    
    async def _estimate_fees(self, inquiry: InquiryInput) -> FeeEstimate:
        """Generate fee estimate"""
        prompt = f"""Generate a fee estimate for this matter:

Client: {inquiry.client_name}
Client Type: {inquiry.client_type or 'Unknown'}

Matter Description:
{inquiry.matter_description}

Practice Area: {inquiry.practice_area or 'To be determined'}
Budget Indication: {inquiry.budget_indication or 'Not provided'}

Consider:
- Typical matter complexity for this type
- Estimated hours at different fee earner levels
- Standard hourly rates (Partner: £350-450, Associate: £200-300, Trainee: £150)
- Likely disbursements (counsel fees, court fees, searches, etc.)
- Fixed fee vs hourly appropriate for this matter type

Provide estimate in GBP:
{{
    "estimate_type": "fixed|hourly|capped|contingency",
    "low_estimate_gbp": <number>,
    "high_estimate_gbp": <number>,
    "hourly_rate_gbp": <blended rate or null>,
    "estimated_hours": <number or null>,
    "disbursements_estimate_gbp": <number>,
    "vat_applicable": <true/false>,
    "assumptions": ["<key assumptions>"],
    "caveats": ["<important caveats>"]
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.3
        )
        
        return FeeEstimate(**response.structured_output)
    
    async def _generate_checklist(self, inquiry: InquiryInput, practice_area: str) -> IntakeChecklist:
        """Generate intake checklist"""
        prompt = f"""Generate an intake checklist for this matter:

Client: {inquiry.client_name}
Client Type: {inquiry.client_type or 'Unknown'}
Company: {inquiry.company_name or 'N/A'}
Practice Area: {practice_area}

Matter Description:
{inquiry.matter_description}

List required:
1. Documents the client must provide
2. Information we need to gather
3. AML/KYC requirements for this client type
4. Optional but helpful documents

Respond with JSON:
{{
    "required_documents": ["<essential documents>"],
    "required_information": ["<information needed>"],
    "aml_requirements": ["<AML/KYC checks needed>"],
    "optional_documents": ["<helpful but not essential>"]
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2
        )
        
        return IntakeChecklist(**response.structured_output)
    
    async def _full_intake(self, inquiry: InquiryInput) -> IntakeResult:
        """Perform complete intake process"""
        # Determine practice area
        practice_area = inquiry.practice_area or await self._determine_practice_area(inquiry)
        
        # Perform all checks
        conflict_check = await self._perform_conflict_check(inquiry)
        risk_assessment = await self._assess_risk(inquiry)
        fee_estimate = await self._estimate_fees(inquiry)
        checklist = await self._generate_checklist(inquiry, practice_area)
        
        # Determine if we can proceed
        can_proceed = conflict_check.can_proceed and risk_assessment.overall_risk != "very_high"
        decline_reason = None
        
        if not conflict_check.can_proceed:
            decline_reason = f"Conflict check failed: {conflict_check.recommendation}"
        elif risk_assessment.overall_risk == "very_high":
            decline_reason = f"Risk level too high: {', '.join(risk_assessment.risk_factors[:3])}"
        
        # Generate engagement letter if proceeding
        engagement_letter = None
        if can_proceed:
            engagement_letter = await self._draft_engagement_letter(
                inquiry, practice_area, fee_estimate
            )
        
        # Determine next steps
        next_steps = self._determine_next_steps(
            can_proceed, conflict_check, risk_assessment
        )
        
        return IntakeResult(
            inquiry_id=inquiry.inquiry_id,
            client_type=inquiry.client_type or "individual",
            practice_area=practice_area,
            matter_type=self._determine_matter_type(inquiry.matter_description, practice_area),
            conflict_check=conflict_check,
            risk_assessment=risk_assessment,
            fee_estimate=fee_estimate,
            checklist=checklist,
            can_proceed=can_proceed,
            decline_reason=decline_reason,
            draft_engagement_letter=engagement_letter,
            next_steps=next_steps
        )
    
    async def _determine_practice_area(self, inquiry: InquiryInput) -> str:
        """Determine practice area from inquiry"""
        result = await self.agent_llm.classify(
            text=inquiry.matter_description,
            categories=["corporate", "employment", "property", "litigation", "private_client"],
            context=f"Client: {inquiry.client_name}, Company: {inquiry.company_name}"
        )
        return result.get("category", "general")
    
    def _determine_matter_type(self, description: str, practice_area: str) -> str:
        """Determine specific matter type"""
        matter_types = {
            "corporate": "company_matter",
            "employment": "employment_matter",
            "property": "property_transaction",
            "litigation": "dispute_matter",
            "private_client": "private_client_matter"
        }
        return matter_types.get(practice_area, "general_matter")
    
    async def _draft_engagement_letter(
        self,
        inquiry: InquiryInput,
        practice_area: str,
        fee_estimate: FeeEstimate
    ) -> str:
        """Draft engagement letter"""
        prompt = f"""Draft a brief engagement letter for:

Client: {inquiry.client_name}
Matter: {inquiry.matter_description}
Practice Area: {practice_area}
Fee Estimate: £{fee_estimate.low_estimate_gbp:,.0f} - £{fee_estimate.high_estimate_gbp:,.0f} + VAT
Fee Basis: {fee_estimate.estimate_type}

Include:
- Scope of work (brief)
- Fee arrangement
- Terms of engagement reference
- SRA regulatory information
- Money laundering requirements

Keep it concise - this is a draft for lawyer review."""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.5
        )
        
        return response.content
    
    def _determine_next_steps(
        self,
        can_proceed: bool,
        conflict_check: ConflictCheckResult,
        risk_assessment: RiskAssessment
    ) -> List[str]:
        """Determine next steps based on intake results"""
        steps = []
        
        if not can_proceed:
            steps.append("Send decline letter")
            steps.append("Record reason in CRM")
            return steps
        
        steps.append("Review intake pack")
        steps.append("Complete AML checks")
        
        if conflict_check.requires_waiver:
            steps.append(f"Obtain conflict waivers from: {', '.join(conflict_check.waiver_parties)}")
        
        if risk_assessment.requires_senior_review:
            steps.append("Escalate to senior partner for approval")
        
        if risk_assessment.enhanced_due_diligence:
            steps.append("Complete enhanced due diligence")
        
        steps.append("Send engagement letter for signature")
        steps.append("Request money on account")
        steps.append("Open matter file")
        
        return steps
