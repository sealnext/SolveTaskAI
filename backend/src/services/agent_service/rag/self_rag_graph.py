from langgraph.graph import StateGraph, END
from .nodes import retrieve_documents, grade_documents, generate_answer
from .state import AgentState

def create_self_rag_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve_documents", retrieve_documents)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate_answer", generate_answer)
    
    workflow.set_entry_point("retrieve_documents")
    workflow.add_edge("retrieve_documents", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        lambda x: "useful" if x["documents"] else "not_useful",
        {
            "useful": "generate_answer",
            "not_useful": END,
        },
    )
    workflow.add_edge("generate_answer", END)
    
    graph = workflow.compile()
    return graph.with_config({"use_injected_graph_state": True})
