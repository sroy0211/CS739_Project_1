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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rkvstore.proto\x12\x07kvstore\"\x19\n\nGetRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\"<\n\x0bGetResponse\x12\r\n\x05value\x18\x01 \x01(\t\x12\r\n\x05\x66ound\x18\x02 \x01(\x08\x12\x0f\n\x07version\x18\x03 \x01(\x04\"9\n\nPutRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\x04\"J\n\x0bPutResponse\x12\x11\n\told_value\x18\x01 \x01(\t\x12\x17\n\x0fold_value_found\x18\x02 \x01(\x08\x12\x0f\n\x07version\x18\x03 \x01(\x04\"\x1c\n\rDeleteRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\"!\n\x0e\x44\x65leteResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x1f\n\x0f\x42\x61tchGetRequest\x12\x0c\n\x04keys\x18\x01 \x03(\t\"\x91\x01\n\x10\x42\x61tchGetResponse\x12\x37\n\x07results\x18\x01 \x03(\x0b\x32&.kvstore.BatchGetResponse.ResultsEntry\x1a\x44\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.kvstore.GetResponse:\x02\x38\x01\"\x80\x01\n\x0f\x42\x61tchPutRequest\x12;\n\nkey_values\x18\x01 \x03(\x0b\x32\'.kvstore.BatchPutRequest.KeyValuesEntry\x1a\x30\n\x0eKeyValuesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\x91\x01\n\x10\x42\x61tchPutResponse\x12\x37\n\x07results\x18\x01 \x03(\x0b\x32&.kvstore.BatchPutResponse.ResultsEntry\x1a\x44\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.kvstore.PutResponse:\x02\x38\x01\",\n\nDieRequest\x12\r\n\x05\x63lean\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"/\n\x0b\x44ieResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\r\n\x0bPingRequest\" \n\x0cPingResponse\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"&\n\x11UpdateTailRequest\x12\x11\n\ttail_port\x18\x01 \x01(\x05\"%\n\x12UpdateTailResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"!\n\x0eGetHeadRequest\x12\x0f\n\x07replace\x18\x01 \x01(\x08\"1\n\x0fGetHeadResponse\x12\x0c\n\x04port\x18\x01 \x01(\x05\x12\x10\n\x08hostname\x18\x02 \x01(\t\"!\n\x0eGetTailRequest\x12\x0f\n\x07replace\x18\x01 \x01(\x08\"1\n\x0fGetTailResponse\x12\x0c\n\x04port\x18\x01 \x01(\x05\x12\x10\n\x08hostname\x18\x02 \x01(\t\"\'\n\x13GetHeartBeatRequest\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"(\n\x14GetHeartBeatResponse\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\x32\x93\x05\n\x07KVStore\x12\x30\n\x03Get\x12\x13.kvstore.GetRequest\x1a\x14.kvstore.GetResponse\x12\x30\n\x03Put\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse\x12\x39\n\x06\x44\x65lete\x12\x16.kvstore.DeleteRequest\x1a\x17.kvstore.DeleteResponse\x12?\n\x08\x42\x61tchGet\x12\x18.kvstore.BatchGetRequest\x1a\x19.kvstore.BatchGetResponse\x12?\n\x08\x42\x61tchPut\x12\x18.kvstore.BatchPutRequest\x1a\x19.kvstore.BatchPutResponse\x12\x36\n\tPutToNext\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse\x12\x30\n\x03\x44ie\x12\x13.kvstore.DieRequest\x1a\x14.kvstore.DieResponse\x12\x33\n\x04Ping\x12\x14.kvstore.PingRequest\x1a\x15.kvstore.PingResponse\x12\x45\n\nUpdateTail\x12\x1a.kvstore.UpdateTailRequest\x1a\x1b.kvstore.UpdateTailResponse\x12\x45\n\nUpdateHead\x12\x1a.kvstore.UpdateTailRequest\x1a\x1b.kvstore.UpdateTailResponse\x12:\n\rForwardToNext\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse2\xd5\x01\n\nMasterNode\x12<\n\x07GetHead\x12\x17.kvstore.GetHeadRequest\x1a\x18.kvstore.GetHeadResponse\x12<\n\x07GetTail\x12\x17.kvstore.GetTailRequest\x1a\x18.kvstore.GetTailResponse\x12K\n\x0cGetHeartBeat\x12\x1c.kvstore.GetHeartBeatRequest\x1a\x1d.kvstore.GetHeartBeatResponseb\x06proto3')

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
  _globals['_GETREQUEST']._serialized_start=26
  _globals['_GETREQUEST']._serialized_end=51
  _globals['_GETRESPONSE']._serialized_start=53
  _globals['_GETRESPONSE']._serialized_end=113
  _globals['_PUTREQUEST']._serialized_start=115
  _globals['_PUTREQUEST']._serialized_end=172
  _globals['_PUTRESPONSE']._serialized_start=174
  _globals['_PUTRESPONSE']._serialized_end=248
  _globals['_DELETEREQUEST']._serialized_start=250
  _globals['_DELETEREQUEST']._serialized_end=278
  _globals['_DELETERESPONSE']._serialized_start=280
  _globals['_DELETERESPONSE']._serialized_end=313
  _globals['_BATCHGETREQUEST']._serialized_start=315
  _globals['_BATCHGETREQUEST']._serialized_end=346
  _globals['_BATCHGETRESPONSE']._serialized_start=349
  _globals['_BATCHGETRESPONSE']._serialized_end=494
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_start=426
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_end=494
  _globals['_BATCHPUTREQUEST']._serialized_start=497
  _globals['_BATCHPUTREQUEST']._serialized_end=625
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_start=577
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_end=625
  _globals['_BATCHPUTRESPONSE']._serialized_start=628
  _globals['_BATCHPUTRESPONSE']._serialized_end=773
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_start=705
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_end=773
  _globals['_DIEREQUEST']._serialized_start=775
  _globals['_DIEREQUEST']._serialized_end=819
  _globals['_DIERESPONSE']._serialized_start=821
  _globals['_DIERESPONSE']._serialized_end=868
  _globals['_PINGREQUEST']._serialized_start=870
  _globals['_PINGREQUEST']._serialized_end=883
  _globals['_PINGRESPONSE']._serialized_start=885
  _globals['_PINGRESPONSE']._serialized_end=917
  _globals['_UPDATETAILREQUEST']._serialized_start=919
  _globals['_UPDATETAILREQUEST']._serialized_end=957
  _globals['_UPDATETAILRESPONSE']._serialized_start=959
  _globals['_UPDATETAILRESPONSE']._serialized_end=996
  _globals['_GETHEADREQUEST']._serialized_start=998
  _globals['_GETHEADREQUEST']._serialized_end=1031
  _globals['_GETHEADRESPONSE']._serialized_start=1033
  _globals['_GETHEADRESPONSE']._serialized_end=1082
  _globals['_GETTAILREQUEST']._serialized_start=1084
  _globals['_GETTAILREQUEST']._serialized_end=1117
  _globals['_GETTAILRESPONSE']._serialized_start=1119
  _globals['_GETTAILRESPONSE']._serialized_end=1168
  _globals['_GETHEARTBEATREQUEST']._serialized_start=1170
  _globals['_GETHEARTBEATREQUEST']._serialized_end=1209
  _globals['_GETHEARTBEATRESPONSE']._serialized_start=1211
  _globals['_GETHEARTBEATRESPONSE']._serialized_end=1251
  _globals['_KVSTORE']._serialized_start=1254
  _globals['_KVSTORE']._serialized_end=1913
  _globals['_MASTERNODE']._serialized_start=1916
  _globals['_MASTERNODE']._serialized_end=2129
# @@protoc_insertion_point(module_scope)
