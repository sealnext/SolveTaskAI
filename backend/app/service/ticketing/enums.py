from enum import Enum


class TicketingSystemType(str, Enum):
	JIRA = 'jira'
	AZURE = 'azure'
