from sqlalchemy import text
from app.models.receipt import Receipt
async def replay(db,key):
    if not key:return None
    if db.bind.dialect.name=='postgresql':
        await db.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{'key':key})
    receipt=await db.get(Receipt,key)
    return receipt.response if receipt else None
async def finish(db,key,group_id,response):
    if key:db.add(Receipt(id=key,group_id=group_id,response=response))
    await db.commit()
    return response
