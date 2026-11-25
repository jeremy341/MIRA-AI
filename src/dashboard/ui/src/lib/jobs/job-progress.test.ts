import { describe, expect, it } from 'vitest';
import type { BusEvent, Job } from '../types';
import { applyJobEvent, isJobActive, jobStatusLabel, percentOf } from './job-progress';

const base: Job = {
  id: 'job-1',
  kind: 'batch_video',
  title: 'Video batch',
  status: 'running',
  progress: 0.2,
  message: 'Frame 600 of 3,000',
  created_at: '2026-11-25T10:00:00+00:00',
  finished_at: null,
  result: null,
  error: null,
};

const progress = (job_id: string, value: number, message = 'Frame 1 of 3'): BusEvent => ({
  type: 'job_progress',
  ts: '2026-11-25T10:01:00+00:00',
  data: { job_id, progress: value, message },
});

const finished = (job_id: string, status: string, error: string | null = null): BusEvent => ({
  type: 'job_finished',
  ts: '2026-11-25T10:02:00+00:00',
  data: { job_id, status, error },
});

describe('job progress', () => {
  it('turns a fraction into a whole percentage and clamps the rest', () => {
    expect(percentOf(0.426)).toBe(43);
    expect(percentOf(1.4)).toBe(100);
    expect(percentOf(-1)).toBe(0);
    expect(percentOf(null)).toBe(0);
    expect(percentOf(Number.NaN)).toBe(0);
  });

  it('knows which statuses are still active', () => {
    expect(isJobActive('queued')).toBe(true);
    expect(isJobActive('running')).toBe(true);
    expect(isJobActive('completed')).toBe(false);
    expect(isJobActive('cancelled')).toBe(false);
  });

  it('moves a running job on with job_progress events for that job only', () => {
    const next = applyJobEvent(base, progress('job-1', 0.5, 'Frame 1,500 of 3,000'));
    expect(next.progress).toBe(0.5);
    expect(next.message).toBe('Frame 1,500 of 3,000');
    expect(applyJobEvent(base, progress('job-2', 0.9))).toBe(base);
  });

  it('keeps the progress the job already had when an event leaves it out', () => {
    const next = applyJobEvent(base, { type: 'job_progress', ts: '', data: { job_id: 'job-1' } });
    expect(next.progress).toBe(0.2);
    expect(next.message).toBe(base.message);
  });

  it('does not move a finished job back with a late progress event', () => {
    const done = { ...base, status: 'completed' as const, progress: 1 };
    expect(applyJobEvent(done, progress('job-1', 0.3))).toBe(done);
  });

  it('applies job_finished with the status and the error', () => {
    expect(applyJobEvent(base, finished('job-1', 'completed'))).toMatchObject({ status: 'completed', progress: 1 });
    expect(applyJobEvent(base, finished('job-1', 'failed', 'Out of memory'))).toMatchObject({
      status: 'failed',
      error: 'Out of memory',
    });
    expect(applyJobEvent(base, finished('job-1', 'cancelled'))).toMatchObject({ status: 'cancelled', progress: 0.2 });
  });

  it('ignores a finished event with an unknown status or for another job', () => {
    expect(applyJobEvent(base, finished('job-1', 'queued'))).toBe(base);
    expect(applyJobEvent(base, finished('job-9', 'completed'))).toBe(base);
  });

  it('labels a job row with its status and progress', () => {
    expect(jobStatusLabel(base)).toBe('Running, 20%');
    expect(jobStatusLabel({ status: 'queued', progress: 0 })).toBe('Queued');
    expect(jobStatusLabel({ status: 'completed', progress: 1 })).toBe('Finished');
    expect(jobStatusLabel({ status: 'cancelled', progress: 0.5 })).toBe('Cancelled');
  });
});
