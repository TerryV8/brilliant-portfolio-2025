from typing import TypedDict, Annotated, Optional, AsyncGenerator
from fastapi import FastAPI, Query
import logging
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.graph import add_messages, StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.memory import MemorySaver
from uuid import uuid4
import json

load_dotenv()

model = ChatOpenAI(model_name="gpt-4o", temperature=0)

search_tool = TavilySearchResults(max_results=4)
tools = [search_tool]
memory = MemorySaver()
llm_with_tools = model.bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list, add_messages]


async def model(state: State) -> AIMessage:
    result = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [result]}


async def tools_router(state: State) -> ToolMessage:
    last_message = state["messages"][-1]

    if (hasattr(last_message, "tool_calls")) and len(last_message.tool_calls) > 0:
        return "tool_node"
    else:
        return END


async def tool_node(state: State) -> ToolMessage:
    # Get tool calls from last message
    tool_calls = state["messages"][-1].tool_calls

    # Initialize list to store messages
    tool_messages = []

    # Process each tool call
    for tool_call in tool_calls:
        # Get tool name and arguments
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        # handle the search tool
        if tool_name == "tavily_search_results_json":
            # Execute the search tool with the provided arguments
            search_results = await search_tool.ainvoke(tool_args)

            # Format search results in a more readable way for the AI
            formatted_results = []

            # Handle different formats of search results
            results = search_results
            if isinstance(search_results, dict) and "results" in search_results:
                results = search_results["results"]

            if isinstance(results, list):
                for i, result in enumerate(results[:5]):  # Limit to top 5 results
                    title = result.get("title", "No title")
                    url = result.get("url", result.get("link", "#"))
                    snippet = result.get("content", "")

                    # Truncate snippet if too long
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."

                    formatted_results.append(
                        f"{i + 1}. {title}\n   URL: {url}\n   {snippet}\n"
                    )

            # Create a well-formatted message with the search results
            search_context = (
                "I found these search results:\n\n" + "\n".join(formatted_results)
                if formatted_results
                else "No relevant search results found."
            )

            # Create tool message with the formatted results
            tool_message = ToolMessage(
                content=search_context,
                tool_call_id=tool_id,
                name=tool_name,
            )

            tool_messages.append(tool_message)

    # Add the tool messages to the state
    return {"messages": tool_messages}


# Update the graph construction
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("model", model)
graph_builder.add_node("tool_node", tool_node)

# Set entry point
graph_builder.set_entry_point("model")

# Add conditional edges
graph_builder.add_conditional_edges(
    "model", tools_router, {"tool_node": "tool_node", END: END}
)

# Add edge from tool_node back to model
graph_builder.add_edge("tool_node", "model")

# Compile the graph
graph = graph_builder.compile(checkpointer=memory)

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS middleware with settings that match frontend requirements
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)


def serialize_ai_message_chunk(chunk):
    if not isinstance(chunk, AIMessageChunk):
        raise TypeError(
            f"Object of type {type(chunk).__name__} is not an AIMessageChunk"
        )

    # Return empty string for empty content to avoid serialization issues
    if not chunk.content:
        return ""

    # If content is a list, join the elements
    if isinstance(chunk.content, list):
        return "".join(str(part) for part in chunk.content if part)

    return str(chunk.content)


async def generate_chat_responses(
    message: str, checkpoint_id: Optional[str] = None
) -> AsyncGenerator[dict, None]:
    # Add your chat generation logic here
    # This is a placeholder - implement according to your needs
    # yield {"content": "This is a placeholder response. Implement chat generation logic here."}

    is_new_conversation = checkpoint_id is None

    if is_new_conversation:
        # Generate a new checkpoint ID for first message in conversation
        new_checkpoint_id = str(uuid4())

        config = {"configurable": {"thread_id": new_checkpoint_id}}

        # Initialize graph with first message
        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]}, version="v2", config=config
        )

        # First send the checkpoint ID
        yield f"data: {json.dumps({'type': 'checkpoint', 'checkpoint_id': new_checkpoint_id})}\n\n"

    else:
        config = {"configurable": {"thread_id": checkpoint_id}}

        events = graph.astream_events(
            {"messages": [HumanMessage(content=message)]}, version="v2", config=config
        )

    # Buffer to accumulate content between spaces
    content_buffer = []

    async for event in events:
        event_type = event["event"]
        if event_type == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if not chunk or not chunk.content:
                continue

            chunk_content = serialize_ai_message_chunk(chunk)
            if not chunk_content:  # Skip empty chunks
                continue

            # Add to buffer
            content_buffer.append(chunk_content)

            # If we have a space or punctuation, flush the buffer
            if any(c.isspace() or c in ".,!?;:" for c in chunk_content):
                if content_buffer:
                    # Join buffer and clean up
                    combined = "".join(content_buffer).strip()
                    if combined:  # Only yield if we have content
                        response = {"type": "content", "content": combined}
                        yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                    content_buffer = []

        # Handle chat model end event
        elif event_type == "on_chat_model_end":
            # First, flush any remaining content in buffer
            if content_buffer:
                combined = "".join(content_buffer).strip()
                if combined:
                    response = {"type": "content", "content": combined}
                    yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                content_buffer = []

            # Then handle tool calls for search
            output = event["data"]["output"]
            # Check if there are tool calls for search
            output = event["data"]["output"]
            tool_calls = []
            if hasattr(output, "tool_calls"):
                tool_calls = output.tool_calls
            elif hasattr(output, "tool_calls_dict"):
                tool_calls = output.tool_calls_dict

            search_calls = [
                call
                for call in tool_calls
                if isinstance(call, dict)
                and call.get("name") == "tavily_search_results_json"
                or hasattr(call, "name")
                and call.name == "tavily_search_results_json"
            ]

            if search_calls:
                # Signal that a search is starting
                search_call = search_calls[0]
                if isinstance(search_call, dict):
                    args = search_call.get("args", {})
                    search_query = (
                        args.get("query", "") if isinstance(args, dict) else ""
                    )
                else:
                    args = getattr(search_call, "args", {})
                    search_query = (
                        getattr(args, "query", "") if hasattr(args, "query") else ""
                    )

                # Escape quotes and special characters
                safe_query = str(search_query).replace("'", "\\'").replace("\n", "\\n")

                yield f"data: {json.dumps({'type': 'search_start', 'query': safe_query})}\n\n"

        # Handle tool end events for search
        elif (
            event_type == "on_tool_end"
            and event["name"] == "tavily_search_results_json"
        ):
            # Search completed - send results or error
            output = event["data"].get("output", [])

            # Extract URLs from the output
            urls = []

            # Handle string output (might be JSON string)
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except json.JSONDecodeError:
                    print("Failed to parse search output as JSON")

            # Handle list output
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict):
                        if "url" in item:
                            urls.append(item["url"])
                        elif "link" in item:  # Some APIs use 'link' instead of 'url'
                            urls.append(item["link"])
            # Handle dictionary output
            elif isinstance(output, dict):
                if "results" in output:
                    results = output["results"]
                    if isinstance(results, list):
                        for item in results:
                            if isinstance(item, dict):
                                if "url" in item:
                                    urls.append(item["url"])
                                elif "link" in item:
                                    urls.append(item["link"])
                # Check for direct URLs in the output
                elif "url" in output:
                    urls.append(output["url"])
                elif "link" in output:
                    urls.append(output["link"])

            # Log the extracted URLs for debugging
            print(f"Extracted URLs: {urls}")

            # Send the search results if we have any
            if urls:
                response = {"type": "search_result", "urls": urls}
                print(f"Sending search result: {response}")
                yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
            else:
                print("No URLs found in search results")

    # Send an end event when done
    yield f"data: {json.dumps({'type': 'end'})}\n\n"


@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    print(f"Received request - message: {message}, checkpoint_id: {checkpoint_id}")
    try:
        return StreamingResponse(
            generate_chat_responses(message, checkpoint_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering for nginx
            },
        )
    except Exception as e:
        print(f"Error in chat_stream: {str(e)}")
        return {"error": str(e)}


# SSE - server-sent events
