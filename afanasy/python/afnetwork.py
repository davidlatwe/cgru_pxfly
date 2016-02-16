#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import socket
import sys

import cgruconfig
import cgruutils


def genHeader(data_size):
	"""Missing DocString

	:param data_size:
	:return:
	"""
	data = 'AFANASY %s JSON' % data_size
	return bytearray(data, 'utf-8')


def sendServer(data, receive=True, verbose=False):
	"""Missing DocString

	:param receive:
	:param verbose:
	:return:
	"""
	size = len(data)
	header = genHeader(size)
	data = header + bytearray(data, 'utf-8')
	datalen = len(data)
	# return True, None

	host = cgruconfig.VARS['af_servername']
	port = cgruconfig.VARS['af_serverport']

	s = None
	err_msg = ''
	reslist = []

	try:
		reslist = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
									 socket.SOCK_STREAM)
	except:  # TODO: Too broad exception clause
		print('Can`t solve "%s":' % host + str(sys.exc_info()[1]))

	for res in reslist:
		af, socktype, proto, canonname, sa = res
		if verbose:
			print('Trying to connect to "%s"' % str(sa[0]))
		try:
			s = socket.socket(af, socktype, proto)
		except:  # TODO: Too broad exception clause
			if err_msg != '':
				err_msg += '\n'
			err_msg += str(sa[0]) + ' : ' + str(sys.exc_info()[1])
			s = None
			continue
		try:
			s.connect(sa)
		except:  # TODO: Too broad exception clause
			if err_msg != '':
				err_msg += '\n'
			err_msg += str(sa[0]) + ' : ' + str(sys.exc_info()[1])
			s.close()
			s = None
			continue
		break

	if s is None:
		print('Could not open socket.')
		print(err_msg)
		return False, None

	if verbose:
		print('afnetwork.sendServer: send %d bytes' % datalen)

	# s.sendall( data) #<<< !!! May not work !!!!

	total_send = 0
	while total_send < len(data):
		sent = s.send(data[total_send:])
		if sent == 0:
			disconnectSocket( s)
			print('Error: Unable send data to socket')
			return False, None
		total_send += sent

	if not receive:
		disconnectSocket( s)
		return True, None


	data = b''
	msg_len = None
	while True:
		buffer = s.recv(4096)

		if not buffer:
			break

		data += buffer

		if msg_len is None:
			dataStr = cgruutils.toStr(data)
			if dataStr.find('AFANASY') != -1 and dataStr.find('JSON') != -1:
				msg_len = dataStr[:dataStr.find('JSON')+4]
				msg_len = len(msg_len) + int(msg_len.split(' ')[1])

		if verbose:
			print('Received %d of %d bytes.' % ( len(data), msg_len))

		if msg_len is not None:
			if len( data) >= msg_len:
				break

	disconnectSocket( s)

	struct = None

	try:
		if not isinstance(data, str):
			data = cgruutils.toStr(data)
		data = data[data.find('JSON')+4:]
		struct = json.loads(data)
	except:  # TODO: Too broad exception clause
		print('afnetwork.py: Received data:')
		print(data)
		print('JSON loads error:')
		print(str(sys.exc_info()[1]))
		struct = None

	return True, struct


def disconnectSocket( i_sd):

	i_sd.close()
