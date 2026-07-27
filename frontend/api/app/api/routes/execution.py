from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.codegen.graph_structurer import GraphEdge, GraphNode
from app.execution.interpreter import FlowchartInterpreter
from app.execution.schemas import ExecuteRequest, ExecuteResponse, TraceStepOut
from app.models.user import User

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("/run", response_model=ExecuteResponse)
def run_execution(payload: ExecuteRequest, _: User = Depends(get_current_user)):
    nodes = [GraphNode(id=n.id, type=n.type, text=n.text) for n in payload.nodes]
    edges = [GraphEdge(id=e.id, from_id=e.fromNodeId, to_id=e.toNodeId, label=e.label) for e in payload.edges]

    interpreter = FlowchartInterpreter(nodes, edges, input_values=payload.input_values)
    result = interpreter.run()

    return ExecuteResponse(
        steps=[
            TraceStepOut(
                step_index=s.step_index, node_id=s.node_id, node_type=s.node_type,
                label=s.label, variables=s.variables, output=s.output, branch_taken=s.branch_taken,
            )
            for s in result.steps
        ],
        final_variables=result.final_variables,
        console_output=result.console_output,
        status=result.status,
        error_message=result.error_message,
        error_node_id=result.error_node_id,
        warnings=result.warnings,
    )
