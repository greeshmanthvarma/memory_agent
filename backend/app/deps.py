from fastapi import Request
def get_compiled_graph(request: Request):
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise RuntimeError("Graph not found")
    return graph
