import type { Principal } from '@icp-sdk/core/principal';
import type { ActorMethod } from '@icp-sdk/core/agent';
import type { IDL } from '@icp-sdk/core/candid';

export interface _SERVICE {
  'getInfo' : ActorMethod<[], { 'tagline' : string, 'appName' : string }>,
  'process_doodle' : ActorMethod<[Uint8Array | number[]], string>,
}
export declare const idlFactory: IDL.InterfaceFactory;
export declare const init: (args: { IDL: typeof IDL }) => IDL.Type[];
