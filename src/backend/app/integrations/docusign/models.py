from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Constants for DocuSign envelope status
ENVELOPE_STATUS = {
    "CREATED": "Envelope has been created",
    "SENT": "Envelope has been sent to recipients",
    "DELIVERED": "Envelope has been delivered to recipients",
    "SIGNED": "Envelope has been signed by all recipients",
    "COMPLETED": "Envelope process has been completed",
    "DECLINED": "Envelope has been declined by a recipient",
    "VOIDED": "Envelope has been voided",
    "EXPIRED": "Envelope has expired"
}

# Constants for DocuSign recipient status
RECIPIENT_STATUS = {
    "CREATED": "Recipient has been created",
    "SENT": "Envelope has been sent to recipient",
    "DELIVERED": "Envelope has been delivered to recipient",
    "SIGNED": "Recipient has signed the document",
    "COMPLETED": "Recipient has completed all required actions",
    "DECLINED": "Recipient has declined to sign",
    "AUTORESPONDED": "Recipient has auto-responded"
}

# Constants for DocuSign recipient types
RECIPIENT_TYPES = {
    "SIGNER": "Recipient needs to sign the document",
    "CC": "Recipient receives a copy of the document",
    "INPERSONSIGNER": "Recipient signs in person",
    "EDITOR": "Recipient can edit the document",
    "INTERMEDIARY": "Recipient routes the envelope to recipients"
}


class DocuSignConfig(BaseModel):
    """Configuration model for DocuSign API integration."""
    client_id: str
    client_secret: str
    authorization_server: str
    account_id: str
    user_id: str
    private_key_path: Optional[str] = None
    base_path: str
    use_jwt_auth: bool = False
    callback_url: Optional[str] = None

    def model_config(self):
        """Pydantic model configuration"""
        return {
            "arbitrary_types_allowed": True,
            "extra": "forbid"
        }

    @validator("use_jwt_auth")
    def validate_jwt_auth(cls, use_jwt_auth, values):
        """Validate JWT authentication configuration."""
        if use_jwt_auth and not values.get("private_key_path"):
            raise ValueError("private_key_path is required when use_jwt_auth is True")
        return use_jwt_auth


class Recipient(BaseModel):
    """Model for DocuSign envelope recipient."""
    email: str
    name: str
    recipient_id: str
    recipient_type: str
    routing_order: Optional[str] = "1"
    status: Optional[str] = None
    status_changed_datetime: Optional[datetime] = None
    signing_url: Optional[str] = None

    @classmethod
    def from_docusign_response(cls, data: Dict[str, Any]) -> "Recipient":
        """Create Recipient instance from DocuSign API response."""
        return cls(
            email=data.get("email", ""),
            name=data.get("name", ""),
            recipient_id=data.get("recipientId", ""),
            recipient_type=data.get("recipientType", ""),
            routing_order=data.get("routingOrder", "1"),
            status=data.get("status", None),
            status_changed_datetime=data.get("statusChangedDateTime", None),
            signing_url=data.get("signingUrl", None)
        )

    def to_docusign_dict(self) -> Dict[str, Any]:
        """Convert Recipient to DocuSign API format."""
        result = {
            "email": self.email,
            "name": self.name,
            "recipientId": self.recipient_id,
            "routingOrder": self.routing_order,
        }

        # Add recipient type-specific fields
        if self.recipient_type.upper() == "SIGNER":
            result.update({
                "recipientType": "signer",
                "tabs": {
                    "signHereTabs": [],
                    "dateSignedTabs": [],
                }
            })
        elif self.recipient_type.upper() == "CC":
            result.update({"recipientType": "cc"})
        elif self.recipient_type.upper() == "INPERSONSIGNER":
            result.update({"recipientType": "inPersonSigner"})
        elif self.recipient_type.upper() == "EDITOR":
            result.update({"recipientType": "editor"})
        elif self.recipient_type.upper() == "INTERMEDIARY":
            result.update({"recipientType": "intermediary"})

        return result


class DocumentInfo(BaseModel):
    """Model for document information in DocuSign envelope."""
    document_id: str
    name: str
    file_extension: Optional[str] = None
    content: Optional[bytes] = None
    document_base64: Optional[str] = None

    @classmethod
    def from_docusign_response(cls, data: Dict[str, Any]) -> "DocumentInfo":
        """Create DocumentInfo instance from DocuSign API response."""
        return cls(
            document_id=data.get("documentId", ""),
            name=data.get("name", ""),
            file_extension=data.get("fileExtension", None),
        )

    def to_docusign_dict(self) -> Dict[str, Any]:
        """Convert DocumentInfo to DocuSign API format."""
        result = {
            "documentId": self.document_id,
            "name": self.name,
        }

        if self.file_extension:
            result["fileExtension"] = self.file_extension

        if self.document_base64:
            result["documentBase64"] = self.document_base64

        return result


class EnvelopeCreate(BaseModel):
    """Model for creating a new DocuSign envelope."""
    email_subject: str
    email_body: Optional[str] = None
    documents: List[DocumentInfo]
    recipients: List[Recipient]
    status: str  # draft, sent, etc.
    envelope_id: Optional[str] = None
    notification_uri: Optional[str] = None
    event_types: Optional[List[str]] = None

    @validator("status")
    def validate_status(cls, status):
        """Validate envelope status."""
        if status.upper() not in ENVELOPE_STATUS:
            raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(ENVELOPE_STATUS.keys())}")
        return status

    def to_docusign_dict(self) -> Dict[str, Any]:
        """Convert EnvelopeCreate to DocuSign API format."""
        result = {
            "emailSubject": self.email_subject,
            "status": self.status,
        }

        if self.email_body:
            result["emailBlurb"] = self.email_body

        # Add documents
        if self.documents:
            result["documents"] = [doc.to_docusign_dict() for doc in self.documents]

        # Add recipients
        if self.recipients:
            recipients_dict = {}
            for recipient in self.recipients:
                recipient_type = recipient.recipient_type.lower()
                if recipient_type not in recipients_dict:
                    recipients_dict[recipient_type + "s"] = []
                recipients_dict[recipient_type + "s"].append(recipient.to_docusign_dict())
            result["recipients"] = recipients_dict

        # Add event notification
        if self.notification_uri:
            result["eventNotification"] = {
                "url": self.notification_uri,
                "loggingEnabled": "true",
                "requireAcknowledgment": "true",
                "useSoapInterface": "false",
                "includeCertificateWithSoap": "false",
                "signMessageWithX509Cert": "false",
                "includeDocuments": "false",
                "includeEnvelopeVoidReason": "true",
                "includeTimeZone": "true",
                "includeSenderAccountAsCustomField": "true",
                "includeDocumentFields": "true",
                "includeCertificateOfCompletion": "true",
            }

            if self.event_types:
                result["eventNotification"]["envelopeEvents"] = [
                    {"envelopeEventStatusCode": event_type} for event_type in self.event_types
                ]

        return result


class Envelope(BaseModel):
    """Model for DocuSign envelope information."""
    envelope_id: str
    status: str
    status_changed_datetime: Optional[datetime] = None
    created_datetime: Optional[datetime] = None
    sent_datetime: Optional[datetime] = None
    completed_datetime: Optional[datetime] = None
    delivered_datetime: Optional[datetime] = None
    declined_datetime: Optional[datetime] = None
    voided_datetime: Optional[datetime] = None
    email_subject: Optional[str] = None
    recipients: Optional[List[Recipient]] = None
    documents: Optional[List[DocumentInfo]] = None

    @classmethod
    def from_docusign_response(cls, data: Dict[str, Any]) -> "Envelope":
        """Create Envelope instance from DocuSign API response."""
        envelope = cls(
            envelope_id=data.get("envelopeId", ""),
            status=data.get("status", ""),
            status_changed_datetime=data.get("statusChangedDateTime", None),
            created_datetime=data.get("createdDateTime", None),
            sent_datetime=data.get("sentDateTime", None),
            completed_datetime=data.get("completedDateTime", None),
            delivered_datetime=data.get("deliveredDateTime", None),
            declined_datetime=data.get("declinedDateTime", None),
            voided_datetime=data.get("voidedDateTime", None),
            email_subject=data.get("emailSubject", None),
        )

        # Add recipients if present
        if "recipients" in data and data["recipients"]:
            envelope.recipients = []
            for recipient_type in ["signers", "carbonCopies", "inPersonSigners", "editors", "intermediaries"]:
                if recipient_type in data["recipients"] and data["recipients"][recipient_type]:
                    for recipient_data in data["recipients"][recipient_type]:
                        recipient_data["recipientType"] = recipient_type[:-1]  # Remove the 's' at the end
                        envelope.recipients.append(Recipient.from_docusign_response(recipient_data))

        # Add documents if present
        if "documents" in data and data["documents"]:
            envelope.documents = [
                DocumentInfo.from_docusign_response(doc_data) for doc_data in data["documents"]
            ]

        return envelope


class EnvelopeStatusUpdate(BaseModel):
    """Model for updating DocuSign envelope status."""
    envelope_id: str
    status: str
    status_reason: Optional[str] = None

    @validator("status")
    def validate_status(cls, status):
        """Validate envelope status."""
        if status.upper() not in ENVELOPE_STATUS:
            raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(ENVELOPE_STATUS.keys())}")
        return status

    def to_docusign_dict(self) -> Dict[str, Any]:
        """Convert EnvelopeStatusUpdate to DocuSign API format."""
        result = {
            "status": self.status,
        }

        if self.status_reason:
            result["statusReason"] = self.status_reason

        return result


class WebhookEvent(BaseModel):
    """Model for DocuSign webhook event notification."""
    envelope_id: str
    status: str
    event_type: Optional[str] = None
    status_changed_datetime: Optional[datetime] = None
    recipients: Optional[List[Recipient]] = None
    raw_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_docusign_payload(cls, payload: Dict[str, Any]) -> "WebhookEvent":
        """Create WebhookEvent instance from DocuSign webhook payload."""
        # Extract envelope data
        envelope_data = payload.get("envelopeStatus", {}) or payload.get("envelope", {})
        if not envelope_data:
            envelope_data = payload  # Fallback if no specific envelope data found

        # Extract recipients if present
        recipients = None
        if "recipients" in envelope_data and envelope_data["recipients"]:
            recipients = []
            for recipient_type in ["signers", "carbonCopies", "inPersonSigners", "editors", "intermediaries"]:
                if recipient_type in envelope_data["recipients"] and envelope_data["recipients"][recipient_type]:
                    for recipient_data in envelope_data["recipients"][recipient_type]:
                        recipient_data["recipientType"] = recipient_type[:-1]  # Remove the 's' at the end
                        recipients.append(Recipient.from_docusign_response(recipient_data))

        return cls(
            envelope_id=envelope_data.get("envelopeId", ""),
            status=envelope_data.get("status", ""),
            event_type=payload.get("event", None),
            status_changed_datetime=envelope_data.get("statusChangedDateTime", None),
            recipients=recipients,
            raw_data=payload,
        )


class SigningUrl(BaseModel):
    """Model for DocuSign signing URL."""
    url: str
    envelope_id: Optional[str] = None
    recipient_id: Optional[str] = None

    @classmethod
    def from_docusign_response(cls, data: Dict[str, Any], envelope_id: Optional[str] = None, recipient_id: Optional[str] = None) -> "SigningUrl":
        """Create SigningUrl instance from DocuSign API response."""
        return cls(
            url=data.get("url", ""),
            envelope_id=envelope_id,
            recipient_id=recipient_id,
        )


class TemplateInfo(BaseModel):
    """Model for DocuSign template information."""
    template_id: str
    name: str
    description: Optional[str] = None
    created_datetime: Optional[datetime] = None
    last_modified_datetime: Optional[datetime] = None
    recipients: Optional[List[Recipient]] = None
    documents: Optional[List[DocumentInfo]] = None

    @classmethod
    def from_docusign_response(cls, data: Dict[str, Any]) -> "TemplateInfo":
        """Create TemplateInfo instance from DocuSign API response."""
        template = cls(
            template_id=data.get("templateId", ""),
            name=data.get("name", ""),
            description=data.get("description", None),
            created_datetime=data.get("created", None),
            last_modified_datetime=data.get("lastModified", None),
        )

        # Add recipients if present
        if "recipients" in data and data["recipients"]:
            template.recipients = []
            for recipient_type in ["signers", "carbonCopies", "inPersonSigners", "editors", "intermediaries"]:
                if recipient_type in data["recipients"] and data["recipients"][recipient_type]:
                    for recipient_data in data["recipients"][recipient_type]:
                        recipient_data["recipientType"] = recipient_type[:-1]  # Remove the 's' at the end
                        template.recipients.append(Recipient.from_docusign_response(recipient_data))

        # Add documents if present
        if "documents" in data and data["documents"]:
            template.documents = [
                DocumentInfo.from_docusign_response(doc_data) for doc_data in data["documents"]
            ]

        return template