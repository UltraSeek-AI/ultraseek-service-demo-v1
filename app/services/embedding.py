# from app.core.config import GEMINI_API_KEY
# from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# import google.generativeai as genai
# from langchain.chains.question_answering import load_qa_chain
# from langchain.prompts import PromptTemplate
# from dotenv import load_dotenv
# import os

# load_dotenv()

# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# # Khởi tạo Google Gemini Embeddings với API Key
# # embedding_model = GoogleGenerativeAIEmbeddings(
# #     model="models/text-embedding-004",
# # )

# def get_embedding(text: str):
#     """
#     Hàm tạo embedding từ văn bản đầu vào bằng Google Gemini API.
#     """
#     embeddings=GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
#     return embeddings.embed(text)
