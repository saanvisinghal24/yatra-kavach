"""Conservative materialized member state; every event remains in the check-in audit."""
from datetime import timezone
from sqlalchemy import select
from app.models.group import Member

def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

async def members_for(db, group):
    members = list((await db.execute(select(Member).where(Member.group_id == group.id).order_by(Member.id))).scalars())
    for index in range(len(members), group.size):
        member = Member(group_id=group.id, name=f'Member {index + 1}', age_band='unknown', journey_state='planned')
        db.add(member)
        members.append(member)
    await db.flush()
    return members

async def apply_event(db, group, event, members):
    selected = [m for m in members if m.id in event.member_ids]
    applied = False
    for member in selected:
        # Arrival order cannot reverse a return; exited is terminal.
        if member.journey_state == 'exited': continue
        if member.last_visit_at and utc(event.client_ts) < utc(member.last_visit_at): continue
        if event.direction == 'outbound' and member.journey_state in ('returning','exit_pending'): continue
        # A self report cannot supersede a same-time staff observation.
        if member.last_visit_at and utc(event.client_ts) == utc(member.last_visit_at) and member.confirmation_source == 'volunteer' and event.source != 'volunteer': continue
        member.journey_state = ('exited' if event.source == 'volunteer' else 'exit_pending') if event.direction == 'exit' else event.direction
        member.last_visit_at = event.client_ts
        member.last_checkpoint_id = event.checkpoint_id
        member.confirmation_source = event.source
        applied = True
    event.state_applied = applied
    states = {m.journey_state for m in members}
    if states == {'exited'}: group.status = 'completed'
    elif len(states) > 1: group.status = 'split'
    elif states <= {'returning','exit_pending'}: group.status = 'returning'
    elif states == {'planned'}: group.status = 'planned'
    else: group.status = 'active'
    if not group.started_at: group.started_at = event.client_ts
