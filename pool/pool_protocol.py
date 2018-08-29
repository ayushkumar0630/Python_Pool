import circuit
from circuit import BooleanCircuit
import json
from util import specialDecryption, specialEncryption, generate_key
import os
import random
from pool_generator import PoolGenerator
from pool_evaluator import PoolEvaluator
import sys

if len(sys.argv) != 2:
	print "usage: python pool_protocol.py <circuit.json>"
	sys.exit(1)

# First step: generate circuit structure with empty bucket and the pool of gates
print '/////////////////////////////////////////////////////////////////////////'
print "Generator start the commnunication....."
filename = sys.argv[1]
obj = json.load(open(filename))
c = PoolGenerator(from_json=obj)
print 'Circuit loaded: %d gates, %d input wires, %d output_wires, %d total' \
	% (len(c.gates), len(c.input_wires), len(c.output_wires), len(c.wires))
# Generate the circuit
c.garble()

# Load the inputs
inputs = obj["inputs"]

# Write the output
outfile1 = 'first.json'
c.output(outfile1, inputs)
print 'Phase 1 completes'
print '///////////////////////////////////////////////////////////////////////////'


print ''
print ''
print ''

# Second step: evaluator random pick gates from the pool and fill the bucket with 10 gates for each bucket
print '/////////////////////////////////////////////////////////////////////////'
print 'Evaluator picks from the pool....'
obj = json.load(open(outfile1))
c = PoolEvaluator(from_json=obj)
outfile2 = 'second.json'
c.first_phase_output(outfile2)
print 'Phase 2 completes'
print '/////////////////////////////////////////////////////////////////////////'

print ''
print ''
print ''



# Third step: generator create soldering label for each gates
print '/////////////////////////////////////////////////////////////////////////'
print 'Generator evaluates secrets for each bucket...'
obj = json.load(open(outfile1))
c = PoolGenerator(from_json=obj)
wire_labels = obj['wire_labels']
outfile3 = 'third.json'
extra_file = json.load(open(outfile2))
c.second_phase_output(outfile3, wire_labels, from_json=extra_file)
print 'Phase 3 completes'
print '/////////////////////////////////////////////////////////////////////////'

print ''
print ''
print ''

# Fourth step: evaluator check the rest of gates in pool and evaluate the circuts
print '/////////////////////////////////////////////////////////////////////////'
print 'Evaluator starts evaluation...'
c = PoolEvaluator(from_json=obj)
inputs = obj["inputs"]
extra = json.load(open(outfile3))
# print c.garble_evaluate(inputs, from_json=extra)
json.dump(c.garble_evaluate(inputs, from_json=extra), sys.stdout, indent=4)
print ""
print 'The evaluation completes'