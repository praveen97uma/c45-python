import sys
import os.path
import xml.dom.minidom
import csv
from collections import Counter
import math 
from database import ElectionDatabase
from data_types import CSVData, ClassificationData
from copy import deepcopy

class Trainer:
    def __init__(self, domain, class_data, document):
        self.load_domain(domain)
        self.edge = 0 
        self.debug = 0 
        self.class_data  = class_data
        self.attributes  = class_data.attributes
        self.category    = class_data.category[0]
        self.column_size = class_data.domain_size
        self.data        = class_data.tuples 
        self.doc = document
        
        if self.debug == 1:
            print "Header information: "
            print self.attributes
            print self.column_size
            print self.category + "\n\n"
    
    def load_domain(self, domain):
        # Load the domain into a parseable document object
        self.dom = xml.dom.minidom.parse(domain).documentElement

        # values can be accesses by : self.category['values'] or if you want the
        # first element, it'd be self.category['values'][0]
        self.category = {'name': self.dom.getElementsByTagName('Category')[0].getAttribute('name'), 'values': self.get_choice()}
        self.cols = self.get_columns()
        self.attributes = self.cols.keys()
   
    def rem_restrictions(self, restrictions):
        restr = restrictions[0]
        i = 0
        index = i
        for x in restr:
            if int(restr[i]) == -1 and i != 0:
                column = self.attributes[index]
                print "Removing " + str(self.attributes[index])
                self.attributes.remove(self.attributes[index])
            else:
                index += 1
            i+=1 
    def get_columns(self):
        cols = {}

        for node in self.dom.getElementsByTagName('variable'):
            col_name = str(node.getAttribute('name'))
            cols[col_name] = self.get_group(node)

        return cols
 
    def get_group(self, node):
        vals = []

        for el in node.getElementsByTagName('group'):
            name = el.getAttribute('name')
            p    = el.getAttribute('p')
            vals.append({'name': name, 'p': float(p)})

        return vals

    def get_choice(self):
        vals = []

        for c in self.dom.getElementsByTagName('choice'):
           c_name = c.getAttribute('name') 
           c_type = c.getAttribute('type') 
           vals.append((c_name, c_type))

        return vals

    def entropy(self, D):
        index = 11 
        obama_ct = 0
        mccain_ct = 0

        if len(D) == 0:
            return 0        

        for e in D:
            if e[index] == 1:
                obama_ct += 1
            elif e[index] == 2:
                mccain_ct += 1
             
        obama_ct = obama_ct / float(len(D))
        mccain_ct = mccain_ct / float(len(D))
        
        if self.debug == 1:
            print "Percent 1: " + str(obama_ct)
            print "Percent 2: " + str(mccain_ct)

        if obama_ct == 0 or mccain_ct == 0:
            return 0        

        entropy = -obama_ct * math.log(obama_ct, 2) - mccain_ct * math.log(mccain_ct, 2)
        return entropy  

    def entropyAi(self, D, Ai):
       id_list = []
       slices = self.get_slices(D, Ai);
       entropies = []
       total_entropy = 0;

       for mslice in slices:
           entropies.append(self.entropy(mslice))
       i=0 
       for entropy in entropies:
           if self.debug == 1:
               print "Entropy["+str(i)+"] = " + str(entropies[i])
           total_entropy += len(slices[i])/float(len(D)) * entropies[i]    
           i+=1 

       return total_entropy
 
    def is_homogenous(self, D):
        if len(D) == 0:
            return False
        mytype = D[0][1]
        for ele in D:
            if ele[11] != mytype:
               return False
        return True   

    def most_freq(self, D):
        obama_ct = 0
        mccain_ct = 0
        for ele in D:
            if ele[11] == 1:
               obama_ct += 1
            elif ele[11] == 2:
               mccain_ct += 1
        if mccain_ct > obama_ct:
            return "2"
        else:
            return "1"

    def get_pres_choice(self, i):
        if int(i) == 2:
            return "McCain"
        elif int(i) == 1:
            return "Obama"
 
    def c45(self, D, A, element, threshold):
        if self.debug == 1:
            print "Attributes: ", A
        if self.is_homogenous(D):
            node = self.doc.createElement('decision')
            node.setAttribute('end', str(D[0][11]))
            node.setAttribute('choice', self.get_pres_choice(D[0][11]))
            element.appendChild(node)
        elif len(A) == 0:
            most_freq_label = self.most_freq(D)
            node = self.doc.createElement('decision')
            node.setAttribute('end', most_freq_label)
            node.setAttribute('choice', self.get_pres_choice(most_freq_label))
            element.appendChild(node)
        else:
            Ag = self.select_splitting_attr(A, D, threshold)
            
            if (Ag == -1):
                most_freq_label = self.most_freq(D)
                node = self.doc.createElement('decision')
                node.setAttribute('end', most_freq_label)
                node.setAttribute('choice', self.get_pres_choice(most_freq_label))
                element.appendChild(node)
            else:
                if self.debug == 1:
                    print "Splitting on: " + Ag

                node = self.doc.createElement('node')
                node.setAttribute('var', str(Ag))
                element.appendChild(node)
                #minus one becuase we removed ID
                size = int(self.class_data.size_map[Ag])
                for i in range(size-1, -1, -1):
                    Dv = self.my_slice(Ag, i+1, D)
                    if len(Dv) != 0:
                        tempAtts = deepcopy(A);
                        tempAtts.remove(Ag)

                        edge = self.doc.createElement('edge')
                        edge.setAttribute('num', str(i+1))
                        edge.setAttribute('var', self.cols[Ag][i]['name'])

                        self.c45(Dv, tempAtts, edge, threshold)
                        
                        node.appendChild(edge)
                    
    def get_slices(self, D, Ai):
        slices=[]
        index = 1
        for i in range(int(self.class_data.size_map[Ai])):
            index = i+1
            slices.append(self.my_slice(Ai, index, D))
        
        if self.debug == 1:
            for sl in slices:
                print "Slice: "
                print sl + "\n"
        
        return slices 

    def my_slice(self, attr, val, D):
        attr_ind = self.attributes.index(attr)+1

        if self.debug == 1:
            print "Index for " + str(attr) + " is : " + str(attr_ind)
        
        mslice = []
        for row in D:
            if row[attr_ind] == val:
                mslice.append(row)
        return mslice
 
    #return -1 when no attribute selected!!
    def select_splitting_attr(self, A, D, threshold):
        p0 = self.entropy(D)
        if self.debug == 1:
            print "P0 entropy: " + str(p0)

        indexes = []
        p = {}
        gain = {}
        max_gain = float("-inf")
        for attr in A:
            p[attr] = self.entropyAi(D, attr);
            gain[attr] = p0 - p[attr]; 
            if gain[attr] > max_gain:
                max_gain = gain[attr]
                max_attr = attr
            if self.debug == 1:
                print "Attr: " + str(attr) +  " gain: " + str(gain[attr])
        if self.debug == 1:
            print "Max gain: " + str(max_gain) + " Max attr: " + str(max_attr)
        if max_gain > threshold: 
            return max_attr 
        else:
             return -1

def main():
    num_args = len(sys.argv)
    domain = training = restriction = ''

    # Make sure the right number of input files are specified
    if  num_args <= 2 or num_args > 4:
        print 'Expected input format: python inducec45.py <domainFile.xml> <TrainingSetFile.csv> [<restrictionsFile>]'
        return
    # If they are read them in
    else: 
        if check_file(sys.argv[1]) == -1 or check_file(sys.argv[2]) == -1:
            return -1
    
        domain = open(sys.argv[1], "r")
 
        #parse the rows directly to the db
        class_data = ClassificationData(sys.argv[2]);
        class_data.parse_tuples();

        if num_args == 4:
            restriction = ClassificationData(sys.argv[3])
            restriction.parse_restr_tuples();
   
    document = xml.dom.minidom.Document() 
    node = document.createElement('Tree')

    document.appendChild(node)

    d = Trainer(domain, class_data, document)
    if num_args == 4: 
        d.rem_restrictions(restriction.restr)

    partial_atts = d.attributes
    partial_atts.remove("Id")
    partial_atts.remove("Vote")

    d.c45(d.data, d.attributes, node, 0)
    print document.toprettyxml()

def check_file(filename):
    if not os.path.exists(filename) or not os.path.isfile(filename): 
        print 'Error can not find the specified file: ', filename
        return -1
    else:
        return filename

if __name__ == '__main__':
    main()
