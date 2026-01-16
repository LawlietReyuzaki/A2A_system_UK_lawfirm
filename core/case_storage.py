"""
Case Storage System

Persistent storage for all processed cases (emails, voice calls, chats, documents).
Uses JSON file storage for simplicity - can be swapped for a database in production.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class CaseType(str, Enum):
    EMAIL = "email"
    VOICE_CALL = "voice_call"
    CHAT = "chat"
    DOCUMENT = "document"


class CaseStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class StoredCase(BaseModel):
    """A stored case with all its data"""
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    case_type: CaseType
    status: CaseStatus = CaseStatus.PENDING
    
    # Input data from customer
    input_data: Dict[str, Any]
    
    # Agent processing results
    processing_result: Optional[Dict[str, Any]] = None
    
    # Classification results (for grouping/filtering)
    classification: Optional[Dict[str, Any]] = None  # intent, urgency, practice_area, etc.
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    processed_at: Optional[str] = None
    processing_duration_ms: Optional[int] = None
    
    # Customer info
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Flags
    requires_human_review: bool = False
    escalation_reason: Optional[str] = None
    
    # Attachments (filenames)
    attachments: List[str] = Field(default_factory=list)


class CaseStorage:
    """
    Simple JSON-based case storage.
    In production, replace with PostgreSQL/MongoDB/etc.
    """
    
    def __init__(self, storage_path: str = "data/cases.json"):
        self.storage_path = storage_path
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Create storage directory and file if they don't exist"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            self._save_all([])
    
    def _load_all(self) -> List[Dict[str, Any]]:
        """Load all cases from storage"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_all(self, cases: List[Dict[str, Any]]):
        """Save all cases to storage"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(cases, f, indent=2, default=str)
    
    def create(self, case: StoredCase) -> StoredCase:
        """Create a new case"""
        cases = self._load_all()
        cases.append(case.model_dump())
        self._save_all(cases)
        return case
    
    def update(self, case_id: str, updates: Dict[str, Any]) -> Optional[StoredCase]:
        """Update an existing case"""
        cases = self._load_all()
        for i, c in enumerate(cases):
            if c.get('case_id') == case_id:
                cases[i].update(updates)
                self._save_all(cases)
                return StoredCase(**cases[i])
        return None
    
    def get(self, case_id: str) -> Optional[StoredCase]:
        """Get a case by ID"""
        cases = self._load_all()
        for c in cases:
            if c.get('case_id') == case_id:
                return StoredCase(**c)
        return None
    
    def get_all(self, case_type: Optional[CaseType] = None, limit: int = 100) -> List[StoredCase]:
        """Get all cases, optionally filtered by type"""
        cases = self._load_all()
        
        if case_type:
            cases = [c for c in cases if c.get('case_type') == case_type.value]
        
        # Sort by created_at descending (newest first)
        cases.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return [StoredCase(**c) for c in cases[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored cases"""
        cases = self._load_all()
        
        stats = {
            'total': len(cases),
            'by_type': {},
            'by_status': {},
            'by_practice_area': {},
            'by_urgency': {},
            'requires_review': 0
        }
        
        for c in cases:
            # By type
            ct = c.get('case_type', 'unknown')
            stats['by_type'][ct] = stats['by_type'].get(ct, 0) + 1
            
            # By status
            status = c.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # By classification
            classification = c.get('classification', {})
            if classification:
                pa = classification.get('practice_area', 'unknown')
                stats['by_practice_area'][pa] = stats['by_practice_area'].get(pa, 0) + 1
                
                urgency = classification.get('urgency', 'unknown')
                stats['by_urgency'][urgency] = stats['by_urgency'].get(urgency, 0) + 1
            
            # Requires review
            if c.get('requires_human_review'):
                stats['requires_review'] += 1
        
        return stats
    
    def delete(self, case_id: str) -> bool:
        """Delete a case"""
        cases = self._load_all()
        original_len = len(cases)
        cases = [c for c in cases if c.get('case_id') != case_id]
        if len(cases) < original_len:
            self._save_all(cases)
            return True
        return False
    
    def clear_all(self):
        """Clear all cases (use with caution!)"""
        self._save_all([])


# Global storage instance
case_storage = CaseStorage()
