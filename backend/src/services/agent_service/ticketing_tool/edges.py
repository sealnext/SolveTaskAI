from typing import Literal
from .state import TicketingState

def decide_next_action(state: TicketingState) -> Literal["retry", "complete", "max_retries"]:
    """Determine the next action based on the current state.
    
    Args:
        state: The current state of the ticketing workflow
        
    Returns:
        Literal["retry", "complete", "max_retries"]: The next action to take
    """
    if state["status"] == "max_retries":
        return "max_retries"
        
    if state["status"] == "complete":
        return "complete"
        
    return "retry" 