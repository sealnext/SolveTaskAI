import re
from typing import Optional, List
import json
from pydantic import BaseModel, root_validator

import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel, root_validator
from typing import Optional, List, Dict, Any


class EditableTicketSchema(BaseModel):
    ticket_url: str
    ticket_api: str
    modifiable_fields: Dict[str, Any] = {}
    comments: List[str] = []

    @root_validator(pre=True)
    def extract_fields(cls, values):
        # Extract base URLs and identifiers
        api_self_url = values.get("self", "")
        base_url = "/".join(api_self_url.split("/")[:3])
        ticket_key = values.get("key", "")

        values["ticket_url"] = f"{base_url}/browse/{ticket_key}"
        values["ticket_api"] = api_self_url

        # Extract editable fields from editmeta
        editmeta_fields = values.get("editmeta", {}).get("fields", {})
        modifiable_fields = {}
        for field_key, field_data in editmeta_fields.items():
            if "operations" in field_data:
                # Include only modifiable fields
                modifiable_fields[field_key] = {
                    "key": field_data.get("key"),
                    "operations": field_data.get("operations"),
                    "value": values.get("fields", {}).get(field_key)
                }

        comments_data = values.get("fields", {}).get("comment", {}).get("comments", [])
        comments_list = [
            f"[{comment.get('id', 'Unknown ID')}] {comment.get('author', {}).get('displayName', 'Unknown')}: {comment.get('body', '')}"
            for comment in comments_data
        ]

        values["modifiable_fields"] = modifiable_fields
        values["comments"] = comments_list

        return values


class Ticket(BaseModel):
    ticket_api: str
    ticket_url: str
    issue_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    sprint: Optional[str] = None
    embedding_vector: Optional[str] = None
    labels: Optional[List[str]] = None
    resolution: Optional[str] = None
    parent: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    resolutiondate: Optional[str] = None

class TicketContent(BaseModel):
    summary: str = "No title provided"
    description: str = "No description provided"
    comments: List[str] = []

    def __str__(self):
        return json.dumps({
            "summary": self.summary,
            "description": self.description,
            "comments": self.comments
        }, indent=1)

class JiraIssueContentSchema(BaseModel):
    content: TicketContent
    ticket_api: str
    ticket_url: str
    
    class Config:
        populate_by_name = True

    @root_validator(pre=True)
    def flatten_fields(cls, values):
        fields = values.get('fields', {})

        api_self_url = values.get('self', "")
        base_url = "/".join(api_self_url.split("/")[:3])
        ticket_key = values.get('key', None)
        values['ticket_url'] = f"{base_url}/browse/{ticket_key}"
        values['ticket_api'] = api_self_url

        # Extract content components with default values
        summary = fields.get('summary') or "No title provided"
        description = fields.get('description') or "No description provided"
        
        # Process comments with author names
        comments = fields.get('comment', {}).get('comments', [])
        comments_list = [
            f"{comment.get('author', {}).get('displayName', 'Unknown')}: {comment.get('body', '')}"
            for comment in comments
        ] if comments else []

        # Create content structure with default values
        values['content'] = {
            "summary": summary,
            "description": description,
            "comments": comments_list
        }

        return values

class JiraIssueSchema(Ticket):
    class Config:
        populate_by_name = True
        extra = "ignore"

    @root_validator(pre=True)
    def flatten_fields(cls, values):
        fields = values.get('fields', {})

        api_self_url = values.get('self', "")
        base_url = "/".join(api_self_url.split("/")[:3])
        ticket_key = values.get('key', None)
        values['ticket_url'] = f"{base_url}/browse/{ticket_key}"
            
        values['ticket_api'] = api_self_url
        values['issue_type'] = fields.get('issuetype', {}).get('name') if fields.get('issuetype') else None
        values['status'] = fields.get('status', {}).get('name') if fields.get('status') else None
        values['priority'] = fields.get('priority', {}).get('name') if fields.get('priority') else None
        values['status'] = fields.get('status', {}).get('name') if fields.get('status') else None
        values['labels'] = fields.get('labels', [])
        values['resolution'] = fields.get('resolution', {}).get('name') if fields.get('resolution') else None
        values['parent'] = fields.get('parent', {}).get('fields', {}).get('summary') if fields.get('parent') else None
        values['assignee'] = fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None
        values['reporter'] = fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None
        values['resolutiondate'] = fields.get('resolutiondate')
        
        customfield_10020 = fields.get('customfield_10020', [])
        values['sprint'] = customfield_10020[0].get('name') if customfield_10020 and len(customfield_10020) > 0 else None

        ordered_fields = {
            'title': fields.get('summary', None),
            'description': fields.get('description', None),
        }

        comments = fields.get('comment', {}).get('comments', [])
        all_comments = " ".join(
            f"{comment.get('author', {}).get('displayName', 'Unknown')}: {comment.get('body', '')}"
            for comment in comments
        ) if comments else ""

        embedding_data = []

        if ordered_fields['title']:
            embedding_data.append(f"Title: {ordered_fields['title']}")

        if ordered_fields['description']:
            embedding_data.append(f"Description: {ordered_fields['description']}")

        if all_comments:
            embedding_data.append(f"Comments: {all_comments}")

        cleaned_embedding_data = [cls.clean_text(data) for data in embedding_data]
        values['embedding_vector'] = " | ".join(cleaned_embedding_data)
        
        logger.info(f"🎯 JiraIssueSchema: Ticket: {values}")

        return values
    
    @classmethod
    def clean_text(cls, text):
        """
        Cleans text by removing unnecessary whitespace, special characters, and normalizing it.
        """
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text
