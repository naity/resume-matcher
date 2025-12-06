import streamlit as st
import requests
import json
import sseclient

st.set_page_config(page_title="Agentic Resume Matcher", page_icon=":page_facing_up:")

st.title(":page_facing_up: Agentic Resume Matcher")
st.markdown("Upload your resume and let our **AI Career Coach** find the best jobs for you.")

# Resume Input
uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])

if st.button("Find Matching Jobs", type="primary"):
    if not uploaded_file:
        st.warning("Please upload your resume first.")
    else:
        st.info("Contacting Career Coach...")
        
        # Container for status updates
        status_container = st.empty()
        results_container = st.container()
        
        try:
            # Connect to the streaming endpoint
            # We need to send the file as multipart/form-data
            files = {"resume": ("resume.pdf", uploaded_file, "application/pdf")}
            response = requests.post(
                "http://localhost:8000/find_jobs",
                files=files,
                stream=True
            )
            response.raise_for_status()
            
            client = sseclient.SSEClient(response)
            
            final_json = None
            
            for event in client.events():
                if event.data:
                    try:
                        data = json.loads(event.data)
                        msg_type = data.get("type")
                        content = data.get("content")
                        
                        if msg_type == "status":
                            status_container.status(content, state="running")
                        
                        elif msg_type == "result":
                            # We got the final JSON result
                            final_json = content
                            status_container.status("Analysis Complete!", state="complete")
                            
                        elif msg_type == "done":
                            break
                            
                    except json.JSONDecodeError:
                        pass
            
            # Render Results
            if final_json:
                try:
                    # It might be a string representation of the JSON or the JSON object itself
                    if isinstance(final_json, str):
                        # Clean up any markdown code blocks if present
                        final_json = final_json.replace("```json", "").replace("```", "").strip()
                        matches = json.loads(final_json)
                    else:
                        matches = final_json
                        
                    # Handle the specific MatchResponse structure if needed
                    # If matches is a dict with "matches" key
                    if isinstance(matches, dict) and "matches" in matches:
                        matches = matches["matches"]
                        
                    st.success(f"Found Top {len(matches)} matches!")
                    
                    for job in matches:
                        with st.expander(f"{job.get('job_title', 'Job')} - Score: {job.get('match_score', 0)}/100"):
                            st.markdown(f"**[Apply Here]({job.get('job_url', '#')})**")
                            st.markdown(f"**Reasoning:** {job.get('reasoning')}")
                            st.markdown(f"**Strengths:** {', '.join(job.get('strengths', []))}")
                            st.markdown(f"**Missing Skills:** {', '.join(job.get('missing_skills', []))}")
                            st.info(f"💡 **Tip:** {job.get('improvement_tips')}")
                            
                except Exception as e:
                    st.error(f"Error parsing results: {e}")
                    st.code(final_json)
                    
        except Exception as e:
            st.error(f"Connection Error: {e}")
