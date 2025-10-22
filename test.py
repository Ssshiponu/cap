from google import genai
from google.genai import types
import chromadb
from dotenv import load_dotenv
import os

load_dotenv()

# client = genai.Client()
db = chromadb.PersistentClient(path="./chorma")
collection = db.get_or_create_collection(name="technova")

texts = [
    # 🧠 General Brand Info
    "TechNova is a global technology company that designs innovative smart devices and software solutions.",
    "Founded in 2012, TechNova focuses on making technology accessible and sustainable for everyone.",
    "TechNova's slogan is 'Innovation for Every Life', emphasizing inclusivity and modern living.",

    # 📱 Products
    "The NovaPhone X is TechNova's flagship smartphone, known for its AI-powered camera and ultra-fast charging.",
    "NovaWatch integrates health tracking and fitness analytics into a minimalist wearable device.",
    "NovaPad is a lightweight tablet optimized for students and professionals with long battery life.",
    "TechNova also produces home automation products under the NovaHome brand.",

    # 🧑‍💻 Software Ecosystem
    "NovaOS is TechNova's operating system that connects all Nova devices seamlessly.",
    "The NovaCloud service offers 1TB of free storage for all registered users.",
    "Developers can build apps for NovaOS using the NovaSDK toolkit.",
    "TechNova's voice assistant, NovaAI, supports over 50 languages.",

    # 🌱 Sustainability & Social
    "TechNova runs a recycling program that allows customers to return old devices for credit.",
    "The company uses renewable energy in 70% of its manufacturing facilities.",
    "TechNova partners with global NGOs to provide digital education in underprivileged areas.",

    # 💬 Customer Experience
    "TechNova’s customer support is available 24/7 via chat, email, and phone.",
    "Users love TechNova products for their reliability and smooth performance.",
    "The company has a loyalty program called NovaPlus that rewards frequent buyers.",

    # 💼 Business and Market
    "TechNova operates in over 40 countries and has headquarters in Singapore.",
    "The brand's revenue grew 25% in 2024 thanks to the success of NovaPhone X.",
    "TechNova competes with brands like Apple, Samsung, and Xiaomi in the global tech market.",

    # 🚀 Future Plans
    "TechNova plans to launch an electric scooter line in 2026 under the NovaMove brand.",
    "The company is also researching augmented reality glasses for next-generation connectivity."
]


# def embed(texts: list[str]):
#     """
#     Returns a list of embedding vectors for the given text list.
#     """
#     # The API expects a list of contents
#     result = client.models.embed_content(
#         model="gemini-embedding-001",
#         contents=texts
#     )

#     # Handle structure differences (depending on SDK version)
#     embeddings = [embedding.values for embedding in result.embeddings]
#     return embeddings


# --- Store in Chroma ---
# collection.add(
#     ids=[str(i) for i in range(len(texts))],
#     documents=texts,
#     # embeddings=embed(texts),
# )

# --- Query ---
query_text = ["what they do for enviroments? "]
# query_embeddings = embed(query_text)

result = collection.query(
    # query_embeddings=query_embeddings,
    query_texts=query_text,
    n_results=2,
    include=["documents", "distances"]
)

# --- Display result ---
print("\nQuery:", query_text[0])
for doc_id, doc, dist in zip(result["ids"][0], result["documents"][0], result["distances"][0]):
    print(f"\n→ ID: {doc_id}")
    print(f"Distance: {dist:.4f}")
    print(f"Document: {doc}")
