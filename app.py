from collections import deque
from threading import Lock
from uuid import uuid4
from flask import Flask, jsonify, request

app = Flask(__name__)


class JobQueue:
    def __init__(self):
        self.pending = deque()
        self.jobs = {}
        self.lock = Lock()

    def enqueue(self, payload):
        job = {"id": str(uuid4()), "status": "queued", "payload": payload}
        with self.lock:
            self.jobs[job["id"]] = job
            self.pending.append(job["id"])
        return job

    def claim(self):
        with self.lock:
            while self.pending:
                job = self.jobs[self.pending.popleft()]
                if job["status"] == "queued":
                    job["status"] = "processing"
                    return dict(job)
        return None

    def complete(self, job_id, result):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            if job["status"] == "processing":
                job["status"] = "completed"
                job["result"] = result
            return dict(job)

    def fail(self, job_id, error):
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return None
            if job["status"] == "processing":
                job["status"] = "failed"
                job["error"] = error
            return dict(job)

    def get(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            return dict(job) if job else None

    def stats(self):
        with self.lock:
            counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0}
            for job in self.jobs.values():
                counts[job["status"]] += 1
            counts["total"] = len(self.jobs)
            return counts


queue = JobQueue()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "distributed-job-queue"})


@app.post("/api/jobs")
def enqueue_job():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify({"error": "JSON object payload is required"}), 400
    return jsonify(queue.enqueue(payload)), 202


@app.post("/api/jobs/claim")
def claim_job():
    job = queue.claim()
    if job is None:
        return jsonify({"message": "no queued jobs"}), 204
    return jsonify(job)


@app.post("/api/jobs/<job_id>/complete")
def complete_job(job_id):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or "result" not in body:
        return jsonify({"error": "JSON body with 'result' is required"}), 400
    job = queue.complete(job_id, body["result"])
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


@app.post("/api/jobs/<job_id>/fail")
def fail_job(job_id):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("error"), str):
        return jsonify({"error": "JSON body with string 'error' is required"}), 400
    job = queue.fail(job_id, body["error"])
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    job = queue.get(job_id)
    if job is None:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


@app.get("/api/jobs/stats")
def stats():
    return jsonify(queue.stats())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
