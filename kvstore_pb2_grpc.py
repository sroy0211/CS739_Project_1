# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import kvstore_pb2 as kvstore__pb2


class KVStoreStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Get = channel.unary_unary(
                '/kvstore.KVStore/Get',
                request_serializer=kvstore__pb2.GetRequest.SerializeToString,
                response_deserializer=kvstore__pb2.GetResponse.FromString,
                )
        self.Put = channel.unary_unary(
                '/kvstore.KVStore/Put',
                request_serializer=kvstore__pb2.PutRequest.SerializeToString,
                response_deserializer=kvstore__pb2.PutResponse.FromString,
                )
        self.Delete = channel.unary_unary(
                '/kvstore.KVStore/Delete',
                request_serializer=kvstore__pb2.DeleteRequest.SerializeToString,
                response_deserializer=kvstore__pb2.DeleteResponse.FromString,
                )
        self.BatchGet = channel.unary_unary(
                '/kvstore.KVStore/BatchGet',
                request_serializer=kvstore__pb2.BatchGetRequest.SerializeToString,
                response_deserializer=kvstore__pb2.BatchGetResponse.FromString,
                )
        self.BatchPut = channel.unary_unary(
                '/kvstore.KVStore/BatchPut',
                request_serializer=kvstore__pb2.BatchPutRequest.SerializeToString,
                response_deserializer=kvstore__pb2.BatchPutResponse.FromString,
                )
        self.PutToNext = channel.unary_unary(
                '/kvstore.KVStore/PutToNext',
                request_serializer=kvstore__pb2.PutRequest.SerializeToString,
                response_deserializer=kvstore__pb2.PutResponse.FromString,
                )
        self.Die = channel.unary_unary(
                '/kvstore.KVStore/Die',
                request_serializer=kvstore__pb2.DieRequest.SerializeToString,
                response_deserializer=kvstore__pb2.DieResponse.FromString,
                )
        self.Ping = channel.unary_unary(
                '/kvstore.KVStore/Ping',
                request_serializer=kvstore__pb2.PingRequest.SerializeToString,
                response_deserializer=kvstore__pb2.PingResponse.FromString,
                )
        self.UpdateTail = channel.unary_unary(
                '/kvstore.KVStore/UpdateTail',
                request_serializer=kvstore__pb2.UpdateTailRequest.SerializeToString,
                response_deserializer=kvstore__pb2.UpdateTailResponse.FromString,
                )
        self.UpdateHead = channel.unary_unary(
                '/kvstore.KVStore/UpdateHead',
                request_serializer=kvstore__pb2.UpdateHeadRequest.SerializeToString,
                response_deserializer=kvstore__pb2.UpdateHeadResponse.FromString,
                )
        self.ForwardToNext = channel.unary_unary(
                '/kvstore.KVStore/ForwardToNext',
                request_serializer=kvstore__pb2.PutRequest.SerializeToString,
                response_deserializer=kvstore__pb2.PutResponse.FromString,
                )


class KVStoreServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Get(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Put(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BatchGet(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BatchPut(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PutToNext(self, request, context):
        """To forward Put requests to the next node in the chain
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Die(self, request, context):
        """New Die RPC method
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Ping(self, request, context):
        """New Ping RPC method
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateTail(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateHead(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ForwardToNext(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_KVStoreServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Get': grpc.unary_unary_rpc_method_handler(
                    servicer.Get,
                    request_deserializer=kvstore__pb2.GetRequest.FromString,
                    response_serializer=kvstore__pb2.GetResponse.SerializeToString,
            ),
            'Put': grpc.unary_unary_rpc_method_handler(
                    servicer.Put,
                    request_deserializer=kvstore__pb2.PutRequest.FromString,
                    response_serializer=kvstore__pb2.PutResponse.SerializeToString,
            ),
            'Delete': grpc.unary_unary_rpc_method_handler(
                    servicer.Delete,
                    request_deserializer=kvstore__pb2.DeleteRequest.FromString,
                    response_serializer=kvstore__pb2.DeleteResponse.SerializeToString,
            ),
            'BatchGet': grpc.unary_unary_rpc_method_handler(
                    servicer.BatchGet,
                    request_deserializer=kvstore__pb2.BatchGetRequest.FromString,
                    response_serializer=kvstore__pb2.BatchGetResponse.SerializeToString,
            ),
            'BatchPut': grpc.unary_unary_rpc_method_handler(
                    servicer.BatchPut,
                    request_deserializer=kvstore__pb2.BatchPutRequest.FromString,
                    response_serializer=kvstore__pb2.BatchPutResponse.SerializeToString,
            ),
            'PutToNext': grpc.unary_unary_rpc_method_handler(
                    servicer.PutToNext,
                    request_deserializer=kvstore__pb2.PutRequest.FromString,
                    response_serializer=kvstore__pb2.PutResponse.SerializeToString,
            ),
            'Die': grpc.unary_unary_rpc_method_handler(
                    servicer.Die,
                    request_deserializer=kvstore__pb2.DieRequest.FromString,
                    response_serializer=kvstore__pb2.DieResponse.SerializeToString,
            ),
            'Ping': grpc.unary_unary_rpc_method_handler(
                    servicer.Ping,
                    request_deserializer=kvstore__pb2.PingRequest.FromString,
                    response_serializer=kvstore__pb2.PingResponse.SerializeToString,
            ),
            'UpdateTail': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateTail,
                    request_deserializer=kvstore__pb2.UpdateTailRequest.FromString,
                    response_serializer=kvstore__pb2.UpdateTailResponse.SerializeToString,
            ),
            'UpdateHead': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateHead,
                    request_deserializer=kvstore__pb2.UpdateHeadRequest.FromString,
                    response_serializer=kvstore__pb2.UpdateHeadResponse.SerializeToString,
            ),
            'ForwardToNext': grpc.unary_unary_rpc_method_handler(
                    servicer.ForwardToNext,
                    request_deserializer=kvstore__pb2.PutRequest.FromString,
                    response_serializer=kvstore__pb2.PutResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'kvstore.KVStore', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class KVStore(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Get(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/Get',
            kvstore__pb2.GetRequest.SerializeToString,
            kvstore__pb2.GetResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Put(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/Put',
            kvstore__pb2.PutRequest.SerializeToString,
            kvstore__pb2.PutResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Delete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/Delete',
            kvstore__pb2.DeleteRequest.SerializeToString,
            kvstore__pb2.DeleteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def BatchGet(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/BatchGet',
            kvstore__pb2.BatchGetRequest.SerializeToString,
            kvstore__pb2.BatchGetResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def BatchPut(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/BatchPut',
            kvstore__pb2.BatchPutRequest.SerializeToString,
            kvstore__pb2.BatchPutResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PutToNext(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/PutToNext',
            kvstore__pb2.PutRequest.SerializeToString,
            kvstore__pb2.PutResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Die(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/Die',
            kvstore__pb2.DieRequest.SerializeToString,
            kvstore__pb2.DieResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Ping(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/Ping',
            kvstore__pb2.PingRequest.SerializeToString,
            kvstore__pb2.PingResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateTail(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/UpdateTail',
            kvstore__pb2.UpdateTailRequest.SerializeToString,
            kvstore__pb2.UpdateTailResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateHead(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/UpdateHead',
            kvstore__pb2.UpdateHeadRequest.SerializeToString,
            kvstore__pb2.UpdateHeadResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ForwardToNext(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.KVStore/ForwardToNext',
            kvstore__pb2.PutRequest.SerializeToString,
            kvstore__pb2.PutResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class MasterNodeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetHead = channel.unary_unary(
                '/kvstore.MasterNode/GetHead',
                request_serializer=kvstore__pb2.GetHeadRequest.SerializeToString,
                response_deserializer=kvstore__pb2.GetReplicaResponse.FromString,
                )
        self.GetTail = channel.unary_unary(
                '/kvstore.MasterNode/GetTail',
                request_serializer=kvstore__pb2.GetTailRequest.SerializeToString,
                response_deserializer=kvstore__pb2.GetReplicaResponse.FromString,
                )
        self.GetHeartBeat = channel.unary_unary(
                '/kvstore.MasterNode/GetHeartBeat',
                request_serializer=kvstore__pb2.SendHeartBeatRequest.SerializeToString,
                response_deserializer=kvstore__pb2.SendHeartBeatResponse.FromString,
                )
        self.GetNextInChain = channel.unary_unary(
                '/kvstore.MasterNode/GetNextInChain',
                request_serializer=kvstore__pb2.GetNextInChainRequest.SerializeToString,
                response_deserializer=kvstore__pb2.GetReplicaResponse.FromString,
                )
        self.UpdateTailDone = channel.unary_unary(
                '/kvstore.MasterNode/UpdateTailDone',
                request_serializer=kvstore__pb2.TailUpdated.SerializeToString,
                response_deserializer=kvstore__pb2.Empty.FromString,
                )


class MasterNodeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetHead(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetTail(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetHeartBeat(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetNextInChain(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateTailDone(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MasterNodeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetHead': grpc.unary_unary_rpc_method_handler(
                    servicer.GetHead,
                    request_deserializer=kvstore__pb2.GetHeadRequest.FromString,
                    response_serializer=kvstore__pb2.GetReplicaResponse.SerializeToString,
            ),
            'GetTail': grpc.unary_unary_rpc_method_handler(
                    servicer.GetTail,
                    request_deserializer=kvstore__pb2.GetTailRequest.FromString,
                    response_serializer=kvstore__pb2.GetReplicaResponse.SerializeToString,
            ),
            'GetHeartBeat': grpc.unary_unary_rpc_method_handler(
                    servicer.GetHeartBeat,
                    request_deserializer=kvstore__pb2.SendHeartBeatRequest.FromString,
                    response_serializer=kvstore__pb2.SendHeartBeatResponse.SerializeToString,
            ),
            'GetNextInChain': grpc.unary_unary_rpc_method_handler(
                    servicer.GetNextInChain,
                    request_deserializer=kvstore__pb2.GetNextInChainRequest.FromString,
                    response_serializer=kvstore__pb2.GetReplicaResponse.SerializeToString,
            ),
            'UpdateTailDone': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateTailDone,
                    request_deserializer=kvstore__pb2.TailUpdated.FromString,
                    response_serializer=kvstore__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'kvstore.MasterNode', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class MasterNode(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetHead(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.MasterNode/GetHead',
            kvstore__pb2.GetHeadRequest.SerializeToString,
            kvstore__pb2.GetReplicaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetTail(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.MasterNode/GetTail',
            kvstore__pb2.GetTailRequest.SerializeToString,
            kvstore__pb2.GetReplicaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetHeartBeat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.MasterNode/GetHeartBeat',
            kvstore__pb2.SendHeartBeatRequest.SerializeToString,
            kvstore__pb2.SendHeartBeatResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetNextInChain(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.MasterNode/GetNextInChain',
            kvstore__pb2.GetNextInChainRequest.SerializeToString,
            kvstore__pb2.GetReplicaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateTailDone(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/kvstore.MasterNode/UpdateTailDone',
            kvstore__pb2.TailUpdated.SerializeToString,
            kvstore__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
