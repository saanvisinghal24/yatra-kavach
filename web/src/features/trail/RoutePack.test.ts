import { describe, it, expect } from 'vitest';
import { deviation } from './RoutePack';

describe('Route deviation', () => {
  it('returns zero for a point on the route', () => {
    expect(
      deviation([[77, 28], [77.002, 28]], [77.001, 28])
    ).toBeCloseTo(0, 5);
  });
});
