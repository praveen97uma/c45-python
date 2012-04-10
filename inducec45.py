import sys
import os.path
import xml.dom.minidom
import csv
from database import ElectionDatabase
from data_types import CSVData, ClassificationData

class Trainer:
    def __init__(self, domain, class_data, db):
        self.load_domain(domain)
        #by the time we are at this point we have the following things available. 
        #1) class_data a ClassificationData object containing the headers of the csvdata file stored
        #2) a database of the tuples 
             #--for some reason I was having a hard time getting it to work with the numbers insert we should check that out
        attribute = class_data.names[1]
        data_range= class_data.domain_size[1]
        db.data_slice(attribute, data_range)

    def load_domain(self, domain):
        # Load the domain into a parseable document object
        self.dom = xml.dom.minidom.parse(domain).documentElement

        # values can be accesses by : self.category['values'] or if you want the
        # first element, it'd be self.category['values'][0]
        self.category = {'name': self.dom.getElementsByTagName('Category')[0].getAttribute('name'), 'values': self.get_choice()}
        self.cols = self.get_columns()
        self.attributes = self.cols.keys()

    def get_columns(self):
        cols = {}

        for node in self.dom.getElementsByTagName('variable'):
            col_name = node.getAttribute('name')
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
 
        #connect to our elections db, stored on my mediatemple  
        db = ElectionDatabase()
        db.connect()

        #parse the rows directly to the db
        class_data = ClassificationData(sys.argv[2]);
        class_data.parse_tuples_to_db(db);

        if num_args == 4:
            restriction = open(check_file(sys.argv[3]), "r") 
    
    d = Trainer(domain, class_data, db)

#    print c45(d.data, d.attributes, xml.dom.minidom.getDOMImplementation())

def check_file(filename):
    if not os.path.exists(filename) or not os.path.isfile(filename): 
        print 'Error can not find the specified file: ', filename
        return -1
    else:
        return filename


# def find_most_frequent_label(D):

# def create_label():

# def enthropy(D):

# D : Training Dataset
# A : List of Attributes
# T : Constructed Decision tree

#def c45(D, A, T):
# Step 1: check termination conditions
# D contains records with the same class label c
# if for all d is in D: class(d) = ci then
#if :
#     create leaf node r;
#     label(r) := ci;
#     T := r;
# No more attributes to consider
# else if A = NONE LEFT then
#elif :
#     c := find most frequent label(D);
#     create leaf node r;
#     label(r) := c;
# else 
#else:
# Step 2: select splitting attribute
#     Ag := selectSplittingAttribute(A,D, threshold);
#    Ag = select_splitting_attr(A, D, threshold)
#     if Ag = NULL then //no attribute is good for a split
#    if (Ag == NULL):
#         create leaf node r;
#         label(r) := find most frequent label(D);
#         T := r;
#    else:
#     else // Step 3: Tree Construction
#         create tree node r;
#         label(r) := Ag;
#         foreach v is in dom(Ag) do
#             Dv := {t belongs in D|t[Ag] = v};
#             if Dv =6 NONE LEFT then
#                 C45(Dv, A - {Ag}, Tv); //recursive call
#                 append Tv to r with an edge labeled v;
#             endif
#         endfor
#     endif
# endif

#uses information gain
# D : Training Dataset
# A : List of Attributes
#def select_splitting_attr(A, D, threshold):
# p0 := enthropy(D);
# for each Ai in A do
#     p[Ai] := enthropyAi (D);
#     Gain[Ai] = p0 - p[Ai]; //compute info gain
# endfor
# best := arg(findMax(Gain[]));
# if Gain[best] >threshold then return best
# else return NULL;

#uses information gain ratio
# D : Training Dataset
# A : List of Attributes
#def select_splitting_attr_ratio(A, D, threshold);
# p0 := enthropy(D);
# for each Ai in A do
#     p[Ai] := enthropyAi (D);
#     Gain[Ai] := p0 - p[Ai]; //compute info gain
#     gainRatio[Ai] := Gain[Ai]/enthropy(Ai); //compute info gain ratio
# endfor
# best := arg(findMax(gainRatio[]));
# if Gain[best] >threshold then return best
# else return NULL;

#def parse_domain():

if __name__ == '__main__':
    main()
