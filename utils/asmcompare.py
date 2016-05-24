# ROPMEMU framework
#
# asmcompare: script to compare the ASM generated 
# by unrop GDB command with the ASM generated by ropemu 
# through jsondisass utility.
#


import sys
from collections import OrderedDict


def parse_jsondisass(fd):
    json_disass = OrderedDict()
    for line in fd.readlines():
        l = line.strip()
        if l.startswith("["): continue
        try:
            number, instruction = l.split(" ", 1)  
        except:
            print l
            raise ValueError
        instr = space_normalizer(instruction)
        if instr.startswith("mov"): instr = sanitize_mov(instr)
        if "0x" in instr: instr = remove_hex(instr)
        if number[:-1] not in json_disass:
            json_disass[str(int(number[:-1]))] = instr
    return json_disass

def remove_hex(instr):
    right = ""
    for b in instr.split(','):
        if "0x" in b:
            b = "%c%s" % (",", str(int(b, 16)))
            right += b
            continue
        right += b
    return right

def sanitize_mov(instr):
    if "QWORDPTR" in instr:
        return instr.replace("QWORDPTR", "")
    if "qwordptr" in instr:
        return instr.replace("qwordptr", "")
    return instr

def space_normalizer(instruction):
    c = 0
    norm_instr = ""
    for i in instruction:
        if i == " ":
           c += 1
           if c != 1: continue
        norm_instr += i
    return norm_instr

def parse_unrop(fd):
    unrop = OrderedDict()
    for line in fd.readlines():
        l = line.strip()
        number, instruction = l.split(" ", 1)
        num = number.split("-")[1]
        instr = space_normalizer(instruction)
        if instr.startswith("mov"): instr = sanitize_mov(instr)
        if "0x" in instr: instr = remove_hex(instr)
        if num not in unrop:
            unrop[num] = instr
    return unrop

def zoom(n, json_disass, unrop_disass):
    print "-"*31
    for x in xrange(int(n)-3, int(n)+3):
        if str(x) not in json_disass.keys() or str(x) not in unrop_disass.keys(): continue
        print "j: %d:%s | u: %d:%s" % (x, json_disass[str(x)], x, unrop_disass[str(x)])

def compare(json_disass, unrop_disass):
    match = 0
    mismatch = 0
    for n, i in json_disass.items():
        if n not in unrop_disass.keys(): continue
        if i == unrop_disass[n]:
            match += 1
        else:
            mismatch += 1
            print "\nMismatch at %s:" % n
            zoom(n, json_disass, unrop_disass)
    print "[+] Results: "
    print "\t - match: %d - mismatch: %d" % (match, mismatch)

def check_instruction(instruction, dictio):
    results = []
    for k, v in dictio.items():
        if instruction in v: results.append(k)
    return results

def show_matches(l, dictio):
    for i in l:
        print i, dictio[i]

def lookup_instr(instruction, json_disass, unrop_disass):
    print "\nLookup %s" % instruction
    l1 = check_instruction(instruction, json_disass)
    l2 = check_instruction(instruction, unrop_disass)
    print "json_disass:"
    show_matches(l1, json_disass)
    print "unrop_disass:"
    show_matches(l2, unrop_disass)

def main():
    if len(sys.argv) != 3:
        print "[-] Usage: %s %s %s" % (sys.argv[0], "<jsondisassout>", "<unropout>")
        sys.exit(1)

    # load file from jsondisass
    fj = open(sys.argv[1])
    json_disass = parse_jsondisass(fj)
    fj.close()

    # load file from unrop
    fu = open(sys.argv[2])
    unrop_disass = parse_unrop(fu)
    fu.close()

    print "[+] ropemu - total instructions: %d" % (len(json_disass.keys()))
    print "[+] GDB (unrop) - total instructions: %d" % (len(unrop_disass.keys()))

    compare(json_disass, unrop_disass)

    #lookup_instr("jmp rax", json_disass, unrop_disass)

main()
