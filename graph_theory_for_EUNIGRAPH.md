# Essential Graph Theory for EuniGraph

## Definition of a graph
A **graph** is a structure composed of a set of **nodes** and a set of **edges** that connect pairs of nodes. In simple terms, a graph is used to represent entities and relationships between entities.

### Meaning in the project
In EuniGraph:
- in the **co-authorship graph**, the entities are researchers and the relationships are the co-signing of publications
- in the **semantic graph**, the entities are publications and the relationships are the proximities between embeddings or similarity scores

---

#### Meaning of Embedding 
_An **embedding** is a numerical representation of content, for example a text, in the form of a vector. The idea is to transform textual content into a mathematical form that makes it possible to compare it with other content: semantically similar texts will have embeddings that are close in vector space. In EuniGraph, embeddings are used to compare publications based on their content and to build the **semantic graph**, in which similar articles are connected to each other._

---


## Nodes
**Nodes** are the vertices of the graph, that is, the objects we want to represent.

### Meaning in the project
- in the **co-authorship graph**, a node corresponds to an **author / researcher**
- in the **semantic graph**, a node corresponds to a **publication**



## Edges
**Edges** are the connections between nodes.

### Meaning in the project
- in the **co-authorship graph**, an edge connects two researchers who have written at least one publication together
- in the **semantic graph**, an edge connects two publications that are semantically close according to the embedding / similarity system

## Directed and undirected graph
A graph can be:

- **directed**, if the edges have a direction
- **undirected**, if the edges have no direction

In network analysis libraries this distinction is fundamental because many metrics depend on whether an edge is oriented or not.

### Meaning in the project
For EuniGraph, as a first approximation:

- the **co-authorship graph** is naturally **undirected**, because the collaboration between A and B is valid in both directions
- the **semantic graph** is also normally treated as **undirected** if the similarity between two articles is made symmetric in the final layer

## Edge weight
An edge can have a **weight**, that is, a numerical value that measures the intensity of the relationship.

### Meaning in the project
In the project the weight of the edges has a very concrete meaning:

- in the **co-authorship graph**, the weight represents the **number of shared publications** between two authors
- in the **semantic graph**, the weight represents the **similarity score** between two publications

Weight is important because many metrics can be calculated both in an unweighted and in a weighted version.

## Degree
The **degree** of a node is the number of edges incident to that node. In an unweighted graph it therefore indicates how many other nodes that node is directly connected to.

### Meaning in the project
In the **co-authorship graph**, the degree of an author indicates how many distinct co-authors they have collaborated with.

Useful interpretation:
- high degree = researcher with many direct collaborations
- low degree = more peripheral researcher or one specialized in a few ties

In the **semantic graph**, the degree of a publication indicates how many other publications it is directly connected to in the similarity layer.

Useful interpretation:
- high degree = article semantically close to many others
- low degree = more isolated or specialized article

## Betweenness
**Betweenness centrality** measures how often a node lies along the shortest paths between other pairs of nodes. In other words, it measures how much a node acts as a bridge in the network. 

### Meaning in the project
In the **co-authorship graph**, a high betweenness can indicate:
- researchers who connect different groups
- bridge authors between universities or distinct research clusters
- figures who facilitate the circulation of collaboration in the network

In the **semantic graph**, a high betweenness can indicate:
- publications that connect different topics
- “bridge” articles between related but non-overlapping research areas
- interdisciplinary or cross-cutting works

This measure is particularly interesting for EUNICE because it can help identify:
- collaborations between different universities
- nodes that promote integration between research communities
- points of connection between different scientific strands

## Strength
The **strength** of a node is its **weighted degree**, that is, the sum of the weights of the edges incident to it.

### Meaning in the project
In the **co-authorship graph**, the strength of an author can be interpreted as the **overall strength of their collaborations**.

Example:
- an author with few co-authors but many shared publications with them can have moderate degree but high strength
- an author with many occasional co-authors can have high degree but not necessarily very high strength

In the **semantic graph**, the strength of a publication measures the **overall sum of its semantic proximities** with other articles.

Useful interpretation:
- high strength = article that is very well connected semantically
- low strength = article that has few strong connections or only weak connections

## Practical difference between degree and strength
This distinction is very important in the project:

- **degree** counts **how many** connections exist
- **strength** measures **how strong** those connections are

### In the co-authorship graph
- degree = how many distinct co-authors
- strength = how intense the overall collaboration has been

### In the semantic graph
- degree = how many nearby articles
- strength = how strong the overall similarity with the neighbors is

## What the co-authorship graph is used for in the EUNICE context
Co-authorship network analysis is a well-established technique for studying scientific collaboration. The literature shows that co-authorship networks are useful for evaluating collaborations, the structure of the scientific community, integration between groups, and opportunities for developing new connections. 
In the EUNICE context, the co-authorship graph can be useful for:

- seeing **who collaborates with whom**
- understanding whether there are **intra-university** or **inter-university** collaborations
- identifying **central**, **bridging**, or **isolated** researchers
- identifying already consolidated research clusters
- observing how integrated or fragmented the EUNICE network is
- supporting cooperation strategies among the universities of the alliance

In summary, the co-authorship graph serves to represent the **social and collaborative structure** of research in EUNICE.

## What the semantic graph is used for in the EUNICE context
The semantic graph does not look directly at people, but at **scientific content**.

In the project, the semantic graph makes it possible to:
- connect publications that deal with similar topics
- bring out research strands even when direct co-authorship does not yet exist
- identify thematic clusters
- find proximities between works produced in different universities
- suggest potential areas of future collaboration

In the EUNICE context, this is useful because it makes it possible to see not only collaboration that has **already taken place**, but also the **potential scientific proximity** between research groups.

### Complementary reading of the two graphs
The combination of the two layers is very powerful:

- **co-authorship graph** = shows the real collaboration that already exists
- **semantic graph** = shows the thematic proximity between works and research lines

## How to read the two graphs together
In the project, the combined use of the two graphs can support questions such as:

- which researchers already collaborate within EUNICE?
- which universities are more connected in terms of co-authorship?
- which publications are semantically close even if they were produced by groups not yet socially connected?
- are there common research areas between universities that do not yet collaborate directly?
- which authors or which articles act as bridges between different clusters?

## Final summary
In the context of EuniGraph:

- a **graph** represents entities and relationships
- **nodes** are researchers or publications
- **edges** represent collaborations or similarities
- **weight** measures the intensity of the relationship
- **degree** measures how many direct connections a node has
- **betweenness** measures how much a node acts as a bridge
- **strength** measures the overall strength of weighted connections

These measures serve to transform a set of metadata and relationships into a readable and analyzable representation of EUNICE research, both from the point of view of actual collaborations and from the point of view of thematic proximities.