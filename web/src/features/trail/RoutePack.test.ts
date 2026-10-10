import {describe,it,expect} from 'vitest';
import {deviation} from './RoutePack';
describe('Controlled-track perpendicular deviation',()=>{
 it('measures the closest segment rather than distance to a checkpoint',()=>{expect(deviation([[77,28],[77.002,28]],[77.001,28])).toBeCloseTo(0,5);});
 it('reports a known 222.64 m offset on the synthetic test track',()=>{expect(deviation([[77,28],[77.002,28]],[77.001,28.002])).toBeCloseTo(222.64,2);});
 it('handles repeated track points without NaN',()=>{expect(Number.isFinite(deviation([[77,28],[77,28]],[77.001,28]))).toBe(true);});
});
