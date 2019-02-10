import networkx as nx
import networkx.algorithms.dag as dag

"""Graph representation of the state of Timeseries connection using networkx library"""


class TSGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def __len__(self):
        return len(self.graph)

    def inDegree(self):
        return self.graph.in_degree()

    def outDegree(self):
        return self.graph.out_degree()

    def size(self):
        return self.graph.size()

    def nodeView(self):
        return self.graph.nodes

    def edges(self):
        return self.graph.edges

    def adj(self):
        return self.graph.adj

    def addNode(self, ts):
        self.graph.add_node(ts)

        for publisher in ts.publishers:
            self.graph.add_edge(publisher, ts)

        self.graph.nodes[ts]['is_broadcasted'] = False

    def isDAG(self):
        return dag.is_directed_acyclic_graph(self.graph)

    def topological_sort(self):
        return dag.topological_sort(self.graph)

    def predecessors(self, ts):
        return list(self.graph.predecessors(ts))

    # consider caching the result for each TS, stored within each node
    def roots(self, ts):
        if 'root' not in self.graph[ts]:
            results = []
            preds = self.predecessors(ts)
            if not preds:
                return ts

            for predecessor in preds:
                recurse = self.roots(predecessor)
                # somehow does not work for direct object comparison
                if isinstance(recurse, list):
                    for source in recurse:
                        if id(source) not in [id(x) for x in results]:
                            results.append(source)
                elif id(recurse) not in [id(x) for x in results]:
                    results.append(recurse)

            self.graph.nodes[ts]['root'] = results
            return results
        else:
            return self.graph.nodes[ts]['root']

    def updateBroadcastStatus(self, ts):
        """ Update broadcast status of Timeseries after broadcasting """
        self.graph.nodes[ts]['is_broadcasted'] = True
