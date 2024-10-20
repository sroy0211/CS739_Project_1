# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: kvstore.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rkvstore.proto\x12\x07kvstore\"\x07\n\x05\x45mpty\"\x19\n\nGetRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\"M\n\x0bGetResponse\x12\r\n\x05value\x18\x01 \x01(\t\x12\r\n\x05\x66ound\x18\x02 \x01(\x08\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0f\n\x07version\x18\x04 \x01(\x04\"M\n\nPutRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\x04\x12\x12\n\nis_forward\x18\x04 \x01(\x08\"[\n\x0bPutResponse\x12\x11\n\told_value\x18\x01 \x01(\t\x12\x17\n\x0fold_value_found\x18\x02 \x01(\x08\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0f\n\x07version\x18\x04 \x01(\x04\"\x1c\n\rDeleteRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\"!\n\x0e\x44\x65leteResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x1f\n\x0f\x42\x61tchGetRequest\x12\x0c\n\x04keys\x18\x01 \x03(\t\"\x91\x01\n\x10\x42\x61tchGetResponse\x12\x37\n\x07results\x18\x01 \x03(\x0b\x32&.kvstore.BatchGetResponse.ResultsEntry\x1a\x44\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.kvstore.GetResponse:\x02\x38\x01\"\x80\x01\n\x0f\x42\x61tchPutRequest\x12;\n\nkey_values\x18\x01 \x03(\x0b\x32\'.kvstore.BatchPutRequest.KeyValuesEntry\x1a\x30\n\x0eKeyValuesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\x91\x01\n\x10\x42\x61tchPutResponse\x12\x37\n\x07results\x18\x01 \x03(\x0b\x32&.kvstore.BatchPutResponse.ResultsEntry\x1a\x44\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.kvstore.PutResponse:\x02\x38\x01\",\n\nDieRequest\x12\r\n\x05\x63lean\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"/\n\x0b\x44ieResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\r\n\x0bPingRequest\" \n\x0cPingResponse\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"*\n\x11UpdateTailRequest\x12\x15\n\rnew_tail_port\x18\x01 \x01(\x05\"%\n\x12UpdateTailResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x13\n\x11UpdateHeadRequest\"%\n\x12UpdateHeadResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"$\n\x0bTailUpdated\x12\x15\n\rnew_tail_port\x18\x01 \x01(\x05\"!\n\x0eGetHeadRequest\x12\x0f\n\x07replace\x18\x01 \x01(\x08\"!\n\x0eGetTailRequest\x12\x0f\n\x07replace\x18\x01 \x01(\x08\"E\n\x12GetReplicaResponse\x12\x0c\n\x04port\x18\x01 \x01(\x05\x12\x10\n\x08hostname\x18\x02 \x01(\t\x12\x0f\n\x07success\x18\x03 \x01(\x08\"6\n\x14SendHeartBeatRequest\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\x12\x0c\n\x04port\x18\x02 \x01(\x05\")\n\x15SendHeartBeatResponse\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"%\n\x15GetNextInChainRequest\x12\x0c\n\x04port\x18\x01 \x01(\x05\x32\x93\x05\n\x07KVStore\x12\x30\n\x03Get\x12\x13.kvstore.GetRequest\x1a\x14.kvstore.GetResponse\x12\x30\n\x03Put\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse\x12\x39\n\x06\x44\x65lete\x12\x16.kvstore.DeleteRequest\x1a\x17.kvstore.DeleteResponse\x12?\n\x08\x42\x61tchGet\x12\x18.kvstore.BatchGetRequest\x1a\x19.kvstore.BatchGetResponse\x12?\n\x08\x42\x61tchPut\x12\x18.kvstore.BatchPutRequest\x1a\x19.kvstore.BatchPutResponse\x12\x36\n\tPutToNext\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse\x12\x30\n\x03\x44ie\x12\x13.kvstore.DieRequest\x1a\x14.kvstore.DieResponse\x12\x33\n\x04Ping\x12\x14.kvstore.PingRequest\x1a\x15.kvstore.PingResponse\x12\x45\n\nUpdateTail\x12\x1a.kvstore.UpdateTailRequest\x1a\x1b.kvstore.UpdateTailResponse\x12\x45\n\nUpdateHead\x12\x1a.kvstore.UpdateHeadRequest\x1a\x1b.kvstore.UpdateHeadResponse\x12:\n\rForwardToNext\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse2\x9e\x03\n\nMasterNode\x12?\n\x07GetHead\x12\x17.kvstore.GetHeadRequest\x1a\x1b.kvstore.GetReplicaResponse\x12?\n\x07GetTail\x12\x17.kvstore.GetTailRequest\x1a\x1b.kvstore.GetReplicaResponse\x12N\n\rSendHeartBeat\x12\x1d.kvstore.SendHeartBeatRequest\x1a\x1e.kvstore.SendHeartBeatResponse\x12M\n\x0eGetNextInChain\x12\x1e.kvstore.GetNextInChainRequest\x1a\x1b.kvstore.GetReplicaResponse\x12\x36\n\x0eUpdateTailDone\x12\x14.kvstore.TailUpdated\x1a\x0e.kvstore.Empty\x12\x37\n\tNewTailUp\x12\x1a.kvstore.UpdateTailRequest\x1a\x0e.kvstore.Emptyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kvstore_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _BATCHGETRESPONSE_RESULTSENTRY._options = None
  _BATCHGETRESPONSE_RESULTSENTRY._serialized_options = b'8\001'
  _BATCHPUTREQUEST_KEYVALUESENTRY._options = None
  _BATCHPUTREQUEST_KEYVALUESENTRY._serialized_options = b'8\001'
  _BATCHPUTRESPONSE_RESULTSENTRY._options = None
  _BATCHPUTRESPONSE_RESULTSENTRY._serialized_options = b'8\001'
  _globals['_EMPTY']._serialized_start=26
  _globals['_EMPTY']._serialized_end=33
  _globals['_GETREQUEST']._serialized_start=35
  _globals['_GETREQUEST']._serialized_end=60
  _globals['_GETRESPONSE']._serialized_start=62
  _globals['_GETRESPONSE']._serialized_end=139
  _globals['_PUTREQUEST']._serialized_start=141
  _globals['_PUTREQUEST']._serialized_end=218
  _globals['_PUTRESPONSE']._serialized_start=220
  _globals['_PUTRESPONSE']._serialized_end=311
  _globals['_DELETEREQUEST']._serialized_start=313
  _globals['_DELETEREQUEST']._serialized_end=341
  _globals['_DELETERESPONSE']._serialized_start=343
  _globals['_DELETERESPONSE']._serialized_end=376
  _globals['_BATCHGETREQUEST']._serialized_start=378
  _globals['_BATCHGETREQUEST']._serialized_end=409
  _globals['_BATCHGETRESPONSE']._serialized_start=412
  _globals['_BATCHGETRESPONSE']._serialized_end=557
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_start=489
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_end=557
  _globals['_BATCHPUTREQUEST']._serialized_start=560
  _globals['_BATCHPUTREQUEST']._serialized_end=688
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_start=640
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_end=688
  _globals['_BATCHPUTRESPONSE']._serialized_start=691
  _globals['_BATCHPUTRESPONSE']._serialized_end=836
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_start=768
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_end=836
  _globals['_DIEREQUEST']._serialized_start=838
  _globals['_DIEREQUEST']._serialized_end=882
  _globals['_DIERESPONSE']._serialized_start=884
  _globals['_DIERESPONSE']._serialized_end=931
  _globals['_PINGREQUEST']._serialized_start=933
  _globals['_PINGREQUEST']._serialized_end=946
  _globals['_PINGRESPONSE']._serialized_start=948
  _globals['_PINGRESPONSE']._serialized_end=980
  _globals['_UPDATETAILREQUEST']._serialized_start=982
  _globals['_UPDATETAILREQUEST']._serialized_end=1024
  _globals['_UPDATETAILRESPONSE']._serialized_start=1026
  _globals['_UPDATETAILRESPONSE']._serialized_end=1063
  _globals['_UPDATEHEADREQUEST']._serialized_start=1065
  _globals['_UPDATEHEADREQUEST']._serialized_end=1084
  _globals['_UPDATEHEADRESPONSE']._serialized_start=1086
  _globals['_UPDATEHEADRESPONSE']._serialized_end=1123
  _globals['_TAILUPDATED']._serialized_start=1125
  _globals['_TAILUPDATED']._serialized_end=1161
  _globals['_GETHEADREQUEST']._serialized_start=1163
  _globals['_GETHEADREQUEST']._serialized_end=1196
  _globals['_GETTAILREQUEST']._serialized_start=1198
  _globals['_GETTAILREQUEST']._serialized_end=1231
  _globals['_GETREPLICARESPONSE']._serialized_start=1233
  _globals['_GETREPLICARESPONSE']._serialized_end=1302
  _globals['_SENDHEARTBEATREQUEST']._serialized_start=1304
  _globals['_SENDHEARTBEATREQUEST']._serialized_end=1358
  _globals['_SENDHEARTBEATRESPONSE']._serialized_start=1360
  _globals['_SENDHEARTBEATRESPONSE']._serialized_end=1401
  _globals['_GETNEXTINCHAINREQUEST']._serialized_start=1403
  _globals['_GETNEXTINCHAINREQUEST']._serialized_end=1440
  _globals['_KVSTORE']._serialized_start=1443
  _globals['_KVSTORE']._serialized_end=2102
  _globals['_MASTERNODE']._serialized_start=2105
  _globals['_MASTERNODE']._serialized_end=2519
# @@protoc_insertion_point(module_scope)
