import streamlit as st
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from prompts.cypher_prompt import create_prompt
from prompts.stakeholder_prompt import create_qa_prompt
from langchain_community.llms import Ollama
import openai
import json
from datetime import datetime
import os
from pathlib import Path

st.set_page_config(page_title="GraphRAG Dialogue Insights", layout="wide")
st.title("GraphRAG Dialogue Insights")
stakeholder_name = st.sidebar.selectbox("Stakeholder Prompt",
                                        ["software_engineer", "service_coordinator", "product_owner"])
select_model = st.sidebar.selectbox("Choose Model", ["Llama3.1", "GPT-4.0"])

with st.expander("📌 Cheat Sheet", expanded=True):
    st.markdown("""
    **Example Questions:**
    1. `Which microservices have an external dependency?`
    2. `I want to fix a bug in [REPLACE WITH SERVICE NAME]. What are its dependencies?`
    3. `Which tasks are most similar based on their descriptions and the microservices they are linked to?`
    4. `I found a bug in [REPLACE WITH SERVICE NAME], which uses [REPLACE WITH TECHNOLOGY]. Which team members are familiar with this technology and should be contacted?`
    5. `Which team members are working on [REPLACE WITH SERVICE NAME]?`

    **Guidelines:**
    - Keep questions relevant to the data and avoid unnecessary words.
    - Write clear instructions, and include entity or edge properties (e.g., `Task` with `name`).
    - Use proper capitalization for entity and edge names (e.g., `Microservice`, `DEPENDS_ON`).
    - If you are asking questions in a language other than English, keep entity, edge names, and properties in English.
    """)

enhanced_graph = Neo4jGraph(
    url="neo4j://127.0.0.1:7687",
    username="neo4j",
    password="password",
    enhanced_schema=True
)


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


cypher_prompt_ = create_prompt()
qa_prompt_ = create_qa_prompt(stakeholder_name=stakeholder_name)


def chat_bot_invoke(chain):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.write("### Chat History")
    for message in st.session_state.chat_history:
        if message["role"] == "User":
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**GDI:** {message['content']}")

    st.markdown("""
        <style>
            .stTextInput {
                display: flex;
            }
            div[data-testid="InputInstructions"] > span:nth-child(1) {
                visibility: hidden;
            }
        </style>
    """, unsafe_allow_html=True)

    st.write("Please type your question about the data and click 'Send' to get an answer.")
    col1, col2 = st.columns([1, 0.15])

    with col1:
        user_input = st.text_input("", placeholder="e.g., I want to fix a bug in [REPLACE WITH SERVICE NAME]. What are its dependencies?")
        # To reproduce the results from the user-centered validation sessions (onboarding use case), refer to "5. Steps to Reproduce" section in the README file. 
        # 1) Comment lines 77 and 78, 2) Comment out line 81-88, and added the extracted questions in the `user_inputs` array 3) comment out line 95, and 4) run `streamlit run GDI.py` and press the "Send" button.
        # user_inputs = 
        # [
        #     "Is there a relationship between UserService and CatalogService",
        #     "Which team member is working on which project.",
        #     "Which team memembers are working on RecommendationService?",
        #     "Which Persons are working on RecommendationService?",
        #     "Which services Diana is working on?"
        # ] 

        responses = []

    with col2:
        if st.button("Send"):
            # Comment out line 95 to loop through the questions provided in the `user_inputs` array.
            # for user_input in user_inputs:
            st.session_state.chat_history.append({"role": "User", "content": user_input})
            with col1:
                with st.spinner("Processing..."):
                    try:
                        result = chain.invoke({"query": user_input})
                        bot_response = str(result["result"]) + str(result["intermediate_steps"])

                        intermediate_steps = result.get("intermediate_steps", [])
                        query = intermediate_steps[0].get("query") if intermediate_steps else "No query found"
                        context = intermediate_steps[1].get("context") if intermediate_steps else "No context available"

                        st.write(f"**Response:** {result['result']}")
                        st.markdown("""
                                <style>
                                    .stCodeBlock > div {
                                        max-width: 100% !important;
                                    }
                                    
                                    .language-cypher {
                                        white-space: pre-wrap !important;
                                        word-break: break-word !important;
                                    }
                                </style>
                            """, unsafe_allow_html=True)

                        st.write("**Corresponding Neo4j Query:**")
                        st.code(query, language="cypher")
                        with st.expander("**Context:**", expanded=False):
                            st.write(context)
                        responses.append(result)

                        st.session_state.chat_history.append({
                            "role": "GDI",
                            "content": str(result["result"]),
                            "query": query,
                            "context": context
                        })
                    except Exception as e:
                        bot_response = f"An error occurred: {e}"
                        st.session_state.chat_history.append({"role": "GDI", "content": bot_response})

    if st.button("Save Session"):
        timestamp = get_timestamp()
        folder_path = Path('../supplementary-materials/saved-logs')
        file_path = os.path.join(folder_path, f"graphrag_dialogue_insights_{timestamp}.json")
        os.makedirs(folder_path, exist_ok=True)

        with open(file_path, 'w') as json_file:
            json.dump(st.session_state.chat_history, json_file, indent=4)
        st.success(f"Chat History Saved: {file_path}")


if select_model == "GPT-4.0":
    user_openai_api_key = st.sidebar.text_input("Enter Open AI key", "", type="password")

    if user_openai_api_key:
        openai.api_key = user_openai_api_key
        st.warning("OpenAI Key present")

        openai_chain = GraphCypherQAChain.from_llm(
            ChatOpenAI(temperature=0, openai_api_key=user_openai_api_key),
            graph=enhanced_graph,
            verbose=True,
            cypher_prompt=cypher_prompt_,
            qa_prompt=qa_prompt_,
            validate_cypher=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True
        )
        chat_bot_invoke(chain=openai_chain)

    else:
        st.warning("Please enter OpenAI API Key to continue")


elif select_model == "Llama3.1":
    llama_chain = GraphCypherQAChain.from_llm(
        graph=enhanced_graph,
        llm=Ollama(model="Llama3.1", temperature=0),
        cypher_prompt=cypher_prompt_,
        qa_prompt=qa_prompt_,
        validate_cypher=True,
        return_intermediate_steps=True,
        allow_dangerous_requests=True
    )
    chat_bot_invoke(chain=llama_chain)
    
