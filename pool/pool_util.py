import circuit
from circuit import BooleanCircuit
import json
from util import specialDecryption, specialEncryption, generate_key
import os
import random

# GLOBAL VARIBLE for XOR-free circuit
DELTA = 'cd1836de66b0fa18b0b58652a6b55e04'

# Define xor hex
def xor_hex(ha, hb):
	return ''.join( chr(ord(a) ^ ord(b)) for (a,b) in zip( ha.decode('hex'), hb.decode('hex') ) ).encode('hex')

# Shuffle function based on knuth-fischer-yates shuffling
def shuffle(a):
    assert type(a) is list
    # TODO: sort a in place, and return None
    n = len(a)
    i = 0
    temp = n
    while temp != 0:
        temp  = temp/16
        i = i+1
    for idx in range(n):
        rand = int(os.urandom(i).encode('hex'), 16)
        while idx+rand >= n:
            rand = int(os.urandom(i).encode('hex'), 16)
        a[idx], a[rand+idx] = a[rand+idx], a[idx]

# Generate a random AND gate
def generate_gate():
	gate = {}
	gate["type"] = "AND"
	w = []
	for i in range(3):
		key_0 = generate_key().encode('hex')
		key_1 = xor_hex(key_0, DELTA)
		w.append([key_0, key_1])
	gate['inp'] = [w[0][0], w[1][0]]
	gate['out'] = [w[2][0]]
	gate['garble_table'] = []
	index = [[0, 0, 0], [0, 1, 0], [1, 0, 0], [1, 1, 1]]
	for i in index:
		key_0 = w[0][i[0]].decode('hex')
		key_1 = w[1][i[1]].decode('hex')
		msg = w[2][i[2]].decode('hex')
		cipher = specialEncryption(key_0, specialEncryption(key_1, msg)).encode('hex')
		gate['garble_table'].append(cipher)
		shuffle(gate['garble_table'])

	return gate

# Fill the pool
def fill_pool(pool, T=100):
	assert len(pool) <= T
	while len(pool) < T:
		pool.append(generate_gate())
	return pool

# For the evaluator to choose gates from the pool to fill the bucket
def fill_bucket(bucket, pool, B=10):
	secure_random = random.SystemRandom()
	for i in range(B):
		key = secure_random.choice(pool.keys())
		bucket[key] = pool[key]
		pool.pop(key)

# Evaluate if a gate is valid
def evaluate_gate(gate):
	key00 = gate['inp'][0].decode('hex')
	key10 = gate['inp'][1].decode('hex')
	key01 = xor_hex(gate['inp'][0], DELTA).decode('hex')
	key11 = xor_hex(gate['inp'][1], DELTA).decode('hex')
	output0 = gate['out'][0]
	output1 = xor_hex(output0, DELTA)
	garbled_table = gate['garble_table']
	for c in garbled_table:
		cipher = c.decode('hex')
		if specialDecryption(key00, cipher) == None:
		    continue
		k = specialDecryption(key00, cipher)
		if specialDecryption(key10, k) == None:
		    continue
		m = specialDecryption(key10, k)
		label = m.encode('hex')
		assert label == output0 or label == output1
	for c in garbled_table:
		cipher = c.decode('hex')
		if specialDecryption(key01, cipher) == None:
		    continue
		k = specialDecryption(key01, cipher)
		if specialDecryption(key10, k) == None:
		    continue
		m = specialDecryption(key10, k)
		label = m.encode('hex')
		assert label == output0 or label == output1
	for c in garbled_table:
		cipher = c.decode('hex')
		if specialDecryption(key00, cipher) == None:
		    continue
		k = specialDecryption(key00, cipher)
		if specialDecryption(key11, k) == None:
		    continue
		m = specialDecryption(key11, k)
		label = m.encode('hex')
		assert label == output0 or label == output1
	for c in garbled_table:
		cipher = c.decode('hex')
		if specialDecryption(key01, cipher) == None:
		    continue
		k = specialDecryption(key01, cipher)
		if specialDecryption(key11, k) == None:
		    continue
		m = specialDecryption(key11, k)
		label = m.encode('hex')
		assert (label == output0 or label == output1), 'Generator is invalid.'

	

if __name__ == '__main__':
	# Test for utility
	generate_gate()
	print "generate_gate is correct"

	pool = []
	fill_pool(pool)
	assert len(pool) == 100
	print "fill_pool is correct"

	bucket = {}
	pool_dict = {}
	for i in range(len(pool)):
		pool_dict[i] = pool[i]
	fill_bucket(bucket, pool_dict)
	print len(bucket), len(pool_dict)
	assert len(bucket) == 10 and len(pool_dict) == 90
	print "fill_bucket is correct"

	evaluate_gate(pool[0])
	print 'evaluate_gate is correct'