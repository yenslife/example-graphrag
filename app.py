from openai import OpenAI
import networkx as nx
from cdlib import algorithms
import os, time
from dotenv import load_dotenv
from constants import DOCUMENTS
from graph_vis import visualize_graph

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 日誌記錄函式
def log_output(message, log_file="log.txt"):
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


# 1. Source Documents → Text Chunks
def split_documents_into_chunks(documents, chunk_size=600, overlap_size=100):
    chunks = []
    for document in documents:
        for i in range(0, len(document), chunk_size - overlap_size):
            chunk = document[i:i + chunk_size]
            chunks.append(chunk)
    return chunks


# 2. Text Chunks → Element Instances
def extract_elements_from_chunks(chunks):
    elements = []
    for index, chunk in enumerate(chunks):
        log_output(f"Chunk index {index} of {len(chunks)}:")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract entities and relationships from the following text."},
                {"role": "user", "content": chunk}
            ]
        )
        log_output(response.choices[0].message.content)
        entities_and_relations = response.choices[0].message.content
        elements.append(entities_and_relations)
    return elements


# 3. Element Instances → Element Summaries
def summarize_elements(elements):
    summaries = []
    for index, element in enumerate(elements):
        log_output(f"Element index {index} of {len(elements)}:")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize the following entities and relationships in a structured format. Use \"->\" to represent relationships, after the \"Relationships:\" word."},
                {"role": "user", "content": element}
            ]
        )
        log_output("Element summary:", response.choices[0].message.content)
        summary = response.choices[0].message.content
        summaries.append(summary)
    return summaries


# 4. Element Summaries → Graph Communities
def build_graph_from_summaries(summaries):
    G = nx.Graph()
    for index, summary in enumerate(summaries):
        log_output(f"Summary index {index} of {len(summaries)}:")
        lines = summary.split("\n")
        entities_section = False
        relationships_section = False
        entities = []
        for line in lines:
            if line.startswith("### Entities:") or line.startswith("**Entities:**"):
                entities_section = True
                relationships_section = False
                continue
            elif line.startswith("### Relationships:") or line.startswith("**Relationships:**"):
                entities_section = False
                relationships_section = True
                continue
            if entities_section and line.strip():
                if line[0].isdigit() and line[1] == ".":
                    line = line.split(".", 1)[1].strip()
                entity = line.strip()
                entity = entity.replace("**", "")
                entities.append(entity)
                G.add_node(entity)
            elif relationships_section and line.strip():
                parts = line.split("->")
                if len(parts) >= 2:
                    source = parts[0].strip()
                    target = parts[-1].strip()
                    relation = " -> ".join(parts[1:-1]).strip()
                    G.add_edge(source, target, label=relation)
    return G


# 5. Graph Communities → Community Summaries
def detect_communities(graph):
    communities = []
    index = 0
    for component in nx.connected_components(graph):
        log_output(
            f"Component index {index} of {len(list(nx.connected_components(graph)))}:")
        subgraph = graph.subgraph(component)
        if len(subgraph.nodes) > 1:  # Leiden algorithm requires at least 2 nodes
            try:
                sub_communities = algorithms.leiden(subgraph)
                for community in sub_communities.communities:
                    communities.append(list(community))
            except Exception as e:
                log_output(f"Error processing community {index}: {e}")
        else:
            communities.append(list(subgraph.nodes))
        index += 1
    log_output("Communities from detect_communities:", communities)
    return communities


def summarize_communities(communities, graph):
    community_summaries = []
    for index, community in enumerate(communities):
        log_output(f"Summarize Community index {index} of {len(communities)}:")
        subgraph = graph.subgraph(community)
        nodes = list(subgraph.nodes)
        edges = list(subgraph.edges(data=True))
        description = "Entities: " + ", ".join(nodes) + "\nRelationships: "
        relationships = []
        for edge in edges:
            relationships.append(
                f"{edge[0]} -> {edge[2]['label']} -> {edge[1]}")
        description += ", ".join(relationships)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize the following community of entities and relationships."},
                {"role": "user", "content": description}
            ]
        )
        summary = response.choices[0].message.content.strip()
        community_summaries.append(summary)
    return community_summaries


# 6. Community Summaries → Community Answers → Global Answer
def generate_answers_from_communities(community_summaries, query):
    intermediate_answers = []
    for index, summary in enumerate(community_summaries):
        log_output(f"Summary index {index} of {len(community_summaries)}:")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Answer the following query based on the provided summary."},
                {"role": "user", "content": f"Query: {query} Summary: {summary}"}
            ]
        )
        log_output("Intermediate answer:", response.choices[0].message.content)
        intermediate_answers.append(
            response.choices[0].message.content)

    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
                "content": "Combine these answers into a final, concise response."},
            {"role": "user", "content": f"Intermediate answers: {intermediate_answers}"}
        ]
    )
    final_answer = final_response.choices[0].message.content
    return final_answer


# Putting It All Together
def graph_rag_pipeline(documents, query, chunk_size=600, overlap_size=100):
    # Step 1: Split documents into chunks
    chunks = split_documents_into_chunks(
        documents, chunk_size, overlap_size)

    # Step 2: Extract elements from chunks
    elements = extract_elements_from_chunks(chunks)

    # Step 3: Summarize elements
    summaries = summarize_elements(elements)

    # Step 4: Build graph and detect communities
    graph = build_graph_from_summaries(summaries)
    communities = detect_communities(graph)

    log_output("communities:", communities[0])
    # Step 5: Summarize communities
    community_summaries = summarize_communities(communities, graph)

    # Step 6: Generate answers from community summaries
    final_answer = generate_answers_from_communities(
        community_summaries, query)

    return final_answer, graph

if __name__ == "__main__":
    # Example usage
    query = "二階選課抽籤完，三階還可以抽籤嗎？"
    log_output('Query:', query)
    total_time = 0
    current_time = time.time()
    answer, graph = graph_rag_pipeline(DOCUMENTS, query)
    total_time += time.time() - current_time
    log_output('Total time:', total_time)
    log_output('Answer:', answer)
    visualize_graph(graph)

