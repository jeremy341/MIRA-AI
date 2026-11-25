/**
 * Job progress, pure. A job is polled from `/api/v1/jobs/{id}` and moved on by `job_progress` and
 * `job_finished` events from the events feed. Covered by job-progress.test.ts.
 */
import type { BusEvent, Job, JobFinishedEventData, JobProgressEventData, JobStatus } from '../types';

export const JOB_ACTIVE: readonly JobStatus[] = ['queued', 'running'];

export function isJobActive(status: JobStatus): boolean {
  return JOB_ACTIVE.includes(status);
}

/** 0.0 to 1.0 as a whole percentage. Anything that is not a number counts as 0. */
export function percentOf(progress: number | null | undefined): number {
  if (typeof progress !== 'number' || !Number.isFinite(progress)) return 0;
  return Math.min(100, Math.max(0, Math.round(progress * 100)));
}

/** Applies one events-feed message to a job. Returns the same object when the event is for another job. */
export function applyJobEvent(job: Job, event: BusEvent): Job {
  if (event.type === 'job_progress') {
    const data = event.data as Partial<JobProgressEventData>;
    if (data.job_id !== job.id || !isJobActive(job.status)) return job;
    return {
      ...job,
      progress: typeof data.progress === 'number' ? Math.min(1, Math.max(0, data.progress)) : job.progress,
      message: typeof data.message === 'string' && data.message ? data.message : job.message,
    };
  }
  if (event.type === 'job_finished') {
    const data = event.data as Partial<JobFinishedEventData>;
    if (data.job_id !== job.id) return job;
    const status = data.status;
    if (status !== 'completed' && status !== 'failed' && status !== 'cancelled') return job;
    return {
      ...job,
      status,
      progress: status === 'completed' ? 1 : job.progress,
      error: typeof data.error === 'string' ? data.error : job.error,
    };
  }
  return job;
}

/** A short status for a job row: "Running, 42%", "Finished", "Cancelled", "Failed". */
export function jobStatusLabel(job: Pick<Job, 'status' | 'progress'>): string {
  switch (job.status) {
    case 'queued':
      return 'Queued';
    case 'running':
      return `Running, ${percentOf(job.progress)}%`;
    case 'completed':
      return 'Finished';
    case 'failed':
      return 'Failed';
    case 'cancelled':
      return 'Cancelled';
  }
}
