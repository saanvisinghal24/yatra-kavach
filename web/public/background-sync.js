/* Background Sync shares the Dexie IndexedDB schema; server UUIDs make retries safe. */
self.addEventListener('sync', event => {
  if (event.tag !== 'yatra-checkins') return;
  event.waitUntil((async () => {
    const database = await new Promise((resolve,reject) => {const r=indexedDB.open('YatraKavachDB');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
    const getPending = store => new Promise((resolve,reject) => {const tx=database.transaction(store);const r=tx.objectStore(store).index('status').getAll('pending');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
    const update = (store,row) => new Promise((resolve,reject)=>{const tx=database.transaction(store,'readwrite');tx.objectStore(store).put(row);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});
    const pending=await getPending('checkins');
    for(let i=0;i<pending.length;i+=50){const batch=pending.slice(i,i+50);const r=await fetch('/api/v1/checkins/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({events:batch.map(e=>({id:e.id,group_code:e.groupCode,checkpoint_id:e.checkpointId,signed_qr:e.signedQr||'',headcount:e.headcount,source:e.source,direction:e.direction||'outbound',member_ids:e.memberIds,client_ts:e.clientTs,clock_skew_s:e.clockSkewS}))})});if(!r.ok)throw new Error('Sync deferred');const data=await r.json();for(const result of data.results){const row=batch.find(e=>e.id===result.id);if(row&&['accepted','duplicate','invalid'].includes(result.status))await update('checkins',{...row,status:result.status==='invalid'?'invalid':'synced',invalidReason:result.invalid_reason,syncedAt:new Date().toISOString()});}}
    if(database.objectStoreNames.contains('outbox'))for(const row of await getPending('outbox')){const r=await fetch('/api/v1'+row.path,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':row.id},body:JSON.stringify(row.payload)});if(!r.ok)throw new Error('Sync deferred');await update('outbox',{...row,status:'synced'});}
    database.close();
  })());
});
