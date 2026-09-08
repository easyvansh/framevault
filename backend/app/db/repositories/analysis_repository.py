from __future__ import annotations

import json

from app.db.database import get_connection


def _analysis_from_row(row: dict) -> dict:
    result = dict(row)
    result["results"] = json.loads(result.pop("results_json"))
    return result


def upsert_frame_analysis(analysis: dict) -> dict:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO frame_analyses (
                frame_id, analyzer_name, analyzer_version, results_json,
                execution_ms, status, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(frame_id, analyzer_name, analyzer_version) DO UPDATE SET
                results_json = excluded.results_json,
                execution_ms = excluded.execution_ms,
                status = excluded.status,
                error = excluded.error,
                updated_at = CURRENT_TIMESTAMP
            """,
            (analysis["frame_id"], analysis["analyzer_name"], analysis["analyzer_version"],
             json.dumps(analysis["results"], separators=(",", ":")), analysis["execution_ms"],
             analysis.get("status", "completed"), analysis.get("error")),
        )
        row = connection.execute(
            """SELECT * FROM frame_analyses
            WHERE frame_id = ? AND analyzer_name = ? AND analyzer_version = ?""",
            (analysis["frame_id"], analysis["analyzer_name"], analysis["analyzer_version"]),
        ).fetchone()
        return _analysis_from_row(row)


def list_frame_analyses(frame_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM frame_analyses WHERE frame_id = ? ORDER BY analyzer_name, analyzer_version",
            (frame_id,),
        ).fetchall()
        return [_analysis_from_row(row) for row in rows]
