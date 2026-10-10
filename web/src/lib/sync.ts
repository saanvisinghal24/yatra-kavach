import { db, LocalCheckin } from './db';

let lastSyncTimestamp: string | null = globalThis.localStorage?.getItem("lastSync") || null;
let currentClockSkewS = 0.0;

export function getLastSyncTime(): string | null {
  return lastSyncTimestamp;
}

export function getCurrentClockSkew(): number {
  return currentClockSkewS;
}

export async function getPendingCheckinCount(): Promise<number> {
  return (await db.outbox.where('status').equals('pending').count()) + await db.checkins.where('status').equals('pending').count();
}

export async function enqueueCheckin(
  groupCode: string,
  checkpointId: number,
  checkpointName: string,
  rawQr: string,
  headcount: number,
  source: 'self' | 'volunteer' = 'self',
  direction: 'outbound'|'returning'|'exit' = 'outbound',
  memberIds?: number[]
): Promise<LocalCheckin> {
  const checkin: LocalCheckin = {
    id: crypto.randomUUID(),
    groupCode,
    checkpointId,
    checkpointName,
    source,
    direction, memberIds,
    headcount,
    clientTs: new Date().toISOString(),
    clockSkewS: currentClockSkewS,
    signedQr: rawQr,
    status: 'pending'
  };

  await db.checkins.put(checkin);
  registerBackgroundSync();
  // Attempt background sync if online
  if (navigator.onLine) {
    syncPendingCheckins(rawQr).catch(() => undefined);
  }

  return checkin;
}

let activeSync: Promise<{synced:number;failed:number}> | null = null;
export function syncPendingCheckins(_lastRawQr?:string):Promise<{synced:number;failed:number}>{
 if(!activeSync)activeSync=drainQueue().finally(()=>{activeSync=null;});
 return activeSync;
}
async function drainQueue():Promise<{synced:number;failed:number}>{
 const total={synced:0,failed:0};
 for(const event of await db.outbox.where('status').equals('pending').toArray()){
  try{
   const response=await fetch('/api/v1'+event.path,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':event.id},body:JSON.stringify(event.payload)});
   if(response.ok){await db.outbox.update(event.id,{status:'synced'});total.synced++;}else total.failed++;
  }catch{total.failed++;}
 }
 // Drain bounded batches; stop if a network/server failure leaves a batch pending.
 while(true){
  const before=await db.checkins.where('status').equals('pending').count();
  if(!before)break;
  const result=await syncBatch();total.synced+=result.synced;total.failed+=result.failed;
  if(await db.checkins.where('status').equals('pending').count()>=before)break;
 }
 if(total.synced){lastSyncTimestamp=new Date().toISOString();globalThis.localStorage?.setItem('lastSync',lastSyncTimestamp);}
 return total;
}
async function syncBatch(): Promise<{synced:number;failed:number}>{
  const pending = await db.checkins.where('status').equals('pending').limit(50).toArray();
  if (pending.length === 0) {
    return { synced: 0, failed: 0 };
  }

  const payload = {
    events: pending.map(item => ({
      id: item.id,
      group_code: item.groupCode,
      checkpoint_id: item.checkpointId,
      signed_qr: item.signedQr || "",
      source: item.source,
      direction: item.direction || 'outbound',
      member_ids: item.memberIds,
      headcount: item.headcount,
      client_ts: item.clientTs,
      clock_skew_s: item.clockSkewS
    }))
  };

  try {
    const response = await fetch('/api/v1/checkins/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      return { synced: 0, failed: pending.length };
    }

    // Measure clock skew from HTTP Date header
    const serverDateHeader = response.headers.get('Date');
    if (serverDateHeader) {
      const serverTimeMs = new Date(serverDateHeader).getTime();
      const localTimeMs = Date.now();
      currentClockSkewS = (localTimeMs - serverTimeMs) / 1000.0;
    }

    const data = await response.json();
    lastSyncTimestamp = new Date().toISOString();
    globalThis.localStorage?.setItem("lastSync", lastSyncTimestamp);

    for (const res of data.results) {
      if (res.status === 'accepted' || res.status === 'duplicate') {
        await db.checkins.update(res.id, {
          status: 'synced',
          syncedAt: new Date().toISOString()
        });
      } else if (res.status === 'invalid') {
        await db.checkins.update(res.id, {
          status: 'invalid',
          invalidReason: res.invalid_reason || 'Rejected by server'
        });
      }
    }

    return { synced: data.accepted_count + data.duplicate_count, failed: data.invalid_count };
  } catch (err) {
    // Offline or network error; items remain pending in Dexie
    return { synced: 0, failed: pending.length };
  }
}

// Auto-trigger sync on network recovery
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    syncPendingCheckins().catch(() => undefined);
  });
}

export async function queueAction(path:string,payload:unknown){
 const id=crypto.randomUUID();await db.outbox.put({id,path,payload,status:'pending'});
 registerBackgroundSync();
 if(navigator.onLine)await syncPendingCheckins();
 return (await db.outbox.get(id))?.status==='synced';
}

function registerBackgroundSync(){
 if(typeof navigator!=='undefined'&&navigator.serviceWorker)navigator.serviceWorker.ready.then((r:any)=>r.sync?.register('yatra-checkins')).catch(()=>{});
}
