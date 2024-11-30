import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def get_issue_types(state: Dict[str, Any]) -> Dict[str, Any]:
    """Get available issue types."""
    try:
        logger.info("Getting issue types")
        get_types_tool = next(t for t in state["tools"] if t.name == "get_issue_types")
        issue_types = await get_types_tool.ainvoke({})
        
        if not issue_types:
            state["status"] = "error"
            state["response"] = "No issue types available"
            return state
            
        state["available_issue_types"] = issue_types
        state["status"] = "get_fields"
        return state
        
    except Exception as e:
        logger.error(f"Error getting issue types: {e}", exc_info=True)
        state["status"] = "error"
        state["response"] = f"Error getting issue types: {str(e)}"
        return state

async def get_required_fields(state: Dict[str, Any]) -> Dict[str, Any]:
    """Get required fields for selected issue type."""
    try:
        # Select appropriate issue type based on request
        # For now just using first one, but you could add logic to select based on request
        state["issue_type"] = state["available_issue_types"][0]
        
        logger.info(f"Getting fields for issue type: {state['issue_type']['name']}")
        get_fields_tool = next(t for t in state["tools"] if t.name == "get_required_fields")
        fields = await get_fields_tool.ainvoke({
            "issue_type_id": state["issue_type"]["id"]
        })
        
        state["required_fields"] = fields
        state["status"] = "create_ticket"
        return state
        
    except Exception as e:
        logger.error(f"Error getting required fields: {e}", exc_info=True)
        state["status"] = "error"
        state["response"] = f"Error getting required fields: {str(e)}"
        return state

async def create_ticket(state: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update ticket."""
    try:
        if state["ticket_id"]:
            # Update existing ticket
            logger.info(f"Updating ticket: {state['ticket_id']}")
            result = await state["edit_tool"].ainvoke({
                "request": state["request"],
                "ticket_id": state["ticket_id"]
            })
        else:
            # Create new ticket
            create_request = (
                f"Create a new {state['issue_type']['name']} ticket with the following information:\n"
                f"User's description: {state['request']}"
            )
            logger.info("Creating new ticket")
            result = await state["edit_tool"].ainvoke({
                "request": create_request,
                "ticket_id": None
            })
        
        state["response"] = result
        state["status"] = "validate"
        return state
        
    except Exception as e:
        logger.error(f"Error in ticket operation: {e}", exc_info=True)
        state["status"] = "error"
        state["response"] = f"Error in ticket operation: {str(e)}"
        return state

async def validate_result(state: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the operation result."""
    try:
        logger.info(f"Validating result. Status: {state['status']}")
        
        if state["status"] == "error":
            if state["retry_count"] >= state["max_retries"]:
                state["status"] = "max_retries"
                return state
            
            state["retry_count"] += 1
            state["status"] = "retry"
            return state
            
        if "Successfully" in state.get("response", ""):
            state["status"] = "complete"
            return state
            
        state["status"] = "retry"
        return state
        
    except Exception as e:
        logger.error(f"Error in validation: {e}", exc_info=True)
        state["status"] = "error"
        state["response"] = f"Error in validation: {str(e)}"
        return state