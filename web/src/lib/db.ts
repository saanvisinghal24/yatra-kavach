import Dexie, { Table } from 'dexie';

export interface LocalGroup {
  code: string;
  yatraId: number;
  routeId: number;
  routeName: string;
  leaderName: string;
  leaderPhone: string;
  emergencyName: string;
  emergencyPhone: string;
  size: number;
  passToken: string;
  cancellationToken?: string;
  tripStatus?: string;
  createdAt: string;
  synced: boolean;
}

export interface LocalCheckin {
  id: string; // Client UUID
  groupCode: string;
  checkpointId: number;
  checkpointName: string;
  source: 'self' | 'volunteer';
  headcount: number;
  clientTs: string;
  clockSkewS: number;
  lat?: number;
  lon?: number;
  status: 'pending' | 'synced' | 'invalid';
  invalidReason?: string;
  syncedAt?: string;
  signedQr?: string;
  direction?: 'outbound' | 'returning' | 'exit';
  memberIds?: number[];
}

export class YatraKavachDB extends Dexie {
  outbox!: Table<{id:string;path:string;payload:any;status:string},string>;
  groups!: Table<LocalGroup, string>;
  checkins!: Table<LocalCheckin, string>;

  constructor() {
    super('YatraKavachDB');
    this.version(2).stores({
      outbox: "id, status",
      groups: 'code, yatraId, routeId, synced',
      checkins: 'id, groupCode, checkpointId, status, clientTs'
    });
  }
}

export const db = new YatraKavachDB();
