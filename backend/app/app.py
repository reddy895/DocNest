import streamlit as st

from backend.app.services.document_processor import extract_text, split_into_chunks
from backend.app.services.vector_store import add_document, search_documents, collection
from backend.app.services.ollama_client import generate_answer
st.set_page_config(page_title="College RAG Assistant", page_icon="📚")
st.title("📚 College Document AI Assistant")
st.write("Upload documents and ask questions using Retrieval Augmented Generation.")

# -------------------------------
# DOCUMENT UPLOAD
# -------------------------------
st.header("1. Upload Documents")
files = st.file_uploader("Select PDF documents", type=["pdf"], accept_multiple_files=True)
if st.button("Process Documents"):
	if not files:
		st.warning("Please upload a PDF.")
	else:
		for file in files:
			with st.spinner(f"Processing {file.name}..."):
				pages = extract_text(file)
				total_chunks = 0
				for page in pages:
					chunks = split_into_chunks(page["text"])
					# Include page number in the stored source identity.
					for index, chunk in enumerate(chunks):
						add_document(f"{file.name}_page_{page['page']}_{index}", [chunk])
						total_chunks += 1
				st.success(f"{file.name}: {total_chunks} chunks indexed.")

# -------------------------------
# KNOWLEDGE BASE STATUS
# -------------------------------
st.header("2. Knowledge Base")
st.metric("Total indexed chunks", collection.count())

# -------------------------------
# QUESTION ANSWERING
# -------------------------------
st.header("3. Ask Your Question")
question = st.text_input("Enter your question")
top_k = st.slider("Number of retrieved chunks", 1, 8, 4)
if st.button("Generate Answer"):
	if not question.strip():
		st.warning("Enter a question.")
	elif collection.count() == 0:
		st.warning("Please upload and process documents first.")
	else:
		with st.spinner("Searching documents..."):
			results = search_documents(question, top_k)
			documents = results["documents"][0]
			metadatas = results["metadatas"][0]
			context = ""
			for i, document in enumerate(documents):
				source = metadatas[i]["source"]
				context += f"\n[Source {i + 1}: {source}]\n{document}\n"

		prompt = f"""You are a document-based AI assistant. Answer the question using ONLY the provided context. If the answer is not available in the context, say that you could not find the information in the documents. Do not invent information. Cite the source numbers in your answer.
CONTEXT: {context}

QUESTION: {question}
ANSWER:
"""
		with st.spinner("Generating answer using Llama..."):
			answer = generate_answer(prompt)
		st.subheader("AI Generated Answer")
		st.write(answer)
		with st.expander("View Retrieved Documents"):
			for i, document in enumerate(documents):
				st.markdown(f"**Source {i + 1}**")
				st.write(document)
				st.divider()

