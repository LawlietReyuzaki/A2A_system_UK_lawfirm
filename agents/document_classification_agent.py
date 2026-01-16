"""
Document Classification Agent

Responsible for:
- Classifying legal documents by type
- Extracting key metadata from documents
- Identifying document relationships
- Flagging documents requiring special handling

Task Flow:
1. Receive document content (text extracted from PDF/DOCX)
2. Classify document type (contract, correspondence, court document, etc.)
3. Identify practice area and sub-type
4. Extract key metadata (parties, dates, references)
5. Determine document sensitivity and handling requirements
6. Route to appropriate extraction agent or storage
"""

import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, '/home/claude/brightlaw-a2a')

from core.a2a_protocol import (
    BaseAgent, AgentCard, AgentCapability, TaskRequest, TaskResponse,
    TaskState, TaskArtifact, Priority
)
from core.llm_client import GeminiClient, AgentLLM


# =============================================================================
# Document Classification Data Models
# =============================================================================

class DocumentInput(BaseModel):
    """Input schema for document classification"""
    document_id: str
    filename: str
    content: str  # Extracted text content
    file_type: str  # pdf, docx, etc.
    file_size_bytes: int = 0
    page_count: int = 1
    source: str = "upload"  # upload, email_attachment, scan
    matter_id: Optional[str] = None


class DocumentClassification(BaseModel):
    """Classification result for a document"""
    document_type: str  # contract, letter, court_filing, deed, etc.
    document_subtype: Optional[str] = None  # employment_contract, lease_agreement, etc.
    practice_area: str
    confidence: float
    language: str = "en"
    is_template: bool = False
    is_executed: bool = False  # Has signatures
    is_draft: bool = False
    reasoning: str


class DocumentMetadata(BaseModel):
    """Extracted metadata from document"""
    title: Optional[str] = None
    date: Optional[str] = None  # Document date
    parties: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)  # Case numbers, contract refs
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    jurisdiction: Optional[str] = None
    governing_law: Optional[str] = None
    key_terms: List[str] = Field(default_factory=list)


class DocumentFlags(BaseModel):
    """Special handling flags"""
    contains_pii: bool = False
    contains_financial_data: bool = False
    privileged: bool = False
    confidential_marking: bool = False
    requires_witness: bool = False
    time_sensitive: bool = False
    flagged_clauses: List[str] = Field(default_factory=list)


class DocumentClassificationResult(BaseModel):
    """Complete document classification result"""
    classification: DocumentClassification
    metadata: DocumentMetadata
    flags: DocumentFlags
    suggested_storage_path: str
    related_document_types: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)


# =============================================================================
# Document Classification Agent
# =============================================================================

SYSTEM_PROMPT = """You are the Document Classification Agent for BrightLaw, a UK legal services firm.

Your responsibilities:
1. CLASSIFY legal documents by type and sub-type
2. EXTRACT key metadata like parties, dates, and references
3. IDENTIFY special handling requirements
4. RECOMMEND storage and next actions

Document Type Categories:

CONTRACTS:
- employment_contract: Staff contracts, service agreements
- commercial_contract: Supply, distribution, licensing agreements
- lease_agreement: Property leases, tenancy agreements
- loan_agreement: Facility agreements, promissory notes
- shareholders_agreement: SHA, investment agreements
- nda: Non-disclosure, confidentiality agreements
- terms_of_service: T&Cs, user agreements

CORRESPONDENCE:
- letter_advice: Legal advice letters
- letter_client: General client correspondence
- letter_third_party: Letters to opposing counsel, third parties
- instruction_letter: Client instructions

COURT_DOCUMENTS:
- claim_form: N1, particulars of claim
- defence: Defence and counterclaim
- witness_statement: Witness statements
- court_order: Orders, judgments
- skeleton_argument: Legal submissions

CORPORATE_DOCUMENTS:
- articles_of_association: Company articles
- board_minutes: Board resolutions, minutes
- shareholders_resolution: Written resolutions
- certificate_incorporation: Formation documents
- annual_return: Confirmation statements

PROPERTY_DOCUMENTS:
- title_deed: Property titles
- transfer_deed: TR1, transfer documents
- lease: Commercial/residential leases
- search_results: Local authority, environmental searches
- mortgage_deed: Charge documents

PRACTICE AREAS:
- corporate: Company, M&A, commercial
- employment: HR, tribunal, contracts
- property: Conveyancing, landlord-tenant
- litigation: Disputes, court matters
- private_client: Wills, probate, family

HANDLING FLAGS:
- PII: Names, addresses, financial details of individuals
- Privileged: Solicitor-client privileged communications
- Confidential: Marked confidential or commercially sensitive
- Time-sensitive: Contains deadlines or limitation dates

Always consider UK legal context and SRA regulations.
Be conservative with confidence scores.
"""


class DocumentClassificationAgent(BaseAgent):
    """
    Agent responsible for classifying legal documents.
    
    Capabilities:
    - Document type classification
    - Metadata extraction
    - Sensitivity flagging
    - Storage recommendations
    """
    
    def __init__(self, llm_client: GeminiClient):
        super().__init__(
            agent_id="document_classification_agent",
            name="Document Classification Agent",
            llm_client=llm_client
        )
        self.agent_llm = AgentLLM(
            client=llm_client,
            agent_name=self.name,
            system_prompt=SYSTEM_PROMPT
        )
    
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.name,
            description="Classifies legal documents by type, extracts metadata, and identifies handling requirements",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="document_classification",
                    description="Classify document by type and practice area",
                    input_schema=DocumentInput.model_json_schema(),
                    output_schema=DocumentClassification.model_json_schema(),
                    estimated_duration_seconds=5,
                    requires_human_review=False
                ),
                AgentCapability(
                    name="document_metadata_extraction",
                    description="Extract key metadata from document",
                    input_schema=DocumentInput.model_json_schema(),
                    output_schema=DocumentMetadata.model_json_schema(),
                    estimated_duration_seconds=10,
                    requires_human_review=False
                ),
                AgentCapability(
                    name="document_full_classification",
                    description="Complete document classification with metadata and flags",
                    input_schema=DocumentInput.model_json_schema(),
                    output_schema=DocumentClassificationResult.model_json_schema(),
                    estimated_duration_seconds=20,
                    requires_human_review=True
                )
            ],
            supported_input_types=["document_text", "document"],
            supported_output_types=["classification", "metadata", "flags"]
        )
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process a document classification task"""
        start_time = time.time()
        
        try:
            doc_data = DocumentInput(**task.input_data)
            
            if task.task_type == "document_classification":
                result = await self._classify_document(doc_data)
                artifact = TaskArtifact(
                    artifact_type="classification",
                    content=result.model_dump()
                )
                confidence = result.confidence
                
            elif task.task_type == "document_metadata_extraction":
                result = await self._extract_metadata(doc_data)
                artifact = TaskArtifact(
                    artifact_type="metadata",
                    content=result.model_dump()
                )
                confidence = 0.8
                
            elif task.task_type == "document_full_classification":
                result = await self._full_classification(doc_data)
                artifact = TaskArtifact(
                    artifact_type="full_classification",
                    content=result.model_dump()
                )
                confidence = result.classification.confidence
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.COMPLETED,
                result=result.model_dump() if hasattr(result, 'model_dump') else result,
                artifacts=[artifact],
                confidence_score=confidence,
                requires_human_review=confidence < 0.7,
                escalation_reason="Low confidence classification" if confidence < 0.7 else None,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                state=TaskState.FAILED,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _classify_document(self, doc: DocumentInput) -> DocumentClassification:
        """Classify a document"""
        # Truncate content for classification (first 3000 chars usually enough)
        content_sample = doc.content[:3000] if len(doc.content) > 3000 else doc.content
        
        prompt = f"""Classify this legal document:

Filename: {doc.filename}
File Type: {doc.file_type}
Pages: {doc.page_count}
Source: {doc.source}

Content (sample):
{content_sample}

Respond with JSON:
{{
    "document_type": "<main type>",
    "document_subtype": "<specific subtype or null>",
    "practice_area": "<practice area>",
    "confidence": <0.0-1.0>,
    "language": "<language code>",
    "is_template": <true/false>,
    "is_executed": <true/false - has signatures>,
    "is_draft": <true/false>,
    "reasoning": "<brief explanation>"
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2
        )
        
        return DocumentClassification(**response.structured_output)
    
    async def _extract_metadata(self, doc: DocumentInput) -> DocumentMetadata:
        """Extract metadata from document"""
        prompt = f"""Extract key metadata from this legal document:

Filename: {doc.filename}

Content:
{doc.content[:5000]}

Extract and respond with JSON:
{{
    "title": "<document title or null>",
    "date": "<document date in YYYY-MM-DD or null>",
    "parties": ["<party names>"],
    "references": ["<case/contract/file references>"],
    "effective_date": "<effective date or null>",
    "expiry_date": "<expiry/termination date or null>",
    "jurisdiction": "<jurisdiction or null>",
    "governing_law": "<governing law or null>",
    "key_terms": ["<important terms, clauses, conditions>"]
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )
        
        return DocumentMetadata(**response.structured_output)
    
    async def _extract_flags(self, doc: DocumentInput) -> DocumentFlags:
        """Extract sensitivity flags from document"""
        prompt = f"""Analyze this document for sensitivity and special handling requirements:

Content:
{doc.content[:5000]}

Check for:
1. PII (personal identifiable information)
2. Financial data
3. Legal privilege indicators
4. Confidentiality markings
5. Witness/signature requirements
6. Time-sensitive deadlines
7. Unusual or concerning clauses

Respond with JSON:
{{
    "contains_pii": <true/false>,
    "contains_financial_data": <true/false>,
    "privileged": <true/false>,
    "confidential_marking": <true/false>,
    "requires_witness": <true/false>,
    "time_sensitive": <true/false>,
    "flagged_clauses": ["<concerning or unusual clauses>"]
}}"""
        
        response = await self.agent_llm.client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1
        )
        
        return DocumentFlags(**response.structured_output)
    
    async def _full_classification(self, doc: DocumentInput) -> DocumentClassificationResult:
        """Perform complete document classification"""
        # Get classification
        classification = await self._classify_document(doc)
        
        # Get metadata
        metadata = await self._extract_metadata(doc)
        
        # Get flags
        flags = await self._extract_flags(doc)
        
        # Determine storage path and next actions
        storage_path = self._generate_storage_path(classification, metadata, doc)
        next_actions = self._determine_next_actions(classification, flags)
        related_types = self._get_related_document_types(classification.document_type)
        
        return DocumentClassificationResult(
            classification=classification,
            metadata=metadata,
            flags=flags,
            suggested_storage_path=storage_path,
            related_document_types=related_types,
            next_actions=next_actions
        )
    
    def _generate_storage_path(
        self,
        classification: DocumentClassification,
        metadata: DocumentMetadata,
        doc: DocumentInput
    ) -> str:
        """Generate suggested storage path"""
        practice = classification.practice_area
        doc_type = classification.document_type
        
        # Use matter ID if available
        if doc.matter_id:
            return f"/matters/{doc.matter_id}/{doc_type}/{doc.filename}"
        
        # Otherwise use practice area organization
        year = metadata.date[:4] if metadata.date else "undated"
        return f"/{practice}/{doc_type}/{year}/{doc.filename}"
    
    def _determine_next_actions(
        self,
        classification: DocumentClassification,
        flags: DocumentFlags
    ) -> List[str]:
        """Determine next actions based on classification and flags"""
        actions = []
        
        if flags.time_sensitive:
            actions.append("extract_deadlines")
            actions.append("create_calendar_reminders")
        
        if classification.document_type in ["contract", "commercial_contract", "employment_contract"]:
            actions.append("extract_obligations")
            actions.append("identify_key_dates")
        
        if flags.privileged:
            actions.append("mark_privileged")
            actions.append("restrict_access")
        
        if classification.is_draft:
            actions.append("track_versions")
        
        if not classification.is_executed and classification.document_type.endswith("contract"):
            actions.append("pending_signature")
        
        return actions
    
    def _get_related_document_types(self, doc_type: str) -> List[str]:
        """Get related document types for this classification"""
        related_map = {
            "employment_contract": ["offer_letter", "job_description", "employee_handbook"],
            "commercial_contract": ["nda", "purchase_order", "invoice"],
            "lease_agreement": ["title_deed", "search_results", "licence_to_assign"],
            "claim_form": ["defence", "witness_statement", "disclosure_list"],
            "shareholders_agreement": ["articles_of_association", "board_minutes"]
        }
        return related_map.get(doc_type, [])
