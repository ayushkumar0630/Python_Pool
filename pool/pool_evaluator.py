import circuit
import util
import json
from circuit import BooleanCircuit
from util import specialDecryption, specialEncryption
from pool_util import DELTA, fill_bucket, xor_hex, generate_gate, fill_pool, evaluate_gate

class PoolEvaluator(BooleanCircuit):
	def __init__(self, from_json=None):
	# The superclass constructor initializes the gates and topological sorting
		super(PoolEvaluator,self).__init__(from_json=from_json)

		# What remains is for us to load the garbling tables
		if from_json is not None:

			# Load the garbled tables
			buckets = from_json["gates"]
			input_labels = from_json["inputs"]
			pool = from_json["pool"]

			for bid in self.sorted_gates:
				bucket = buckets[bid]
				tables = {}
				fill_bucket(tables, pool)
				bucket["tables"] = tables

			self.gates = buckets
			self.input_labels = input_labels
			self.pool = pool
			# print len(pool)


	def first_phase_output(self, outfile):
		obj = {}
		gates = {}
		pool = {}
		for gid,gate in self.gates.iteritems():
			gates[gid] = gate.copy() # Copy the gate object directly
		obj["gates"] = gates

		# Copy the pool
		pool = {}
		for pid in self.pool:
			pool[pid] = self.pool[pid]
		obj["pool"] = pool

		# Output wire labels in debug mode
		# if debug: 
		#     obj["wire_labels"] = self.wire_labels

		# if inputs is not None:
		#     print 'Input available'
		#     assert len(inputs) == len(self.input_wires)
		#     input_labels = {}
		#     for wid,v in inputs.iteritems():
		#         assert v in (0,1)
		#         input_labels[wid] = self.wire_labels[wid][v]
		#         obj["inputs"] = input_labels

		with open(outfile,"w") as f:
			json.dump(obj, f, indent=4)
		print 'Wrote garbled circuit', outfile

	def garble_evaluate(self, inp, from_json=None):
		# print DELTA
		if from_json is not None:
			self.gates = from_json['gates']
			assert len(inp) == len(self.input_wires)
			for gid in self.pool:
				evaluate_gate(self.pool[gid])
			print 'The generator is valid'

			self.bucket_wire_labels = {}
			for wid in self.input_wires:
				assert wid in inp, 'Must provide a label for each wire'
				label = inp[wid]
				assert len(label) == 2 * 16  # Labels are keys, 16 bytes in hex
				self.bucket_wire_labels[wid] = label

			for gid in self.sorted_gates:
				count = 0
				B = len(self.gates[gid]['tables'])
				w0 = self.gates[gid]['inp'][0]
				w1 = self.gates[gid]['inp'][1]
				w2 = self.gates[gid]['out'][0]
				bucket_wire_label0 = self.bucket_wire_labels[w0]
				bucket_wire_label1 = self.bucket_wire_labels[w1]
				# print bucket_wire_label0, bucket_wire_label1
				# soldering
				result = {}
				for tid in self.gates[gid]['tables']:
					table = self.gates[gid]['tables'][tid]
					inp0 = xor_hex(table['inp_d'][w0], bucket_wire_label0).decode('hex')
					# print inp0.encode('hex')
					inp1 = xor_hex(table['inp_d'][w1], bucket_wire_label1).decode('hex')
					for c in table['garble_table']:
						cipher = c.decode('hex')
						if specialDecryption(inp0, cipher) == None:
							continue
						k = specialDecryption(inp0, cipher)
						if specialDecryption(inp1, k) == None:
							continue
						m = specialDecryption(inp1, k)
						label = m.encode('hex')
						label = xor_hex(label, table['out_d'][w2])
						if label in result:
							result[label] += 1
						else:
							result[label] = 1
				assert len(result) == 1, "Invalid generator detected"
				(label, count) = result.popitem()
				assert count == 10, "Invalid generator detected"
				self.bucket_wire_labels[w2] = label
			return dict((wid,self.bucket_wire_labels[wid]) for wid in self.output_wires)

				





if __name__ == '__main__':
	import sys
	if len(sys.argv) < 3:
		print "usage: python evaluator.py <circuit.json> <first_phase_output.json>"
		sys.exit(1)

	filename = sys.argv[1]
	obj = json.load(open(filename))

	if len(sys.argv) == 3:
		# Circuit
		c = PoolEvaluator(from_json=obj)

		# first phase communication
		outfile = sys.argv[2]
		c.first_phase_output(outfile)

	if len(sys.argv) == 4:
		inputs = obj["inputs"]
		c = PoolEvaluator(from_json=obj)
		extra = json.load(open(sys.argv[2]))
		# print extra['gates']['g3']['tables']['56']['out_d']
		c.garble_evaluate(inputs, from_json=extra)
