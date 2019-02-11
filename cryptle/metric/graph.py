import networkx as nx
import networkx.algorithms.dag as dag
import networkx.algorithms.traversal.depth_first_search as dfs

"""Graph representation of the state of Timeseries connection using networkx library"""


class TSGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def __len__(self):
        return len(self.graph)

    def inDegree(self, *args):
        return self.graph.in_degree(*args)

    def outDegree(self, *args):
        return self.graph.out_degree(*args)

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

    def attr(self, ts, attr):
        return self.graph.nodes[ts][attr]

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
        """Update broadcast status of Timeseries after broadcasting."""
        # print(f'\nUpdating {repr(ts)}...')
        self.graph.nodes[ts]['is_broadcasted'] = True
        # some sort of differentiation between the nodes

        # all source TS (i.e. open_buffer, timestamp etc.) has no incoming edges
        if self.inDegree(ts) == 0:
            # print(f'this is a source {repr(ts)}')
            # recursively search all successors, mark them as not broadcasted
            # print(self.dfsSuccessors(ts))
            for _, successors in self.dfsSuccessors(ts).items():
                for successor in successors:
                    self.graph.nodes[successor]['is_broadcasted'] = False

        # for node in self.graph:
        #     print(repr(node), self.graph.nodes[node])

    def checkResetCondition(self):
        finished = all(
            [
                self.graph.nodes[node]['is_broadcasted'] == True
                for node in self.sources()
            ]
        )
        if finished:
            self.resetBrodcastStatus()
        else:
            pass
            # print(repr(ts), 'not finished')

    def resetBrodcastStatus(self):
        for node in self.graph:
            self.graph.nodes[node]['is_broadcasted'] = False

    def dfsSuccessors(self, ts):
        return dfs.dfs_successors(self.graph, ts)

    # caching is important
    def sources(self):
        if 'sources' not in self.graph.graph:
            results = []
            for node in self.graph:
                if self.inDegree(node) == 0:
                    results.append(node)
            self.graph.graph['sources'] = results
            return results
        else:
            return self.graph.graph['sources']
