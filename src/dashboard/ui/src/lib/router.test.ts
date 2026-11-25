import { describe, expect, it } from 'vitest';
import { DEFAULT_ROUTE, parseLocation, parseRoute, routeHref } from './router';

describe('parseLocation', () => {
  it('reads a plain route with no id', () => {
    expect(parseLocation('#/models')).toEqual({ name: 'models', id: null, known: true });
  });

  it('reads the session id from #/sessions/<id>, decoded', () => {
    expect(parseLocation('#/sessions/s001a7f3')).toEqual({ name: 'sessions', id: 's001a7f3', known: true });
    expect(parseLocation('#/sessions/a%20b')).toEqual({ name: 'sessions', id: 'a b', known: true });
  });

  it('ignores a second segment on routes that do not take an id', () => {
    expect(parseLocation('#/models/extra')).toEqual({ name: 'models', id: null, known: true });
  });

  it('keeps the id when the sessions id is empty', () => {
    expect(parseLocation('#/sessions/')).toEqual({ name: 'sessions', id: null, known: true });
  });

  it('marks an empty or unknown hash as not known, so the store rewrites it', () => {
    expect(parseLocation('')).toEqual({ name: DEFAULT_ROUTE, id: null, known: false });
    expect(parseLocation('#/')).toEqual({ name: DEFAULT_ROUTE, id: null, known: false });
    expect(parseLocation('#/nope/5')).toEqual({ name: DEFAULT_ROUTE, id: null, known: false });
  });

  it('survives a malformed escape in the id', () => {
    expect(parseLocation('#/sessions/%E0%A4%A')).toEqual({ name: 'sessions', id: null, known: true });
  });
});

describe('parseRoute and routeHref with ids', () => {
  it('still returns just the route name', () => {
    expect(parseRoute('#/sessions/abc')).toBe('sessions');
  });

  it('builds the session detail hash with an encoded id', () => {
    expect(routeHref('sessions', 'abc')).toBe('#/sessions/abc');
    expect(routeHref('sessions', 'a/b')).toBe('#/sessions/a%2Fb');
  });

  it('drops the id for routes that do not take one', () => {
    expect(routeHref('models', 'abc')).toBe('#/models');
    expect(routeHref('sessions')).toBe('#/sessions');
  });
});
