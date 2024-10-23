import logging

logger = logging.getLogger(__name__)

def route_action(state):
    logger.debug(f"Edge: route_action called with state: {state}")
    if state["action"] == "delete":
        return "delete"
    elif state["action"] == "add":
        return "add"
    else:
        raise ValueError(f"Invalid action: {state['action']}")
