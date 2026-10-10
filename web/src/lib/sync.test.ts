import 'fake-indexeddb/auto';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getCurrentClockSkew, syncPendingCheckins, enqueueCheckin } from './sync';
import { db } from './db';

describe('Offline Checkin Queue & Sync Manager', () => {
  beforeEach(async () => {
    await db.checkins.clear();
    await db.outbox.clear();
  });

  it('initializes clock skew at 0 seconds', () => {
    expect(getCurrentClockSkew()).toBe(0.0);
  });

  it('handles empty sync queue cleanly without network requests', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    const result = await syncPendingCheckins();
    expect(result.synced).toBe(0);
    expect(result.failed).toBe(0);
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it('correctly enqueues offline checkin into IndexedDB Dexie table', async () => {
    const item = await enqueueCheckin('TEST01', 2, 'Dhancho', 'YK1:CP:2:MOCK', 3, 'self');
    expect(item.groupCode).toBe('TEST01');
    expect(item.status).toBe('pending');
    expect(item.headcount).toBe(3);

    const stored = await db.checkins.where('groupCode').equals('TEST01').toArray();
    expect(stored.length).toBe(1);
    expect(stored[0].checkpointName).toBe('Dhancho');
  });

  it('correctly calculates clock skew from server Date header', () => {
    const serverDate = new Date('Wed, 23 Sep 2026 12:00:00 GMT');
    const localNow = new Date('Wed, 23 Sep 2026 12:00:05 GMT').getTime();
    const skewS = (localNow - serverDate.getTime()) / 1000.0;
    expect(skewS).toBe(5.0); // Local is 5 seconds ahead
  });
});

describe('bulk reconnect',()=>{
 beforeEach(async()=>{await db.checkins.clear();await db.outbox.clear();});
 it('drains 123 events in bounded batches and coalesces concurrent triggers',async()=>{
  for(let i=0;i<123;i++)await enqueueCheckin('TEST01',2,'Dhancho','signed-'+i,3);
  const sizes:number[]=[];
  const fetchSpy=vi.spyOn(globalThis,'fetch').mockImplementation(async(_url,init)=>{
   const events=JSON.parse(String(init?.body)).events;sizes.push(events.length);
   return new Response(JSON.stringify({results:events.map((e:any)=>({id:e.id,status:'accepted'})),accepted_count:events.length,duplicate_count:0,invalid_count:0}));
  });
  try{const [a,b]=await Promise.all([syncPendingCheckins(),syncPendingCheckins()]);expect(a.synced).toBe(123);expect(b).toEqual(a);expect(sizes).toEqual([50,50,23]);expect(await db.checkins.where('status').equals('pending').count()).toBe(0);}finally{fetchSpy.mockRestore();}
 });
 it('stops on network failure without discarding pending events',async()=>{
  await enqueueCheckin('TEST01',2,'Dhancho','signed',3);
  const fetchSpy=vi.spyOn(globalThis,'fetch').mockRejectedValue(new Error('offline'));
  try{expect((await syncPendingCheckins()).failed).toBe(1);expect(fetchSpy).toHaveBeenCalledTimes(1);expect(await db.checkins.where('status').equals('pending').count()).toBe(1);}finally{fetchSpy.mockRestore();}
 });
});
