import uuid
from threading import Lock
from threading import Timer

_jobs = {}
_active_jobs = {}  # (user_id, conversation_id) -> job_id
_lock = Lock()


def create_job(user_id: str, conversation_id: int):
    job_id = str(uuid.uuid4())

    with _lock:
        _jobs[job_id] = {
            "user_id": user_id,
            "conversation_id": conversation_id,

            "answer": "",
            "thinking": "",

            "finished": False,
            "error": None,
        }
        _active_jobs[(user_id, conversation_id)] = job_id

    return job_id


def get_job(job_id: str):
    return _jobs.get(job_id)


def get_active_job_id(user_id: str, conversation_id: int):
    return _active_jobs.get((user_id, conversation_id))


def append(job_id: str, thinking: str = "", content: str = ""):
    job = _jobs.get(job_id)

    if not job:
        return

    if thinking:
        job["thinking"] += thinking

    if content:
        job["answer"] += content

def finish(job_id: str):
    job = _jobs.get(job_id)

    if job:
        job["finished"] = True

        # 30초 후 자동 삭제
        Timer(30, remove, args=(job_id,)).start()

def remove(job_id: str):
    with _lock:
        job = _jobs.pop(job_id, None)

        if job:
            key = (job["user_id"], job["conversation_id"])
            if _active_jobs.get(key) == job_id:
                _active_jobs.pop(key, None)