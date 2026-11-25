import { describe, expect, it } from 'vitest';
import { clientFps, frameSrc, initialLiveState, MAX_FRAME_CHARS, normalizeDetections, parseVideoMessage, reduceLive } from './video-state';
import { parseEventMessage } from './events-feed';
import { toWebSocketUrl } from './transport';

describe('parseVideoMessage', () => {
  it('recognises pong and the three message types', () => {
    expect(parseVideoMessage('pong')).toBe('pong');
    expect(parseVideoMessage('{"type":"frame","frame_id":1,"frame":"AA","detections":[],"timestamp":"x"}')).toMatchObject({ type: 'frame' });
    expect(parseVideoMessage('{"type":"metrics","fps":24}')).toMatchObject({ type: 'metrics' });
    expect(parseVideoMessage('{"type":"status","status":"connected","message":"m"}')).toMatchObject({ type: 'status' });
  });

  it('returns null for invalid JSON, non-objects and unknown types', () => {
    expect(parseVideoMessage('not json')).toBeNull();
    expect(parseVideoMessage('42')).toBeNull();
    expect(parseVideoMessage('{"type":"hardware_sample"}')).toBeNull();
  });
});

describe('normalizeDetections', () => {
  it('maps the live `class` key and keeps only well-formed entries', () => {
    const result = normalizeDetections([
      { class: 'glass', confidence: 0.9, bbox: [1, 2, 3, 4], track_id: 7 },
      { class: 'unknown', confidence: 0.9, bbox: [1, 2, 3, 4] },
      { class: 'paper', confidence: 0.5, bbox: [1, 2, 3] },
      { class_name: 'trash', confidence: 0.4, bbox: [0, 0, 5, 5], track_id: null },
      { class: 'metal', confidence: 'high', bbox: [1, 2, 3, 4] },
      null,
    ]);
    expect(result).toEqual([
      { className: 'glass', confidence: 0.9, bbox: [1, 2, 3, 4], trackId: 7 },
      { className: 'trash', confidence: 0.4, bbox: [0, 0, 5, 5], trackId: null },
    ]);
  });

  it('returns an empty list for non-arrays', () => {
    expect(normalizeDetections(undefined)).toEqual([]);
    expect(normalizeDetections({})).toEqual([]);
  });
});

describe('reduceLive', () => {
  const frame = (id: number, data = 'QUJD') => ({
    type: 'frame' as const,
    frame_id: id,
    frame: data,
    detections: [{ class: 'glass' as const, confidence: 0.8, bbox: [1, 1, 9, 9] as [number, number, number, number], track_id: null, timestamp: 't' }],
    timestamp: 't',
  });

  it('stores the latest frame as a data URI with normalised detections', () => {
    const next = reduceLive(initialLiveState(), frame(3), 1000);
    expect(next.frame?.src).toBe('data:image/jpeg;base64,QUJD');
    expect(next.frame?.frameId).toBe(3);
    expect(next.frame?.detections[0].className).toBe('glass');
    expect(next.framesReceived).toBe(1);
    expect(next.lastFrameAt).toBe(1000);
  });

  it('skips a frame that is too large and says why', () => {
    const huge = 'A'.repeat(MAX_FRAME_CHARS + 1);
    const next = reduceLive(initialLiveState(), frame(4, huge), 1000);
    expect(next.frame).toBeNull();
    expect(next.notice).toMatch(/too large/);
    expect(next.framesReceived).toBe(1);
  });

  it('skips an empty frame', () => {
    const next = reduceLive(initialLiveState(), frame(5, ''), 1000);
    expect(next.frame).toBeNull();
    expect(next.notice).toMatch(/empty/);
  });

  it('clears the notice when a normal frame follows', () => {
    const big = reduceLive(initialLiveState(), frame(1, 'A'.repeat(MAX_FRAME_CHARS + 1)), 1000);
    const ok = reduceLive(big, frame(2), 1100);
    expect(ok.notice).toBeNull();
    expect(ok.frame?.frameId).toBe(2);
  });

  it('maps metrics fields to camel case and records the time', () => {
    const next = reduceLive(
      initialLiveState(),
      {
        type: 'metrics',
        fps: 24.5,
        inference_latency_ms: 41.2,
        avg_latency_ms: 40,
        cpu_percent: 30,
        memory_percent: 45,
        temperature_celsius: null,
        detections_per_second: 2,
        skip_frames: false,
        timestamp: 't',
      },
      500,
    );
    expect(next.metrics).toMatchObject({ fps: 24.5, latencyMs: 41.2, avgLatencyMs: 40, temperatureC: null, receivedAt: 500 });
  });

  it('records the server status message', () => {
    const next = reduceLive(initialLiveState(), { type: 'status', status: 'running', message: 'Streaming started' }, 1);
    expect(next.serverStatus).toBe('running');
    expect(next.serverMessage).toBe('Streaming started');
  });
});

describe('clientFps and frameSrc', () => {
  it('counts frames in the last second', () => {
    const times = [0, 100, 200, 300, 400];
    expect(clientFps(times, 400)).toBeCloseTo(10, 5);
    expect(clientFps(times, 5000)).toBe(0);
    expect(clientFps([], 100)).toBe(0);
  });

  it('adds the JPEG data prefix only when it is missing', () => {
    expect(frameSrc('QUJD')).toBe('data:image/jpeg;base64,QUJD');
    expect(frameSrc('data:image/jpeg;base64,QUJD')).toBe('data:image/jpeg;base64,QUJD');
  });
});

describe('socket URLs and event envelopes', () => {
  it('uses wss on https and ws otherwise', () => {
    expect(toWebSocketUrl('/ws/video', { protocol: 'http:', host: '127.0.0.1:8000' })).toBe('ws://127.0.0.1:8000/ws/video');
    expect(toWebSocketUrl('/ws/v1/events', { protocol: 'https:', host: 'mira.local' })).toBe('wss://mira.local/ws/v1/events');
  });

  it('parses bus events and drops hello and ping', () => {
    expect(parseEventMessage('{"type":"hello","ts":"t","data":{"version":1}}')).toBeNull();
    expect(parseEventMessage('{"type":"ping"}')).toBeNull();
    expect(parseEventMessage('{"type":"arm_event","ts":"t","data":{"kind":"sort_requested"}}')).toMatchObject({ type: 'arm_event' });
    expect(parseEventMessage('nope')).toBeNull();
  });
});
