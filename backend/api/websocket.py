"""PROJECT LASTLINE: WebSocket Live Streaming Hub.

Broadcasts live operational state frames, sensor trust scores, and multi-agent
diagnostics to connected control-room client interfaces <= 1 second intervals.
"""

import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from backend.api.state import get_system_state


async def handle_live_stream(websocket: WebSocket) -> None:
    """Manages continuous state broadcast over an open WebSocket connection."""
    await websocket.accept()
    state = get_system_state()

    try:
        # Immediate frame on connect
        initial_frame = state.get_current_frame()
        await websocket.send_json(initial_frame)

        while True:
            # Advance simulation hour if playing
            if state.replay.is_playing:
                state.replay.step_forward()

            frame = state.get_current_frame()
            await websocket.send_json(frame)

            # Sleep interval scaled by replay speed (default 1.0 second per step)
            delay = max(0.2, 1.0 / max(state.replay.speed, 0.1))
            await asyncio.sleep(delay)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
