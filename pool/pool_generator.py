import circuit
from circuit import BooleanCircuit
import json
from util import specialDecryption, specialEncryption, generate_key
import os
import random
from pool_util import DELTA, xor_hex, generate_gate, fill_pool

# Generate basic bucket structure for that both parties agreed
class PoolGenerator(BooleanCircuit):
	def __init__(self, from_json=None):
		# The superclass constructor initializes the gates and topological sorting
		super(PoolGenerator,self).__init__(from_json=from_json)

	def garble(self):
		# Generate new wire labels
		self.wire_labels = {} # maps wire id to {"0":label0 ,"1": label1}

		# Encode all bucket wires
		for wid in self.wires:
			key_0 = generate_key().encode('hex')
			key_1 = xor_hex(key_0, DELTA)
			self.wire_labels[wid] = [key_0, key_1] # Based on XOR-free structure

		B = 10
		T = len(self.gates) * B
		pool = []
		self.pool = fill_pool(pool, T+100)

	def output(self, outfile, inputs=None, debug=True):
		# Save as a JSON file, with wire lables for debugging
		obj = {}
		gates = {}
		pool = {}
		for gid,gate in self.gates.iteritems():
			gates[gid] = gate.copy() # Copy the gate object directly
		obj["gates"] = gates
        
		# Copy the pool
		for pid, piece in enumerate(self.pool):
			pool[pid] = piece
		obj["pool"] = pool

		# Output wire labels in debug mode
		if debug: 
			obj["wire_labels"] = self.wire_labels

		if inputs is not None:
			print 'Input available'
			assert len(inputs) == len(self.input_wires)
			input_labels = {}
			for wid,v in inputs.iteritems():
				assert v in (0,1)
				input_labels[wid] = self.wire_labels[wid][v]
				obj["inputs"] = input_labels

		with open(outfile,"w") as f:
			json.dump(obj, f, indent=4)
		print 'Wrote garbled circuit', outfile

	def second_phase_output(self, outfile, wire_labels, from_json=None, inputs=None):
		self.wire_labels = wire_labels
		if from_json is not None:
			self.pool = from_json['pool']
			gates = from_json["gates"]
			self.gates = gates
			for bid, bucket in self.gates.iteritems():
				w0 = bucket['inp'][0]
				w1 = bucket['inp'][1]
				w2 = bucket['out'][0]
				w0_label = self.wire_labels[w0][0]
				# print w0_label
				w1_label = self.wire_labels[w1][0]
				w2_label = self.wire_labels[w2][0]

				for tid, table in bucket["tables"].iteritems():
					table['inp_lable'] = {}
					table['inp_lable'][w0] = table['inp'][0]
					table['inp_lable'][w1] = table['inp'][1]
					table['out_lable'] = {}
					table['out_lable'][w2] = table['out'][0]
					table['inp_d'] = {}
					table['inp_d'][w0] = xor_hex(table['inp'][0], w0_label)
					table['inp_d'][w1] = xor_hex(table['inp'][1], w1_label)
					table['out_d'] = {}
					table['out_d'][w2] = xor_hex(table['out'][0], w2_label)

			obj = {}
			gates = {}
			pool = {}
			for gid,gate in self.gates.iteritems():
				gates[gid] = gate.copy() # Copy the gate object directly
			obj["gates"] = gates
			obj['pool'] = self.pool
	        

			# Output wire labels in debug mode
			# if debug: 
			# 	obj["wire_labels"] = self.wire_labels

		if inputs is not None:
			print 'Input available'
			assert len(inputs) == len(self.input_wires)
			input_labels = {}
			for wid,v in inputs.iteritems():
				assert v in (0,1)
				input_labels[wid] = self.wire_labels[wid][v]
				obj["inputs"] = input_labels

		with open(outfile,"w") as f:
			json.dump(obj, f, indent=4)
		print 'Wrote garbled circuit', outfile


if __name__ == '__main__':
	import sys
	if len(sys.argv) < 4:
		print "usage: python generator.py <circuit.json> <outfile.json> phase_num <extra_file.json>"
		sys.exit(1)

	filename = sys.argv[1]
	obj = json.load(open(filename))

	# Build init output
	if sys.argv[3] == '1':
		# Circuit
		c = PoolGenerator(from_json=obj)
		print 'Circuit loaded: %d gates, %d input wires, %d output_wires, %d total' \
			% (len(c.gates), len(c.input_wires), len(c.output_wires), len(c.wires))

		# Generate the circuit
		c.garble()

		# Load the inputs
		inputs = obj["inputs"]

		# Write the output
		outfile = sys.argv[2]
		c.output(outfile, inputs)

	if sys.argv[3] == '2':
		c = PoolGenerator(from_json=obj)
		wire_labels = obj['wire_labels']
		# c.garble()
		outfile = sys.argv[2]
		extra_file = json.load(open(sys.argv[4]))
		c.second_phase_output(outfile, wire_labels, from_json=extra_file)
