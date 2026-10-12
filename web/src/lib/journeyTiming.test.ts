import {describe,it,expect} from 'vitest';
import {arrivalTiming} from './journeyTiming';
describe('scan based arrival',()=>{
 it('counts down from the scan while preserving arrival window',()=>{const start='2026-10-12T08:00:00Z';const a=arrivalTiming(start,30,60,Date.parse(start))!;const b=arrivalTiming(start,30,60,Date.parse(start)+10*60000)!;expect(a.remaining).toBe('30–60 min remaining');expect(b.remaining).toBe('20–50 min remaining');expect(a.arrival).toBe(b.arrival);});
 it('handles expired window and absent scans',()=>{expect(arrivalTiming('2026-10-12T08:00:00',30,60,Date.parse('2026-10-12T10:00:00Z'))!.remaining).toContain('passed');expect(arrivalTiming(undefined,30,60,Date.now())).toBeNull();});
});
