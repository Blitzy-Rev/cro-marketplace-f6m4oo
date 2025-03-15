from typing import List, Dict, Optional, Any, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc

from .base import CRUDBase
from ..models.prediction import Prediction, PredictionStatus
from ..schemas.prediction import PredictionCreate, PredictionUpdate, PredictionBatchCreate, PredictionBatchUpdate
from ..db.session import db_session
from ..core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class CRUDPrediction(CRUDBase[Prediction, PredictionCreate, PredictionUpdate]):
    """CRUD operations for Prediction models with specialized methods for AI predictions"""
    
    def __init__(self):
        """Initialize the CRUD prediction class with the Prediction model"""
        super().__init__(Prediction)
    
    def create_prediction(
        self,
        molecule_id: UUID,
        property_name: str,
        value: Union[str, int, float, bool],
        confidence: float,
        model_name: str,
        model_version: Optional[str] = None,
        units: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> Prediction:
        """Create a new prediction from AI prediction result"""
        db_session_local = db or db_session
        
        prediction = Prediction.from_ai_prediction(
            molecule_id=molecule_id,
            property_name=property_name,
            value=value,
            confidence=confidence,
            model_name=model_name,
            model_version=model_version,
            units=units,
            metadata=metadata
        )
        
        db_session_local.add(prediction)
        db_session_local.commit()
        db_session_local.refresh(prediction)
        
        return prediction
    
    def get_by_molecule_id(
        self,
        molecule_id: UUID,
        db: Optional[Session] = None,
        min_confidence: Optional[float] = None
    ) -> List[Prediction]:
        """Get all predictions for a specific molecule"""
        db_session_local = db or db_session
        
        query = select(Prediction).where(Prediction.molecule_id == molecule_id)
        
        if min_confidence is not None:
            query = query.where(Prediction.confidence >= min_confidence)
        
        result = db_session_local.execute(query)
        return result.scalars().all()
    
    def get_by_molecule_and_property(
        self,
        molecule_id: UUID,
        property_name: str,
        db: Optional[Session] = None
    ) -> List[Prediction]:
        """Get predictions for a specific molecule and property"""
        db_session_local = db or db_session
        
        query = select(Prediction).where(
            and_(
                Prediction.molecule_id == molecule_id,
                Prediction.property_name == property_name
            )
        )
        
        result = db_session_local.execute(query)
        return result.scalars().all()
    
    def get_latest_prediction(
        self,
        molecule_id: UUID,
        property_name: str,
        db: Optional[Session] = None
    ) -> Optional[Prediction]:
        """Get the latest prediction for a molecule and property"""
        db_session_local = db or db_session
        
        query = select(Prediction).where(
            and_(
                Prediction.molecule_id == molecule_id,
                Prediction.property_name == property_name
            )
        ).order_by(
            desc(Prediction.created_at)
        ).limit(1)
        
        result = db_session_local.execute(query)
        return result.scalars().first()
    
    def get_valid_predictions(
        self,
        min_confidence: Optional[float] = None,
        db: Optional[Session] = None
    ) -> List[Prediction]:
        """Get completed predictions with confidence above threshold"""
        db_session_local = db or db_session
        
        query = select(Prediction).where(Prediction.status == PredictionStatus.COMPLETED)
        
        if min_confidence is not None:
            query = query.where(Prediction.confidence >= min_confidence)
        
        result = db_session_local.execute(query)
        return result.scalars().all()
    
    def update_prediction_status(
        self,
        prediction_id: UUID,
        status: PredictionStatus,
        error_message: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[Prediction]:
        """Update the status of a prediction"""
        db_session_local = db or db_session
        
        prediction = self.get(prediction_id, db=db_session_local)
        
        if not prediction:
            return None
        
        prediction.status = status
        
        if error_message and status == PredictionStatus.FAILED:
            prediction.error_message = error_message
        
        db_session_local.commit()
        db_session_local.refresh(prediction)
        
        return prediction
    
    def update_prediction_value(
        self,
        prediction_id: UUID,
        value: Union[str, int, float, bool],
        confidence: float,
        db: Optional[Session] = None
    ) -> Optional[Prediction]:
        """Update the value and confidence of a prediction"""
        db_session_local = db or db_session
        
        prediction = self.get(prediction_id, db=db_session_local)
        
        if not prediction:
            return None
        
        prediction.value = value
        prediction.confidence = confidence
        prediction.status = PredictionStatus.COMPLETED
        
        db_session_local.commit()
        db_session_local.refresh(prediction)
        
        return prediction
    
    def create_batch(
        self,
        batch_data: PredictionBatchCreate,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Create a new prediction batch"""
        db_session_local = db or db_session
        
        # Create new prediction batch record
        batch = {
            "id": UUID(),
            "molecule_ids": batch_data.molecule_ids,
            "properties": batch_data.properties,
            "model_name": batch_data.model_name,
            "model_version": batch_data.model_version,
            "options": batch_data.options,
            "status": PredictionStatus.PENDING,
            "total_count": len(batch_data.molecule_ids) * len(batch_data.properties),
            "completed_count": 0,
            "failed_count": 0,
            "created_by": batch_data.created_by,
            "created_at": datetime.now(),
            "external_job_id": batch_data.external_job_id
        }
        
        # In a real implementation, this would be saved to the database
        
        return batch
    
    def update_batch(
        self,
        batch_id: UUID,
        batch_data: PredictionBatchUpdate,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Update a prediction batch"""
        db_session_local = db or db_session
        
        batch = self.get_batch(batch_id, db=db_session_local)
        
        if not batch:
            raise ValueError(f"Prediction batch {batch_id} not found")
        
        # Update batch with new data
        # In a real implementation, this would update a database record
        
        return batch
    
    def get_batch(
        self,
        batch_id: UUID,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a prediction batch by ID"""
        # This would query the database for the batch record
        return None
    
    def get_batch_predictions(
        self,
        batch_id: UUID,
        db: Optional[Session] = None
    ) -> List[Prediction]:
        """Get all predictions associated with a batch"""
        db_session_local = db or db_session
        
        batch = self.get_batch(batch_id, db=db_session_local)
        
        if not batch:
            return []
        
        # This would query predictions associated with the batch
        # In a real implementation, predictions would have a batch_id field or similar
        
        return []
    
    def filter_predictions(
        self,
        molecule_id: Optional[UUID] = None,
        property_names: Optional[List[str]] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        status: Optional[PredictionStatus] = None,
        min_confidence: Optional[float] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        db: Optional[Session] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Filter predictions based on various criteria"""
        db_session_local = db or db_session
        
        query = select(Prediction)
        filters = []
        
        if molecule_id:
            filters.append(Prediction.molecule_id == molecule_id)
            
        if property_names:
            filters.append(Prediction.property_name.in_(property_names))
            
        if model_name:
            filters.append(Prediction.model_name == model_name)
            
        if model_version:
            filters.append(Prediction.model_version == model_version)
            
        if status:
            filters.append(Prediction.status == status)
            
        if min_confidence is not None:
            filters.append(Prediction.confidence >= min_confidence)
            
        if created_after:
            filters.append(Prediction.created_at >= created_after)
            
        if created_before:
            filters.append(Prediction.created_at <= created_before)
        
        if filters:
            query = query.where(and_(*filters))
        
        count_query = select(func.count()).select_from(query.subquery())
        total = db_session_local.execute(count_query).scalar() or 0
        
        query = query.offset(skip).limit(limit)
        result = db_session_local.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

# Singleton instance for application-wide use
prediction = CRUDPrediction()