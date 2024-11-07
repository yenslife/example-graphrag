import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
import networkx as nx

def tw_font():
    font = 'Microsoft JhengHei' # 如果是 Windows 的電腦才可以用

    for i in sorted(fontManager.get_font_names()):
        if 'Heiti' in i: # Mac 的繁體中文
            font = i
            break
        if 'PingFang' in i:
            font = i
            break

    matplotlib.rc('font', family=font)
    plt.pie(
        [800, 300, 400],
        labels=['交通', '住宿', '餐飲'],
        autopct='%1.1f%%'
    )
    plt.show()

    return font

def visualize_graph(G: nx.Graph):
    font = tw_font()
    matplotlib.rc('font', family=font)
    # Set up the figure and axis
    plt.figure(figsize=(12, 10))  # Increase the figure size if needed

    # Adjust node spacing by setting the 'k' parameter in spring_layout
    pos = nx.spring_layout(
        G, k=0.9
    )  # Increase 'k' to control the spacing between nodes (default is 0.1)

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=1000)

    # Draw the edges
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), width=2)

    # Draw the labels for the nodes
    nx.draw_networkx_labels(G, pos, font_size=6, font_family="sans-serif")

    # Get edge labels from the graph and draw them
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")

    # Display the graph
    plt.title("Knowledge Graph Visualization")
    plt.axis("off")  # Hide the axis
    plt.show()

if __name__ == '__main__':
    tw_font()
