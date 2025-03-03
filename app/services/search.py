# import pandas as pd
# from app.db.pinecone_db import index
# from app.services.embedding import get_embedding

# def ingest_data(csv_file: str):
#     df = pd.read_csv(csv_file)
#     vectors = []
#     for _, row in df.iterrows():
#         embedding = get_embedding(row["description"])
#         vectors.append((str(row["id"]), embedding, {"name": row["name"], "price": row["price"]}))
#     index.upsert(vectors)
