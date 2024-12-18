Comprehensive Design Patterns for Structuring a LangGraph Agent

0. Most important thing
- always ask me back if you are not sure about something in langgraph/langchain as I am the one who will be giving you information about the documentation. ALWAYS ask me back if you need more context about how to use the library. If you are not sure about something in langgraph, ask me back. ( VERY IMPORTANT )

1. Project Planning
- Define agent responsibilities and plan state management needs.
- Break down workflows into distinct graphs, only creating subgraphs when complexity requires.
- Identify shared components for reuse across graphs.
2. Development Order
- Define base configuration and state classes (e.g., AgentState using dataclasses for immutability).
- Build the core graph structure with clear transitions.
- Add shared utilities and reusable tools last.
3. Core Patterns and Best Practices
- State Management
- Use @dataclass(kw_only=True) for immutable, typed states.
- Separate concerns into input, agent, and output states.
- Type-safe transitions with annotated fields and reducers.
- Configuration Management
- Centralized configuration using type-safe defaults (e.g., AgentConfiguration).
- Environment-based and metadata-driven configurations.
- Dependency injection for external services and caching where applicable.
- Modular Architecture
- Divide core functionalities into modules (draft, critique, check) with single responsibility.
- Clear separation of routing and processing logic.
- Reusable utilities for cross-graph components.
4. Workflow and Flow Control Patterns
- Builder Pattern
- Use a graph-building approach with add_edge and add_conditional_edges for dynamic flow:
```python
builder.add_edge(START, "analyze_and_route_query")
builder.add_conditional_edges("analyze_and_route_query", route_query)
builder.add_edge("respond", END)
```
- Structure workflows as state machines with explicit END transitions.
- Strategy Pattern for Query Routing
- Dynamically route queries based on state and classification:
```python
def route_query(state: AgentState) -> Literal["create_research_plan", "ask_for_more_info", "respond_to_general_query"]:
    if state.router["type"] == "langchain":
        return "create_research_plan"
    elif state.router["type"] == "more-info":
        return "ask_for_more_info"
    elif state.router["type"] == "general":
        return "respond_to_general_query"
    else:
        raise ValueError("Unknown router type.")
```
- Chain of Responsibility
- Sequential query analysis and routing using clearly defined nodes:
```python
async def analyze_and_route_query(state: AgentState, config: RunnableConfig) -> dict[str, Router]:
    model = load_chat_model(config.query_model)
    response = await model.with_structured_output(Router).ainvoke(state.messages)
    return {"router": response}
5. Tooling and Integration Patterns
- Factory Pattern for Retrievers and Embeddings
- Centralized creation of tools dynamically based on configuration:
```python
@contextmanager
def make_retriever(config: RunnableConfig):
    if config.retriever_provider == "elastic":
        with make_elastic_retriever(config) as retriever:
            yield retriever
    else:
        raise ValueError("Unknown retriever provider.")
```
6. Tool Integration
- Structured tool definitions with Pydantic models for validation.
- Clear contracts and interfaces, separate from the main logic.
7. Error Handling & Validation
- Validate inputs with Pydantic models and explicit edge-case handling.
- Extract and validate code, providing actionable feedback for errors.
8. Message Handling
- Maintain consistent formats with a distinction between user and system messages.
- Use utilities for clean message transformations and state updates.
9. Testing and Documentation
- Testing Strategy
- Unit Tests: Validate individual components (state, utilities, tools).
- Integration Tests: Ensure workflows and transitions function end-to-end.
- Mocking: Replace external dependencies for isolated tests.
- Documentation
- Clear README for architecture and usage.
- Type hints and docstrings for all components.
- Detailed configuration documentation.
10. Guiding Philosophy
- Maintain consistent formats with a distinction between user and system messages.
- Use utilities for clean message transformations and state updates.
- Testing and Documentation:
- Testing Strategy
- Unit Tests: Validate individual components (state, utilities, tools).
- Integration Tests: Ensure workflows and transitions function end-to-end.
- Mocking: Replace external dependencies for isolated tests.
- Documentation
- Clear README for architecture and usage.
- Type hints and docstrings for all components.
- Detailed configuration documentation.
10. Guiding Philosophy
- Start with a simple graph, scaling complexity only when needed.
- Focus on type safety, clear state management, and modularity.
- Ensure separation of concerns, reusability, and maintainability.

Example of a well-defined graph:
```python
async def respond_to_general_query(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a response to a general query not related to LangChain.

    This node is called when the router classifies the query as a general question.

    Args:
        state (AgentState): The current state of the agent, including conversation history and router logic.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router["logic"]
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


async def create_research_plan(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[str] | str]:
    """Create a step-by-step research plan for answering a LangChain-related query.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used to generate the plan.

    Returns:
        dict[str, list[str]]: A dictionary with a 'steps' key containing the list of research steps.
    """

    class Plan(TypedDict):
        """Generate research plan."""

        steps: list[str]

    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model).with_structured_output(Plan)
    messages = [
        {"role": "system", "content": configuration.research_plan_system_prompt}
    ] + state.messages
    response = cast(Plan, await model.ainvoke(messages))
    return {"steps": response["steps"], "documents": "delete"}


async def conduct_research(state: AgentState) -> dict[str, Any]:
    """Execute the first step of the research plan.

    This function takes the first step from the research plan and uses it to conduct research.

    Args:
        state (AgentState): The current state of the agent, including the research plan steps.

    Returns:
        dict[str, list[str]]: A dictionary with 'documents' containing the research results and
                              'steps' containing the remaining research steps.

    Behavior:
        - Invokes the researcher_graph with the first step of the research plan.
        - Updates the state with the retrieved documents and removes the completed step.
    """
    result = await researcher_graph.ainvoke({"question": state.steps[0]})
    return {"documents": result["documents"], "steps": state.steps[1:]}


def check_finished(state: AgentState) -> Literal["respond", "conduct_research"]:
    """Determine if the research process is complete or if more research is needed.

    This function checks if there are any remaining steps in the research plan:
        - If there are, route back to the `conduct_research` node
        - Otherwise, route to the `respond` node

    Args:
        state (AgentState): The current state of the agent, including the remaining research steps.

    Returns:
        Literal["respond", "conduct_research"]: The next step to take based on whether research is complete.
    """
    if len(state.steps or []) > 0:
        return "conduct_research"
    else:
        return "respond"


async def respond(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a final response to the user's query based on the conducted research.

    This function formulates a comprehensive answer using the conversation history and the documents retrieved by the researcher.

    Args:
        state (AgentState): The current state of the agent, including retrieved documents and conversation history.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.response_model)
    context = format_docs(state.documents)
    prompt = configuration.response_system_prompt.format(context=context)
    messages = [{"role": "system", "content": prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


# Define the graph
builder = StateGraph(AgentState, input=InputState, config_schema=AgentConfiguration)
builder.add_node(analyze_and_route_query)
builder.add_node(ask_for_more_info)
builder.add_node(respond_to_general_query)
builder.add_node(conduct_research)
builder.add_node(create_research_plan)
builder.add_node(respond)

builder.add_edge(START, "analyze_and_route_query")
builder.add_conditional_edges("analyze_and_route_query", route_query)
builder.add_edge("create_research_plan", "conduct_research")
builder.add_conditional_edges("conduct_research", check_finished)
builder.add_edge("ask_for_more_info", END)
builder.add_edge("respond_to_general_query", END)
builder.add_edge("respond", END)

# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "RetrievalGraph"
```