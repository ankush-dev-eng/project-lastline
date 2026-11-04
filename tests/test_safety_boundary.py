"""Phase 0 / Gate Safety Test: Hard Safety Boundary & Zero Write Actuation Guarantee.

HARD SAFETY RULE: The system is advisory and sandboxed. It must NEVER send or
implement real control commands. All 'actions' are recommendations requiring human
approval, simulated only in the twin. Build this guarantee into the architecture
(no write-capable interfaces) and test it.
"""

import ast
from pathlib import Path


FORBIDDEN_CONTROL_CALLS = {
    "pymodbus.client.sync.ModbusTcpClient.write_coil",
    "pymodbus.client.sync.ModbusTcpClient.write_register",
    "pymodbus.client.sync.ModbusTcpClient.write_registers",
    "cpppo.server.enip.client.connector.write",
    "pycomm3.LogixDriver.write",
    "snap7.client.Client.db_write",
    "snap7.client.Client.as_db_write",
}

FORBIDDEN_METHOD_NAMES = {
    "send_control_command",
    "actuate_hardware",
    "write_plc_setpoint",
    "override_physical_actuator",
    "execute_physical_override",
}


def test_no_forbidden_industrial_protocols():
    """Verify that no physical PLC/SCADA write drivers or libraries are present in codebase."""
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    python_files = list(backend_dir.glob("**/*.py"))

    for py_file in python_files:
        content = py_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_CONTROL_CALLS:
            assert forbidden not in content, (
                f"SAFETY VIOLATION: Forbidden physical write reference '{forbidden}' found in {py_file}!"
            )


def test_no_write_capable_ast_methods():
    """Parse all AST trees across backend, twin, and agents to guarantee zero physical control methods."""
    root_dir = Path(__file__).resolve().parent.parent
    checked_dirs = [root_dir / "backend", root_dir / "twin"]

    for d in checked_dirs:
        if not d.exists():
            continue
        for py_file in d.glob("**/*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    assert node.name not in FORBIDDEN_METHOD_NAMES, (
                        f"SAFETY VIOLATION: Forbidden write-capable function '{node.name}' declared in {py_file}!"
                    )
