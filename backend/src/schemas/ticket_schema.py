import re
from typing import Optional, List
from pydantic import BaseModel, root_validator

class Ticket(BaseModel):
    ticket_api: str
    ticket_url: str
    issue_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    sprint: Optional[str] = None
    embedding_vector: Optional[str] = None

class TicketContent(BaseModel):
    title: str = "No title provided"
    description: str = "No description provided"
    comments: List[str] = []

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
        title = fields.get('summary') or "No title provided"
        description = fields.get('description') or "No description provided"
        
        # Process comments with author names
        comments = fields.get('comment', {}).get('comments', [])
        comments_list = [
            f"{comment.get('author', {}).get('displayName', 'Unknown')}: {comment.get('body', '')}"
            for comment in comments
        ] if comments else []

        # Create content structure with default values
        values['content'] = {
            "title": title,
            "description": description,
            "comments": comments_list
        }

        return values

class JiraIssueSchema(Ticket):
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
        values['issue_type'] = fields.get('issuetype', {}).get('name') if fields.get('issuetype') else None
        values['status'] = fields.get('status', {}).get('name') if fields.get('status') else None
        values['priority'] = fields.get('priority', {}).get('name') if fields.get('priority') else None

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
