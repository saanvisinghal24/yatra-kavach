import {describe,it,expect,vi} from 'vitest';
import 'fake-indexeddb/auto';
import {checkpointToken,passCode} from './qr';
import {enqueueCheckin,syncPendingCheckins} from './sync';
import {db} from './db';
describe('Signed offline QR pipeline',()=>{
 it('accepts camera URLs and rejects unsigned text',()=>{expect(checkpointToken('https://demo.invalid/check-in?token=YK1:CP:2:abcd1234')).toEqual({token:'YK1:CP:2:abcd1234',id:2});expect(()=>checkpointToken('YK1:CP:2:VALID')).toThrow();expect(passCode('YK1:ABC234')).toBe('ABC234');expect(passCode('https://demo.invalid/pass/ABC234?token=YK1:ABC234')).toBe('ABC234');});
 it('keeps a different signature for each queued event',async()=>{await db.checkins.clear();await db.outbox.clear();await enqueueCheckin('ABC234',1,'Hadsar','YK1:CP:1:abcd1234',3);await enqueueCheckin('ABC234',2,'Dhancho','YK1:CP:2:1234abcd',2);let payload:any;const mock=vi.spyOn(globalThis,'fetch').mockImplementation(async(_url,init)=>{payload=JSON.parse(init!.body as string);return new Response(JSON.stringify({results:payload.events.map((e:any)=>({id:e.id,status:'accepted'})),accepted_count:2,duplicate_count:0,invalid_count:0}),{headers:{Date:new Date().toUTCString()}});});await syncPendingCheckins();expect(Object.fromEntries(payload.events.map((e:any)=>[e.checkpoint_id,e.signed_qr]))).toEqual({1:'YK1:CP:1:abcd1234',2:'YK1:CP:2:1234abcd'});expect(await db.checkins.where('status').equals('synced').count()).toBe(2);mock.mockRestore();});
});
