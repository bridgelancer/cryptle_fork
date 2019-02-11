import networkx as nx
import networkx.algorithms.dag as dag
import networkx.algorithms.traversal.depth_first_search as dfs

from typing import Any, List, Optional
from datetime import time

"""Graph representation of the state of Timeseries connection using networkx library"""


class TSGraph:
    """Static NetworkX DiGraph wrapper in Timeseries class"""

    def __init__(self):
        self.graph = nx.DiGraph()

    def __len__(self):
        """Returns the total number of nodes present in the graph"""
        return len(self.graph)

    def inDegree(self, *nodes):
        """Returns the total number of incoming edge of the input nodes. Returns the
        total number of incoming edges with no nodes were given."""
        return self.graph.in_degree(*nodes)

    def outDegree(self, *nodes):
        """Returns the total number of outgoing edge of the input nodes. Returns the
        total number of outgoing edges with no nodes were given."""
        return self.graph.out_degree(*nodes)

    def size(self, weight=None):
        """Returns the the number of edges or total of all edge attributes values"""
        if weight is None:
            return self.graph.size()
        else:
            return self.graph.size(weight)

    def nodeView(self):
        """Returns an NetworkX NodeView of the TS graph"""
        return self.graph.nodes

    def edges(self):
        """Returns an NetworkX OutEdgeView of the TS graph"""
        return self.graph.edges

    def adj(self):
        return self.graph.adj

    def addNode(self, ts):
        """Construct necessary node and edges, called during an instance TS __inti__"""
        self.graph.add_node(ts)

        for publisher in ts.publishers:
            self.graph.add_edge(publisher, ts)

        self.graph.nodes[ts]['is_broadcasted'] = False

    def isDAG(self):
        """Returns whether the graph is a directed acyclic graph"""
        return dag.is_directed_acyclic_graph(self.graph)

    def topological_sort(self):
        """Returns an iterable of node names in topological sorted order of a directed
        acyclic graph"""
        return dag.topological_sort(self.graph)

    def predecessors(self, ts):
        """Returns a list of predecessor of node ts"""
        return list(self.graph.predecessors(ts))

    def attr(self, ts, attr):
        """Returns the value of a particular node attribute of the ts"""
        return self.graph.nodes[ts][attr]

    def setNodeAttr(self, ts, attr_name: str, attr_val: Any):
        self.graph.nodes[ts][attr_name] = attr_val

    def setExecuteTime(self, predecessor, successor, t: Optional[List[time]] = None):
        if time is None:
            raise ValueError('Please input a valid time')

        if not isinstance(t, list):
            t = [t]

        self.graph[predecessor][successor]['execute_time'] = t

    def getExecuteTime(self, predecessor, successor):
        return self.graph[predecessor][successor]['execute_time']

    def roots(self, ts):
        """Recursively search for the source of the ts and returns. Results cached"""
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
        """Update broadcast status of Timeseries after broadcasting. Called before
        actual broadcast proceeds."""
        # print(f'\nUpdating {repr(ts)}...')
        self.graph.nodes[ts]['is_broadcasted'] = True

        # All source TS (i.e. open_buffer, timestamp etc.) has no incoming edges
        if self.inDegree(ts) == 0:
            # print(f'this is a source {repr(ts)}')

            # recursively search all successors, mark them as not broadcasted
            for _, successors in self.dfsSuccessors(ts).items():
                for successor in successors:
                    self.graph.nodes[successor]['is_broadcasted'] = False

    def checkResetCondition(self):
        """Check whether all source nodes are broadcasted during this episode"""
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

    def resetBrodcastStatus(self):
        """Reset all ``is_broadcasted`` node attribute to False"""
        for node in self.graph:
            self.graph.nodes[node]['is_broadcasted'] = False

    def dfsSuccessors(self, ts):
        """Return an dictionary of successors in DFS from ts"""
        return dfs.dfs_successors(self.graph, ts)

    def sources(self):
        """Set and return the the emitting TS sources as NetworkX graph attribute"""
        if 'sources' not in self.graph.graph:
            results = []
            for node in self.graph:
                if self.inDegree(node) == 0:
                    results.append(node)
            self.graph.graph['sources'] = results
            return results
        else:
            return self.graph.graph['sources']
