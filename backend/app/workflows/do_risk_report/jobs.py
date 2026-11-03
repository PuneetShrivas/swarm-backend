"""
Asynchronous Job Execution Manager and Server-Sent Events (SSE) Push Channel
for D&O Public Risk Underwriting Reports.
Provides non-blocking job creation, status polling, and real-time streaming
of pipeline progress and completed markdown sections for early reading.
"""

import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel, Field

from app.workflows.do_risk_report.orchestrator import DORiskReportOrchestrator


class CompletedSection(BaseModel):
    section: str
    title: str
    content: str
    completed_at: str


class ReportJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    mode: str = "standard"
    provider: Optional[str] = "gpt-oss"
    fallback_model: Optional[str] = None
    current_date: Optional[str] = None
    user_id: Optional[str] = None
    status: str = "pending"  # "pending", "running", "completed", "failed"
    progress_stage: str = "initialized"
    progress_detail: str = "Job created"
    sections_completed_count: int = 0
    completed_sections: Dict[str, CompletedSection] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobManager:
    """
    Centralized in-memory job state and SSE event broadcaster.
    Thread-safe and async-safe across concurrent report requests.
    """
    _instance: Optional["JobManager"] = None

    def __init__(self):
        self._jobs: Dict[str, ReportJob] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "JobManager":
        if cls._instance is None:
            cls._instance = JobManager()
        return cls._instance

    def create_job(
        self,
        ticker: str,
        mode: str = "standard",
        current_date: Optional[str] = None,
        user_id: Optional[str] = None,
        provider: Optional[str] = None,
        fallback_model: Optional[str] = None,
    ) -> ReportJob:
        job = ReportJob(
            ticker=ticker.strip().upper(),
            mode=mode,
            current_date=current_date,
            user_id=user_id,
            provider=provider or "gpt-oss",
            fallback_model=fallback_model,
        )
        self._jobs[job.job_id] = job
        self._subscribers[job.job_id] = []
        return job

    def get_job(self, job_id: str) -> Optional[ReportJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50) -> List[ReportJob]:
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def _broadcast(self, job_id: str, event_name: str, data: Dict[str, Any]) -> None:
        queues = self._subscribers.get(job_id, [])
        msg = f"event: {event_name}\ndata: {json.dumps(data)}\n\n"
        for q in list(queues):
            try:
                q.put_nowait(msg)
            except Exception:
                pass

    def start_job(
        self,
        job_id: str,
        orchestrator: Optional[DORiskReportOrchestrator] = None,
    ) -> asyncio.Task:
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found")

        job.status = "running"
        job.progress_stage = "starting"
        job.progress_detail = f"Initiating pipeline for {job.ticker} ({job.mode} mode)..."
        job.updated_at = datetime.now(timezone.utc).isoformat()
        self._broadcast(job_id, "progress", {
            "job_id": job_id,
            "stage": job.progress_stage,
            "detail": job.progress_detail,
            "updated_at": job.updated_at,
        })

        orch = orchestrator or DORiskReportOrchestrator()
        task = asyncio.create_task(self._run_job_coro(job, orch))
        return task

    async def _run_job_coro(self, job: ReportJob, orch: DORiskReportOrchestrator) -> None:
        job_id = job.job_id

        def on_progress(stage: str, detail: str):
            job.progress_stage = stage
            job.progress_detail = detail
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._broadcast(job_id, "progress", {
                "job_id": job_id,
                "stage": stage,
                "detail": detail,
                "updated_at": job.updated_at,
            })

        async def on_section_complete(sec_name: str, sec_title: str, content: str):
            now_iso = datetime.now(timezone.utc).isoformat()
            sec_record = CompletedSection(
                section=sec_name,
                title=sec_title,
                content=content,
                completed_at=now_iso,
            )
            job.completed_sections[sec_name] = sec_record
            job.sections_completed_count = len(job.completed_sections)
            job.updated_at = now_iso
            self._broadcast(job_id, "section_complete", {
                "job_id": job_id,
                "section": sec_name,
                "title": sec_title,
                "content": content,
                "sections_completed_count": job.sections_completed_count,
                "completed_at": now_iso,
            })

        try:
            result = await orch.run(
                ticker=job.ticker,
                mode=job.mode,
                current_date=job.current_date,
                user_id=job.user_id,
                provider=job.provider or "gpt-oss",
                fallback_model=job.fallback_model,
                on_progress=on_progress,
                on_section_complete=on_section_complete,
            )
            job.status = "completed"
            job.progress_stage = "done"
            job.progress_detail = "Report generation and artifact compilation complete"
            job.result = result.model_dump()
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._broadcast(job_id, "completed", {
                "job_id": job_id,
                "status": "completed",
                "result": job.result,
                "updated_at": job.updated_at,
            })
        except Exception as e:
            job.status = "failed"
            job.progress_stage = "error"
            job.progress_detail = f"Failed: {str(e)}"
            job.error = str(e)
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._broadcast(job_id, "error", {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
                "updated_at": job.updated_at,
            })
        finally:
            # Send sentinel None to unblock any waiting subscribers
            for q in list(self._subscribers.get(job_id, [])):
                try:
                    q.put_nowait(None)
                except Exception:
                    pass

    async def subscribe(self, job_id: str) -> AsyncGenerator[str, None]:
        """
        Yields Server-Sent Events (SSE) for the specified job_id.
        Streams initial snapshot, live progress milestones, completed markdown sections,
        and final completion or error payload.
        """
        job = self.get_job(job_id)
        if not job:
            err_data = json.dumps({"error": f"Job '{job_id}' not found"})
            yield f"event: error\ndata: {err_data}\n\n"
            return

        q: asyncio.Queue = asyncio.Queue()
        if job_id not in self._subscribers:
            self._subscribers[job_id] = []
        self._subscribers[job_id].append(q)

        try:
            # 1. Send initial state snapshot immediately to subscriber
            yield f"event: init\ndata: {json.dumps(job.model_dump())}\n\n"

            # If job is already terminal, send terminal event and finish
            if job.status == "completed":
                yield f"event: completed\ndata: {json.dumps({'job_id': job_id, 'status': 'completed', 'result': job.result})}\n\n"
                return
            elif job.status == "failed":
                yield f"event: error\ndata: {json.dumps({'job_id': job_id, 'status': 'failed', 'error': job.error})}\n\n"
                return

            # 2. Stream events as they arrive
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    if msg is None:
                        # Sentinel received: check terminal status
                        current_job = self.get_job(job_id)
                        if current_job and current_job.status == "completed":
                            yield f"event: completed\ndata: {json.dumps({'job_id': job_id, 'status': 'completed', 'result': current_job.result})}\n\n"
                        elif current_job and current_job.status == "failed":
                            yield f"event: error\ndata: {json.dumps({'job_id': job_id, 'status': 'failed', 'error': current_job.error})}\n\n"
                        break
                    yield msg
                except asyncio.TimeoutError:
                    # Send periodic SSE comment heartbeat to keep HTTP connection alive
                    yield ": keep-alive\n\n"
        finally:
            if job_id in self._subscribers and q in self._subscribers[job_id]:
                self._subscribers[job_id].remove(q)


job_manager = JobManager.get_instance()
