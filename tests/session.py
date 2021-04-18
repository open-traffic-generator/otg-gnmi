import re
import sys
import os
import logging
import time
import grpc 
from otg_gnmi.autogen import gnmi_pb2, gnmi_pb2_grpc
from tests.utils.settings import *
from otg_gnmi.common.utils import *

'''
python3 -m tests.session --submode 1 --encoding 2 "/port_metrics[name=P1]" "/flow_metrics[name=F1]" "/bgpv4_metrics[name=BGP Peer 1]" "/flow_metrics[name=F2]"
python3 -m tests.session --server 10.72.47.36:50051 --submode 1 --encoding 2 "/port_metrics[name=P1]" "/flow_metrics[name=F1]" "/bgpv4_metrics[name=BGP Router 1]" "/flow_metrics[name=F2]"

'--submode' --> [TARGET_DEFINED, ON_CHANGE, SAMPLE]
'--mode' --> [STREAM, ONCE, POLL]
'--encoding' --> [JSON, BYTES, PROTO, ASCII, JSON_IETF]
'''

class Session(object):

	def __init__(self):
		self.logfile = init_logging('gNMIClient')
		self.logger = logging.getLogger(self.logfile)
		self.options = self.init_options()
		self.channel = self.init_channel()
		self.stub = self.init_stub()
	
	def init_options(self):
		self.logger.debug("Create gNMI options")
		options = GnmiSettings()
		return options

	def is_secure(self):
		if len(self.options.tls) == 0 and len(self.options.cert) == 0:
			return False
		return True

	def init_channel(self):	
		self.logger.info("Create gNMI channel")
		channel = None
		self.logger.info('Options: %s', self.options.to_string())
		if self.is_secure():
			self.logger.info("Create SSL Channel [connection: %s]", self.options.server)
			if self.options.cert:
				cred = grpc.ssl_channel_credentials(root_certificates=open(self.options.cert).read())
				opts = []
				if self.options.altName:
					opts.append(('grpc.ssl_target_name_override', self.options.altName,))
				if self.options.noHostCheck:
					self.logger.error('Disable server name verification against TLS cert is not yet supported!')
					# TODO: Clarify how to setup gRPC with SSLContext using check_hostname:=False

				channel = grpc.secure_channel(self.options.server, cred, opts)
			else:
				self.logger.error('Disable cert validation against root certificate (InsecureSkipVerify) is not yet supported!')
				# TODO: Clarify how to setup gRPC with SSLContext using verify_mode:=CERT_NONE

				cred = grpc.ssl_channel_credentials(root_certificates=None, private_key=None, certificate_chain=None)
				channel = grpc.secure_channel(self.options.server, cred)

		else:
			self.logger.info("Create insecure Channel")
			channel = grpc.insecure_channel(self.options.server)
			
		return channel
	
	def init_stub(self):
		self.logger.debug("Create gNMI stub")
		stub = gnmi_pb2_grpc.gNMIStub(self.channel)
		return stub	

	def capabilites(self):
		
		result = True
		self.logger.info('Sending CapabilityRequest')
		try:
			request = gnmi_pb2.CapabilityRequest()
			responses = self.stub.Capabilities(request, metadata=self.options.metadata)
			self.logger.info('CapabilityRequest Response: %s', responses)
			if respose != None and response.error.code == grpc.StatusCode.UNIMPLEMENTED:
				result = False
    	
		except KeyboardInterrupt:
			self.logger	.info("Stopped by user")
			result = False

		except grpc.RpcError as x:
			self.logger.error("RPC Error: %s", x.details)
			result = False

		except Exception as err:
			self.logger.error("Excepion: s", err)
			result = False

		return result

	def get(self):
		
		result = True
		self.logger.info('Sending GetRequest')
		try:
			request = gnmi_pb2.GetRequest()
			responses = self.stub.Get(request, metadata=self.options.metadata)
			self.logger.info('GetRequest Response: %s', responses)
			if respose != None and response.error.code == grpc.StatusCode.UNIMPLEMENTED:
				result = False
    	
		except KeyboardInterrupt:
			self.logger	.info("Stopped by user")
			result = False

		except grpc.RpcError as x:
			self.logger.error("RPC Error: %s", x.details)
			result = False

		except Exception as err:
			self.logger.error("Excepion: s", err)
			result = False

		return result


	def set(self):
		
		result = True
		self.logger.info('Sending SetRequest')
		try:
			path = gnmi_pb2.Path(elem=[                
				gnmi_pb2.PathElem(name='val', key={'name': 'setup_test'})
			])
			update = gnmi_pb2.Update(path=path, val=gnmi_pb2.TypedValue(json_val=json.dumps({'name': 'setup_test'}).encode("utf-8")))
			updates = []
			updates.append(update)
			request = gnmi_pb2.SetRequest(update=updates)			
			responses = self.stub.Get(request, metadata=self.options.metadata)
			self.logger.info('SetRequest Response: %s', responses)
			if respose != None and response.error.code == grpc.StatusCode.UNIMPLEMENTED:
				result = False
    	
		except KeyboardInterrupt:
			self.logger	.info("Stopped by user")
			result = False

		except grpc.RpcError as x:
			self.logger.error("RPC Error: %s", x.details)
			result = False

		except Exception as err:
			self.logger.error("Excepion: s", err)
			result = False

		return result

	def subscribe(self):
		
		result = True
		req_iterator = generate_subscription_request(self.options)		
		
		start = 0
		secs = 0
		upd_cnt = 0
		resp_cnt = 0
		try:
			self.logger.info ('Sending SubscribeRequest: %s', req_iterator) 
			#responses = self.stub.Subscribe(req_iterator, self.options.timeout, metadata=self.options.metadata)
			responses = self.stub.Subscribe(req_iterator, None, metadata=self.options.metadata)
			res_idx = 0 
			for response in responses:
				
				self.logger.info('Response[%s]: %s', res_idx, response)
				res_idx = res_idx + 1
				
				if response.HasField('error'):
					self.logger.error('gNMI Error Code %s, Error Message: %s', 
						str(response.error.code), str(response.error.message))

				elif response.HasField('sync_response'):
					self.logger.debug('Sync Response received\n'+str(response))
					secs += time.time() - start
					start = 0
					if self.options.stats:
						self.logger.info("Total Messages: %d [Rate: %5.0f], Total Updates: %d [Rate: %5.0f], Total Time: %1.2f secs", 
							resp_cnt, resp_cnt/secs, upd_cnt, upd_cnt/secs, secs)						
				
				elif response.HasField('update'):
					if start==0:
						start=time.time()
					resp_cnt += 1
					upd_cnt += len(response.update.update)
					if not self.options.stats:
						self.logger.info('Update received\n'+str(response))
				else:
					self.logger.error('Received unknown response: %s', str(response))

				if self.options.is_done(upd_cnt):
					self.logger.info('Completed, exiting now.\n')
					break

		except KeyboardInterrupt:
			self.logger	.info("Stopped by user")
			result = False

		except grpc.RpcError as x:
			self.logger.error("RPC Error: %s", x.details)
			result = False

		except Exception as err:
			self.logger.error("Excepion: s", err)
			result = False

		return result

if __name__ == '__main__':
	sessoin = Session()
	sessoin.subscribe()