import uvicorn
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from src.agent import get_agent
from src.models import MatchResponse

app = FastAPI(title="Agentic Resume Matcher")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import base64

@app.post("/find_jobs")
async def find_jobs(resume: UploadFile = File(...)):
    """
    Streams the agent's execution steps and final result.
    """
    # Read and encode the PDF
    content = await resume.read()
    base64_pdf = base64.b64encode(content).decode("utf-8")

    async def event_generator():
        agent = get_agent()
        print("🚀 Starting Agent Stream...")
        
        # Construct Multimodal Message
        msg_content = [
            {"type": "text", "text": "Here is my resume. Please analyze it and find the best jobs for me."},
            {
                "type": "file",
                "base64": base64_pdf,
                "mime_type": "application/pdf",
                "filename": resume.filename,
            }
        ]

        # Stream the agent's execution
        async for chunk in agent.astream(
            {"messages": [{"role": "user", "content": msg_content}]},
            stream_mode="values"
        ):
            # Check the latest message in the conversation
            if "messages" in chunk:
                latest_message = chunk["messages"][-1]
                
                # 1. Tool Calls (Agent decides to search)
                if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
                    for tool_call in latest_message.tool_calls:
                        # Notify UI that we are searching
                        yield f"data: {json.dumps({'type': 'status', 'content': f'🔍 Searching jobs...'})}\n\n"
                
                # 2. Tool Output (Observation)
                elif latest_message.type == "tool":
                    yield f"data: {json.dumps({'type': 'status', 'content': '✅ Found jobs, analyzing...'})}\n\n"

                # 3. Final Answer (AI Message with structured output)
                elif latest_message.type == "ai" and latest_message.content:
                    # In some cases, the content might be the JSON string if ProviderStrategy didn't intercept it yet,
                    # or it might be empty if the result is in a different key.
                    # For this demo, let's try to yield the content if it looks like JSON.
                    content = latest_message.content
                    if content.strip().startswith("{") or content.strip().startswith("["):
                         yield f"data: {json.dumps({'type': 'result', 'content': content})}\n\n"
        
        # End of stream
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
