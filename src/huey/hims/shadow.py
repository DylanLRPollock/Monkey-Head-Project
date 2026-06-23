"""Shadow-mode HIMS trace emission for V1 runtime flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from huey.hims.schema import HIMSMessage, MessageStatus, TrustClass
from huey.hims.thundermail import ThunderMail


class ShadowHIMS:
    """Emit HIMS mailbox and ledger records without replacing V1 authority."""

    def __init__(self, root: Path) -> None:
        self.mail = ThunderMail(root)

    @property
    def root(self) -> Path:
        return self.mail.root

    @property
    def ledger_path(self) -> Path:
        return self.mail.ledger_path

    def read_message(self, message_id: str) -> dict[str, Any] | None:
        """Return one persisted message snapshot."""

        return self.mail.read_message(message_id)

    def read_ledger(self) -> list[dict[str, Any]]:
        """Return the append-only ledger entries."""

        return self.mail.read_ledger()

    def emit_run_record(self, run_record: dict[str, Any]) -> dict[str, Any]:
        """Translate one authoritative V1 run record into shadow HIMS traces."""

        run_id = str(run_record.get("run_id") or uuid4().hex)
        return self.emit_trace(
            lineage_id=run_id,
            source_file=str(run_record.get("source_file", "")),
            transcript=run_record.get("transcript"),
            response=run_record.get("response"),
            exit_status=str(run_record.get("exit_status", "error")),
            error_message=(
                str(run_record.get("error_message_if_any"))
                if run_record.get("error_message_if_any")
                else None
            ),
            authoritative_reference={
                "type": "v1_run_record",
                "run_id": run_id,
            },
            context={
                "timestamp_start": run_record.get("timestamp_start"),
                "timestamp_end": run_record.get("timestamp_end"),
                "runtime_seconds": run_record.get("runtime_seconds"),
                "transcription_engine": run_record.get("transcription_engine"),
                "transcription_model": run_record.get("transcription_model"),
                "cognition_provider": run_record.get("cognition_provider"),
                "cognition_model": run_record.get("cognition_model"),
            },
        )

    def emit_proof_loop_record(
        self,
        *,
        source_file: str | Path,
        prepared_audio: str | Path,
        transcript: str,
        response_text: str,
        audio_manifest: dict[str, Any],
        response_payload: dict[str, Any],
        structured_log_event_id: str | None = None,
    ) -> dict[str, Any]:
        """Translate one proof-loop completion into shadow HIMS traces."""

        lineage_id = structured_log_event_id or uuid4().hex
        authoritative_reference = (
            {
                "type": "proof_loop_log_event",
                "event_id": structured_log_event_id,
            }
            if structured_log_event_id
            else {
                "type": "proof_loop_result",
                "result_id": lineage_id,
            }
        )
        return self.emit_trace(
            lineage_id=lineage_id,
            source_file=str(source_file),
            transcript=transcript,
            response=response_text,
            exit_status="success",
            error_message=None,
            authoritative_reference=authoritative_reference,
            context={
                "prepared_audio": str(prepared_audio),
                "audio_manifest": dict(audio_manifest),
                "response_payload": dict(response_payload),
            },
        )

    def emit_trace(
        self,
        *,
        lineage_id: str,
        source_file: str,
        transcript: Any,
        response: Any,
        exit_status: str,
        error_message: str | None,
        authoritative_reference: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Emit the first shadow-mode HIMS slice for one V1-style event."""

        if not source_file.strip():
            raise ValueError("source_file is required for shadow HIMS traces")
        if not lineage_id.strip():
            raise ValueError("lineage_id is required for shadow HIMS traces")

        shared_context = dict(context or {})
        authoritative_reference = dict(authoritative_reference)

        packet = HIMSMessage(
            sender="labtech.aperture",
            recipient="huey_brain.aperture_translation",
            role_context="v1_shadow_ingress",
            intent_type="external_interface_packet",
            payload={
                "source_file": source_file,
                "authoritative_reference": authoritative_reference,
                "context": shared_context,
            },
            authority_requirement="aperture_translation",
            status=MessageStatus.ACCEPTED,
            trust_class=TrustClass.ROUTINE_INTERNAL,
            route=["external_input", "aperture_translation"],
            signature_or_validation_metadata={
                "shadow_mode": True,
                "preserves_authoritative_v1_record": True,
            },
            lineage_metadata={
                "root_lineage_id": lineage_id,
                "lineage_stage": "external_interface_packet",
                "authoritative_path": "v1",
            },
        )
        packet_snapshot = self.mail.post(
            packet,
            metadata={"shadow_mode": True, "lineage_stage": "external_interface_packet"},
        )
        self.mail.transition(
            packet.message_id,
            status=MessageStatus.ARCHIVED,
            reason="Translated into internal shadow request",
            lineage_updates={"lineage_stage": "external_interface_packet_archived"},
        )

        request = HIMSMessage(
            sender="huey_brain.aperture_translation",
            recipient="huey_brain.v1_loop",
            role_context="v1_fixture_run",
            intent_type="request",
            payload={
                "source_file": source_file,
                "transcript": transcript,
                "requested_operation": "cognition_bridge_run",
                "authoritative_reference": authoritative_reference,
                "context": shared_context,
            },
            authority_requirement="v1_fixture_run",
            status=MessageStatus.QUEUED,
            trust_class=TrustClass.ROUTINE_INTERNAL,
            route=[
                "aperture_translation",
                "hims_routing",
                "pending_validation",
                "v1_loop",
            ],
            signature_or_validation_metadata={
                "shadow_mode": True,
                "validation_state": "pending",
            },
            lineage_metadata={
                "root_lineage_id": lineage_id,
                "parent_message_id": packet.message_id,
                "lineage_stage": "request",
                "authoritative_path": "v1",
            },
            correlation_id=lineage_id,
        )
        request_snapshot = self.mail.post(
            request,
            metadata={"shadow_mode": True, "lineage_stage": "request"},
        )

        if exit_status == "success":
            self.mail.transition(
                request.message_id,
                status=MessageStatus.ACCEPTED,
                reason="Shadow approval for V1 fixture run",
                signature_updates={"validation_state": "accepted"},
                lineage_updates={"validation_outcome": "accepted"},
            )
            request_snapshot = self.mail.transition(
                request.message_id,
                status=MessageStatus.EXECUTED,
                reason="Authoritative V1 run completed",
                signature_updates={"validation_state": "executed"},
                lineage_updates={"terminal_state": "executed"},
            )
            outcome_intent = "report"
            outcome_trust_class = TrustClass.ROUTINE_INTERNAL
        else:
            request_snapshot = self.mail.transition(
                request.message_id,
                status=MessageStatus.REJECTED,
                reason=error_message or "Authoritative V1 run failed",
                signature_updates={"validation_state": "rejected"},
                lineage_updates={"terminal_state": "rejected"},
            )
            outcome_intent = "alert"
            outcome_trust_class = TrustClass.BRANCH_OR_OFFICE_RESTRICTED

        outcome = HIMSMessage(
            sender="huey_brain.v1_loop",
            recipient="labtech.operator",
            role_context="v1_fixture_run",
            intent_type=outcome_intent,
            payload={
                "source_file": source_file,
                "transcript": transcript,
                "response": response,
                "exit_status": exit_status,
                "error_message": error_message,
                "authoritative_reference": authoritative_reference,
                "context": shared_context,
            },
            authority_requirement="structured_record",
            status=MessageStatus.EXECUTED,
            trust_class=outcome_trust_class,
            route=["v1_loop", "structured_log", "operator_visibility"],
            signature_or_validation_metadata={
                "shadow_mode": True,
                "request_terminal_status": request_snapshot["status"],
            },
            lineage_metadata={
                "root_lineage_id": lineage_id,
                "parent_message_id": request.message_id,
                "request_message_id": request.message_id,
                "lineage_stage": outcome_intent,
                "authoritative_path": "v1",
            },
            correlation_id=request.message_id,
        )
        outcome_snapshot = self.mail.post(
            outcome,
            metadata={"shadow_mode": True, "lineage_stage": outcome_intent},
        )

        archive = HIMSMessage(
            sender="huey_brain.shadow_hims",
            recipient="huey.archive",
            role_context="v1_shadow_archive",
            intent_type="archived_record",
            payload={
                "source_file": source_file,
                "request_message_id": request.message_id,
                "outcome_message_id": outcome.message_id,
                "terminal_request_status": request_snapshot["status"],
                "authoritative_reference": authoritative_reference,
                "context": shared_context,
            },
            authority_requirement="continuity_record",
            status=MessageStatus.ARCHIVED,
            trust_class=TrustClass.BRANCH_OR_OFFICE_RESTRICTED,
            route=["structured_log", "shadow_archive"],
            signature_or_validation_metadata={
                "shadow_mode": True,
                "preserves_authoritative_v1_record": True,
            },
            lineage_metadata={
                "root_lineage_id": lineage_id,
                "parent_message_id": outcome.message_id,
                "request_message_id": request.message_id,
                "lineage_stage": "archived_record",
                "authoritative_path": "v1",
            },
            correlation_id=outcome.message_id,
        )
        archive_snapshot = self.mail.post(
            archive,
            metadata={"shadow_mode": True, "lineage_stage": "archived_record"},
        )

        return {
            "root_lineage_id": lineage_id,
            "packet_message_id": packet_snapshot["message_id"],
            "request_message_id": request_snapshot["message_id"],
            "outcome_message_id": outcome_snapshot["message_id"],
            "archive_message_id": archive_snapshot["message_id"],
            "shadow_root": str(self.root),
            "shadow_ledger": str(self.ledger_path),
        }


__all__ = ["ShadowHIMS"]
