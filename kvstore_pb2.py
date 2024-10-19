# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: kvstore.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'kvstore.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rkvstore.proto\x12\x07kvstore\"\x19\n\nGetRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\"M\n\x0bGetResponse\x12\r\n\x05value\x18\x01 \x01(\t\x12\r\n\x05\x66ound\x18\x02 \x01(\x08\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0f\n\x07version\x18\x04 \x01(\x04\"9\n\nPutRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\x04\"[\n\x0bPutResponse\x12\x11\n\told_value\x18\x01 \x01(\t\x12\x17\n\x0fold_value_found\x18\x02 \x01(\x08\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0f\n\x07version\x18\x04 \x01(\x04\"\x1c\n\rDeleteRequest\x12\x0b\n\x03key\x18\x01 \x01(\t\"!\n\x0e\x44\x65leteResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x1f\n\x0f\x42\x61tchGetRequest\x12\x0c\n\x04keys\x18\x01 \x03(\t\"\x91\x01\n\x10\x42\x61tchGetResponse\x12\x37\n\x07results\x18\x01 \x03(\x0b\x32&.kvstore.BatchGetResponse.ResultsEntry\x1a\x44\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.kvstore.GetResponse:\x02\x38\x01\"\x80\x01\n\x0f\x42\x61tchPutRequest\x12;\n\nkey_values\x18\x01 \x03(\x0b\x32\'.kvstore.BatchPutRequest.KeyValuesEntry\x1a\x30\n\x0eKeyValuesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\x91\x01\n\x10\x42\x61tchPutResponse\x12\x37\n\x07results\x18\x01 \x03(\x0b\x32&.kvstore.BatchPutResponse.ResultsEntry\x1a\x44\n\x0cResultsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.kvstore.PutResponse:\x02\x38\x01\",\n\nDieRequest\x12\r\n\x05\x63lean\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"/\n\x0b\x44ieResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\r\n\x0bPingRequest\" \n\x0cPingResponse\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"&\n\x11UpdateTailRequest\x12\x11\n\ttail_port\x18\x01 \x01(\x05\"%\n\x12UpdateTailResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"!\n\x0eGetHeadRequest\x12\x0f\n\x07replace\x18\x01 \x01(\x08\"!\n\x0eGetTailRequest\x12\x0f\n\x07replace\x18\x01 \x01(\x08\"E\n\x12GetReplicaResponse\x12\x0c\n\x04port\x18\x01 \x01(\x05\x12\x10\n\x08hostname\x18\x02 \x01(\t\x12\x0f\n\x07success\x18\x03 \x01(\x08\"\'\n\x13GetHeartBeatRequest\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"(\n\x14GetHeartBeatResponse\x12\x10\n\x08is_alive\x18\x01 \x01(\x08\"%\n\x15GetNextInChainRequest\x12\x0c\n\x04port\x18\x01 \x01(\x05\x32\x93\x05\n\x07KVStore\x12\x30\n\x03Get\x12\x13.kvstore.GetRequest\x1a\x14.kvstore.GetResponse\x12\x30\n\x03Put\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse\x12\x39\n\x06\x44\x65lete\x12\x16.kvstore.DeleteRequest\x1a\x17.kvstore.DeleteResponse\x12?\n\x08\x42\x61tchGet\x12\x18.kvstore.BatchGetRequest\x1a\x19.kvstore.BatchGetResponse\x12?\n\x08\x42\x61tchPut\x12\x18.kvstore.BatchPutRequest\x1a\x19.kvstore.BatchPutResponse\x12\x36\n\tPutToNext\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse\x12\x30\n\x03\x44ie\x12\x13.kvstore.DieRequest\x1a\x14.kvstore.DieResponse\x12\x33\n\x04Ping\x12\x14.kvstore.PingRequest\x1a\x15.kvstore.PingResponse\x12\x45\n\nUpdateTail\x12\x1a.kvstore.UpdateTailRequest\x1a\x1b.kvstore.UpdateTailResponse\x12\x45\n\nUpdateHead\x12\x1a.kvstore.UpdateTailRequest\x1a\x1b.kvstore.UpdateTailResponse\x12:\n\rForwardToNext\x12\x13.kvstore.PutRequest\x1a\x14.kvstore.PutResponse2\xaa\x02\n\nMasterNode\x12?\n\x07GetHead\x12\x17.kvstore.GetHeadRequest\x1a\x1b.kvstore.GetReplicaResponse\x12?\n\x07GetTail\x12\x17.kvstore.GetTailRequest\x1a\x1b.kvstore.GetReplicaResponse\x12K\n\x0cGetHeartBeat\x12\x1c.kvstore.GetHeartBeatRequest\x1a\x1d.kvstore.GetHeartBeatResponse\x12M\n\x0eGetNextInChain\x12\x1e.kvstore.GetNextInChainRequest\x1a\x1b.kvstore.GetReplicaResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kvstore_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._loaded_options = None
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_options = b'8\001'
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._loaded_options = None
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_options = b'8\001'
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._loaded_options = None
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_options = b'8\001'
  _globals['_GETREQUEST']._serialized_start=26
  _globals['_GETREQUEST']._serialized_end=51
  _globals['_GETRESPONSE']._serialized_start=53
  _globals['_GETRESPONSE']._serialized_end=130
  _globals['_PUTREQUEST']._serialized_start=132
  _globals['_PUTREQUEST']._serialized_end=189
  _globals['_PUTRESPONSE']._serialized_start=191
  _globals['_PUTRESPONSE']._serialized_end=282
  _globals['_DELETEREQUEST']._serialized_start=284
  _globals['_DELETEREQUEST']._serialized_end=312
  _globals['_DELETERESPONSE']._serialized_start=314
  _globals['_DELETERESPONSE']._serialized_end=347
  _globals['_BATCHGETREQUEST']._serialized_start=349
  _globals['_BATCHGETREQUEST']._serialized_end=380
  _globals['_BATCHGETRESPONSE']._serialized_start=383
  _globals['_BATCHGETRESPONSE']._serialized_end=528
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_start=460
  _globals['_BATCHGETRESPONSE_RESULTSENTRY']._serialized_end=528
  _globals['_BATCHPUTREQUEST']._serialized_start=531
  _globals['_BATCHPUTREQUEST']._serialized_end=659
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_start=611
  _globals['_BATCHPUTREQUEST_KEYVALUESENTRY']._serialized_end=659
  _globals['_BATCHPUTRESPONSE']._serialized_start=662
  _globals['_BATCHPUTRESPONSE']._serialized_end=807
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_start=739
  _globals['_BATCHPUTRESPONSE_RESULTSENTRY']._serialized_end=807
  _globals['_DIEREQUEST']._serialized_start=809
  _globals['_DIEREQUEST']._serialized_end=853
  _globals['_DIERESPONSE']._serialized_start=855
  _globals['_DIERESPONSE']._serialized_end=902
  _globals['_PINGREQUEST']._serialized_start=904
  _globals['_PINGREQUEST']._serialized_end=917
  _globals['_PINGRESPONSE']._serialized_start=919
  _globals['_PINGRESPONSE']._serialized_end=951
  _globals['_UPDATETAILREQUEST']._serialized_start=953
  _globals['_UPDATETAILREQUEST']._serialized_end=991
  _globals['_UPDATETAILRESPONSE']._serialized_start=993
  _globals['_UPDATETAILRESPONSE']._serialized_end=1030
  _globals['_GETHEADREQUEST']._serialized_start=1032
  _globals['_GETHEADREQUEST']._serialized_end=1065
  _globals['_GETTAILREQUEST']._serialized_start=1067
  _globals['_GETTAILREQUEST']._serialized_end=1100
  _globals['_GETREPLICARESPONSE']._serialized_start=1102
  _globals['_GETREPLICARESPONSE']._serialized_end=1171
  _globals['_GETHEARTBEATREQUEST']._serialized_start=1173
  _globals['_GETHEARTBEATREQUEST']._serialized_end=1212
  _globals['_GETHEARTBEATRESPONSE']._serialized_start=1214
  _globals['_GETHEARTBEATRESPONSE']._serialized_end=1254
  _globals['_GETNEXTINCHAINREQUEST']._serialized_start=1256
  _globals['_GETNEXTINCHAINREQUEST']._serialized_end=1293
  _globals['_KVSTORE']._serialized_start=1296
  _globals['_KVSTORE']._serialized_end=1955
  _globals['_MASTERNODE']._serialized_start=1958
  _globals['_MASTERNODE']._serialized_end=2256
# @@protoc_insertion_point(module_scope)
