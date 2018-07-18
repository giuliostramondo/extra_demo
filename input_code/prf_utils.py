#import matplotlib.pyplot as plt
import numpy as np
import re 
import argparse
from enum import Enum
import itertools
import pulp
from math import floor
import sys

def compute_omega(p,q):
    def xgcd(b, n):
        x0, x1, y0, y1 = 1, 0, 0, 1
        while n != 0:
            q, b, n = b // n, n, b % n
            x0, x1 = x1, x0 - q * x1
            y0, y1 = y1, y0 - q * y1
        return b, x0, y0
    (gcd, t,s) = xgcd(p, q)
    #print (t,s)
    sigma = 0
    omega = s + sigma * p
    while omega <= 0:
        sigma += 1
        omega = s + sigma * p
    return omega

def parseATrace(filename):
    def comment_remover(text):
        def replacer(match):
            s = match.group(0)
            if s.startswith('/'):
                return " " # note: a space and not an empty string
            else:
                return s
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE
        )
        return re.sub(pattern, replacer, text)
    #print filename
    f = open(filename, 'r')
    parallelAccess = f.read()
    parallelAccess = comment_remover(parallelAccess)
    pattern  = '(A[\d+][\d+],)*A[\d+][\d+];'
    pattern = "A\[(\d+)\]\[(\d+)\]"
    p = re.compile(pattern)

    accessList = parallelAccess.split(";")
    parsedAccessList = []
    for access in accessList:
        if access  and (not access.isspace()):
            parsed = p.findall(access)
            parsedAccessList.append(map(lambda tuple: (int(tuple[0]),int(tuple[1])), parsed))

    return parsedAccessList

def parseATraceFromString(string):
    def comment_remover(text):
        def replacer(match):
            s = match.group(0)
            if s.startswith('/'):
                return " " # note: a space and not an empty string
            else:
                return s
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE
        )
        return re.sub(pattern, replacer, text)
    #print filename
    parallelAccess = string
    parallelAccess = comment_remover(parallelAccess)
    pattern  = '(A[\d+][\d+],)*A[\d+][\d+];'
    pattern = "A\[(\d+)\]\[(\d+)\]"
    p = re.compile(pattern)

    accessList = parallelAccess.split(";")
    parsedAccessList = []
    for access in accessList:
        if access  and (not access.isspace()):
            parsed = p.findall(access)
            parsedAccessList.append(map(lambda tuple: (int(tuple[0]),int(tuple[1])), parsed))

    return parsedAccessList



def find_plot_dimension(accessList):
    dim1 = 0
    dim2 = 0
    for parellelAccess in accessList:
        for access in parellelAccess:
            #print access
            if dim1 < access[0]:
                dim1 = access[0]
            if dim2 < access[1]:
                dim2 = access[1]
    return (dim1+1,dim2+1)


def find_matrix_dimension(parellelAccess,p,q):
    dim1 = 0
    dim2 = 0
    for access in parellelAccess:
        #print access
        if dim1 < access[0]:
            dim1 = access[0]
        if dim2 < access[1]:
            dim2 = access[1]
    return (dim1+1+(p*q),dim2+1+(p*q))


def create_plane_image(size):
    image = np.zeros(size[0]*size[1])
    image = image.reshape((size[0], size[1]))
    return image
	
def plot_array(image, item_to_access,title,coverage=[],coverage_id=-1,type=0):
    print "This function was commented out to solve problems with matplotlib"
    if coverage == [] or coverage_id != -1:
        for to_access in item_to_access:
            image[to_access[0]][to_access[1]]+=5

    if coverage != []:
        if coverage_id != -1:
            for accessed in coverage[coverage_id]:
                image[accessed[0]][accessed[1]]+=4
        else:
            for i in range(0,len(coverage)):
                for accessed in coverage[i]:
                    image[accessed[0]][accessed[1]]+=1

    #Remove item_to_access from image
    if type == 1:
        for to_access in item_to_access:
            image[to_access[0]][to_access[1]]=0
            
    row_labels = range(len(image))
    col_labels = range(len(image[0]))
    #plt.rcParams['figure.figsize'] = 100, 100
    #im=plt.matshow(image, cmap=plt.cm.gray)
    #if coverage != [] and coverage_id == -1:
     #   plt.colorbar(im,ticks=[0, 1, 2,3],fraction=0.046, pad=0.04)
    #plt.xticks(range(len(image[0])), col_labels)
    #plt.yticks(range(len(image)), row_labels)
    #plt.title(title)
    


    #plt.gca().invert_yaxis()
    #plt.gca().set_xticks([x - 0.5 for x in plt.gca().get_xticks()][1:], minor='true')
    #plt.gca().set_yticks([y - 0.5 for y in plt.gca().get_yticks()][1:], minor='true')
    #plt.grid(which='minor',color='b', linestyle='-', linewidth=2)


    #plt.show()


class Shape(Enum):
    RECTANGLE = 0
    ROW = 1
    COLUMN =2
    MAIN_DIAGONAL = 3
    SECONDARY_DIAGONAL = 4
    TRANSPOSED_RECTANGLE = 5

class MappingScheme(Enum):
    RECTANGLE_ONLY = 0
    ReRo = 1
    ReCo = 2
    RoCo = 3
    ReTr = 4

availableShapes={MappingScheme.RECTANGLE_ONLY:[Shape.RECTANGLE], 
                 MappingScheme.ReRo:[Shape.RECTANGLE,Shape.ROW,Shape.MAIN_DIAGONAL,Shape.SECONDARY_DIAGONAL],
                 MappingScheme.ReCo:[Shape.RECTANGLE,Shape.COLUMN,Shape.MAIN_DIAGONAL,Shape.SECONDARY_DIAGONAL],
                 MappingScheme.RoCo:[Shape.RECTANGLE,Shape.COLUMN,Shape.ROW],
                 MappingScheme.ReTr:[Shape.RECTANGLE,Shape.TRANSPOSED_RECTANGLE],}
    

def AGU(start_i,start_j,p,q,shape):
    res=[]
    if shape == Shape.RECTANGLE:
        for i in range(0,p):
            for j in range(0,q):
                res.append((start_i+i,start_j+j))
        return res
    elif shape == Shape.ROW:
        for i in range(0,p):
            for j in range(0,q):
                res.append((start_i,start_j+(i*q+j)))
        return res
    elif shape == Shape.MAIN_DIAGONAL:
        for i in range(0,p):
            for j in range(0,q):
                res.append((start_i+(i*q+j),start_j+(i*q+j)))
        return res
    elif shape == Shape.SECONDARY_DIAGONAL:
        for i in range(0,p):
            for j in range(0,q):
                res.append((start_i+(i*q+j),start_j-(i*q+j)))
        return res
    elif shape == Shape.COLUMN:
        for i in range(0,p):
            for j in range(0,q):
                res.append((start_i+(i*q+j),start_j))
        return res
    elif shape == Shape.TRANSPOSED_RECTANGLE:
        for i in range(0,p):
            for j in range(0,q):
                res.append((start_i+j,start_j+i))
        return res
    else:
        return res

def m(i,j,mappingScheme,p,q):
    if mappingScheme == MappingScheme.RECTANGLE_ONLY:
        k = i%p
        l=  j%q
    elif mappingScheme == MappingScheme.ReRo:
        k=int((i+floor(j/q))%p)
        l= j%q
    elif mappingScheme == MappingScheme.ReCo:
        k = i%p
        l = int((floor(i/p)+j)%q)
    elif mappingScheme == MappingScheme.RoCo:
        #k = int((i+floor(j/q))%p)
        #l = int((floor(i/p)+j)%q)

        k = (i+j/q)%p
        l = (i/p+j)%q
    elif mappingScheme == MappingScheme.ReTr:
        if(p<q):
            k = i%p
            l= (i-i%p+j)%q
        else:
            k = (i+j-(j%q))%p
            l = j%q
    return (k,l)

def inv_m(i,j,mappingScheme,p,q,k,l):
    if mappingScheme == MappingScheme.ReRo:
        beta =  (l-(j%q))%q
        alpha = (k-i%p-(j/q)%p-((j%q)+beta)/q)%p
    elif mappingScheme == MappingScheme.ReCo:
        alpha =  (k-i%p)%p
        beta = (l-j%q-(i/p)%q-((i%p)+alpha)/p)%q
    elif mappingScheme == MappingScheme.RoCo:
        beta1 =  (l-(j%q))%q
        alpha = (k-i%p-(j/q)%p-((j%q)+beta1)/q)%p
        #alpha = (k-i%p-(j/q)%p-((j%q)+((l-(j%q))%q))/q)%p
        alpha1 =  (k-i%p)%p
        beta = (l-j%q-(i/p)%q-((i%p)+alpha1)/p)%q
        #beta  = (l-j%q-(i/p)%q-((i%p)+((k-i%p)%p))/p)%q
    elif mappingScheme == MappingScheme.ReTr:
        if p<q:
            alpha = (k-i%p)%p
            beta  = (l-(i+alpha)%q+(i+alpha)%p-j%q)%q
        else:
            beta =  (l-(j%q))%q
            alpha = (k-i%p-(j+beta)%p+(j+beta)%q)%p
    return (alpha,beta)

def inv_m_shapes(i,j,mappingScheme,p,q,k,l,shape):
    if mappingScheme == MappingScheme.ReRo:
        if shape == Shape.RECTANGLE:
            beta =  (l-(j%q))%q
            alpha = (k-i%p-(j/q)%p-((j%q)+beta)/q)%p
        if shape == Shape.ROW:
           #n2 = 0
            #if l-j%q<0:
             #   n2 =1
            beta1 =  l-(j%q)
            alpha1 = (k-i%p-(j/q)%p-((j%q)+beta1)/q)%p
            alpha = 0
            beta = (beta1+alpha1*q)%(p*q)
        if shape == Shape.MAIN_DIAGONAL:
            # n2 = 0
            # if l-j%q<0:
            #   n2 =1
            cj1 =0

            k=(k+p-1)%p
            #Catalin's way
            if l>=j%q:
                cj1 = -1
            cj2 = ((k-i%p - ((l-j%q)%q)%p - cj1 - (j/q)%p) %(p * compute_omega(p,q+1)))%p

            cj2 = ((k - i % p - ((l - j % q) % q) % p - cj1 - (j / q) % p) * compute_omega(p, q + 1)) % p


            res = (l-j%q)%q+q*cj2
            #res = (i % p + ((l - j % q) % q) % p + ((q + 1) * cj2) % p + cj1 + (j / q) % p) % p
            alpha = res
            beta = res

        if shape == Shape.SECONDARY_DIAGONAL:
            # n2 = 0
            # if l-j%q<0:
            #   n2 =1
            cj1 =0

            #l = (-l - j * (q / 3) - j * (q / 4) - j * (q / 5) - j * (q / 7)) % q


            #l = (-l - j * ((q / 3) + (q / 4) + (q / 5) + (q / 7))) % q

            if j%q == 0 and l == 0:
                k=(k-1)%p

            if j%q == 1 and (l == 0 or l == 1 or l ==2):
                k=(k-1)%p

            if j%q == 2 and ( l == 1 or l ==2 or l == 3) and q == 4 :
                k=(k-1)%p


            if j%q == 2 and ( l == 0 or l == 1 or l ==2 or l == 3 or l== 4) and (q == 6 or q == 8):
                k=(k-1)%p

            if j%q == 3 and ( l == 5 or l == 1 or l ==2 or l == 3 or l== 4) and (q == 6):
                k=(k-1)%p

            if j%q == 3 and ( l == 0 or l == 1 or l ==2 or l == 3 or l== 4 or l== 5 or l== 6) and (q == 8):
                k=(k-1)%p

            if j%q == 3 and (l ==3) and q == 4:
                k=(k-1)%p

            if j%q == 4 and ( l == 5 or l == 3 or l== 4) and (q == 6):
                k=(k-1)%p

            if j%q == 4 and ( l == 1 or l == 2 or l== 3 or l== 4 or l== 5 or l== 6 or l== 7) and (q == 8):
                k=(k-1)%p

            if j%q == 5 and ( l == 5) and (q == 6):
                k=(k-1)%p

            if j%q == 5 and ( l == 3  or l== 4  or l== 5  or l== 6 or l== 7) and (q == 8):
                k=(k-1)%p

            if j%q == 6 and ( l== 5  or l== 6 or l== 7) and (q == 8):
                k=(k-1)%p

            if j%q == 7 and ( l== 7) and (q == 8):
                k=(k-1)%p

            # if j == 4 and (l ==0):
            #     k=(k-1)%p

            l = (-l - j * (q - 2)) % q

            # if l==0 and j ==1 :
            #     k = (k - 1) % p

            # if l == 0:
            #     k = (k - 1) % p
            #k = ((k-1)*(not (l))%p+k*(not not (l))%p)%p
            #Catalin's way
            if l>=j%q:
                cj1 = -1


            cj2 = ((k-i%p - ((l-j%q)%q)%p - cj1 - (j/q)%p) %(p * compute_omega(p,q+1)))%p

            cj2 = ((k - i % p - ((l - j % q) % q) % p - cj1 - (j / q) % p) * compute_omega(p, q - 1)) % p


            res = (l-j%q)%q+q*cj2
            #res = (i % p + ((l - j % q) % q) % p + ((q + 1) * cj2) % p + cj1 + (j / q) % p) % p
            alpha = res
            beta = -res

    elif mappingScheme == MappingScheme.ReCo:
        if shape == Shape.RECTANGLE:
            alpha =  (k-i%p)%p
            beta = (l-j%q-(i/p)%q-((i%p)+alpha)/p)%q
        if shape == Shape.COLUMN:
            alpha1 =  (k-i%p)%p
            beta1 = (l-j%q-(i/p)%q-((i%p)+alpha1)/p)%q
            alpha = (beta1*p+alpha1)%(p*q)
            beta = 0
        if shape == Shape.MAIN_DIAGONAL:
            alpha1 =  (k-i%p)%p
            beta1 = (l-j%q-(i/p)%q-((i%p)+alpha1)/p)%q
            alpha = (((beta1*p+alpha1)*(p+1))%(p*q))
            beta = (((beta1*p+alpha1)*(p+1))%(p*q))
    elif mappingScheme == MappingScheme.RoCo:
        if shape == Shape.RECTANGLE:
            beta1 = (l - (j % q)) % q
            alpha = (k - i % p - (j / q) % p - ((j % q) + beta1) / q) % p

            #alpha = (k-i%p-(j/q)%p-((j%q)+((l-(j%q))%q))/q)%p


            alpha1 =  (k-i%p)%p
            beta = (l-j%q-(i/p)%q-((i%p)+alpha1)/p)%q
            #beta  = (l-j%q-(i/p)%q-((i%p)+((k-i%p)%p))/p)%q


        if shape == Shape.COLUMN:
            beta1 = (l - (j % q)) % q
            alpha2 = (k - i % p - (j / q) % p - ((j % q) + beta1) / q) % p

            #alpha = (k-i%p-(j/q)%p-((j%q)+((l-(j%q))%q))/q)%p


            alpha1 =  (k-i%p)%p
            beta2 = (l-j%q-(i/p)%q-((i%p)+alpha1)/p)%q
            #beta  = (l-j%q-(i/p)%q-((i%p)+((k-i%p)%p))/p)%q
            alpha = (beta2*p+alpha2)%(p*q)
            beta = 0
        if shape == Shape.ROW:
            beta1 = (l - (j % q)) % q
            alpha2 = (k - i % p - (j / q) % p - ((j % q) + beta1) / q) % p

            #alpha = (k-i%p-(j/q)%p-((j%q)+((l-(j%q))%q))/q)%p


            alpha1 =  (k-i%p)%p
            beta2 = (l-j%q-(i/p)%q-((i%p)+alpha1)/p)%q
            alpha = 0
            beta = (beta2+alpha2*q)%(p*q)
    elif mappingScheme == MappingScheme.ReTr:
        if p<q:
            alpha = (k-i%p)%p
            beta  = (l-(i+alpha)%q+(i+alpha)%p-j%q)%q
        else:
            beta =  (l-(j%q))%q
            alpha = (k-i%p-(j+beta)%p+(j+beta)%q)%p
    return (alpha,beta)

#Returns an array containing all the possible coverage sets
#for a given scheme
#scheme can be a mapping scheme or a list of shapes
def possibleCoverage(N, M, p, q, scheme):
    if isinstance(scheme,list):
        shapes = scheme
    elif isinstance(scheme,MappingScheme):
        shapes = availableShapes[scheme]
    else:
        print "This function accepts either a MappingScheme either a list of Shape, you used "+str(type(scheme))
        return []

    res = []
    for shape in shapes:
        i_MAX = 0
        j_MAX = 0
        i_MIN = 0
        j_MIN = 0
        if shape == Shape.RECTANGLE:
            i_MAX = (N-p)+1
            j_MAX = (M-q)+1
        elif shape == Shape.ROW:
            i_MAX = (N)
            j_MAX = (M-(p*q)+1)
        elif shape == Shape.COLUMN:
            i_MAX = (N-(p*q)+1)
            j_MAX = (M)
        elif shape == Shape.TRANSPOSED_RECTANGLE:
            i_MAX = (N-q+1)
            j_MAX = (M-p+1)
        elif shape == Shape.MAIN_DIAGONAL:
            i_MAX = (N-(p*q)+1)
            j_MAX = (M-(p*q)+1)
        elif shape == Shape.SECONDARY_DIAGONAL:
            j_MIN = (p*q)
            i_MAX = (N-(p*q)+1)
            j_MAX = (M)
        else:
            print "possibleCoverage: Unrecognized Shape"
            
        for i in range(i_MIN,i_MAX):
            for j in range(j_MIN,j_MAX):
                res.append(AGU(i,j,p,q,shape))
    return res

def possibleCoverage_and_ParallelAccesses(N, M, p, q, scheme):
    if isinstance(scheme,list):
        shapes = scheme
    elif isinstance(scheme,MappingScheme):
        shapes = availableShapes[scheme]
    else:
        print "This function accepts either a MappingScheme either a list of Shape, you used "+str(type(scheme))
        return []

    res = []
    par_accs =[]
    for shape in shapes:
        i_MAX = 0
        j_MAX = 0
        i_MIN = 0
        j_MIN = 0
        if shape == Shape.RECTANGLE:
            i_MAX = (N-p)+1
            j_MAX = (M-q)+1
        elif shape == Shape.ROW:
            i_MAX = (N)
            j_MAX = (M-(p*q)+1)
        elif shape == Shape.COLUMN:
            i_MAX = (N-(p*q)+1)
            j_MAX = (M)
        elif shape == Shape.TRANSPOSED_RECTANGLE:
            i_MAX = (N-q+1)
            j_MAX = (M-p+1)
        elif shape == Shape.MAIN_DIAGONAL:
            i_MAX = (N-(p*q)+1)
            j_MAX = (M-(p*q)+1)
        elif shape == Shape.SECONDARY_DIAGONAL:
            j_MIN = (p*q)
            i_MAX = (N-(p*q)+1)
            j_MAX = (M)
        else:
            print "possibleCoverage: Unrecognized Shape"
            
        for i in range(i_MIN,i_MAX):
            for j in range(j_MIN,j_MAX):
                #res.append(AGU(i,j,p,q,shape))
                #par_accs.append((i,j,shape))
                res.append(((i,j,shape),AGU(i,j,p,q,shape)))
    return res

#Takes the output of possibleCoverage and removes all the element that do not appear in the list of active points
#The result is filtered, removing all the emtpy lists and all the duplicates
def removeNotActivePoints(activePoints,possibleCoverages):
    filteredCoverage = list(possibleCoverages)
    for coverage in filteredCoverage:
        c = []
        for element in coverage:
            if not element in activePoints:
                c.append(element)
        for toRemove in c:
            coverage.remove(toRemove)
    #Removes empty lists
    filteredCoverage = [x for x in filteredCoverage if x != []]
    #Removes duplicates
    filteredCoverage.sort()
    filteredCoverage = list(filteredCoverage for filteredCoverage,_ in itertools.groupby(filteredCoverage))
    return filteredCoverage

#Required to use the set as the set of possible solutions in the pulp implementation of the ILP problem.
def listOfListToListOfTuples(listOfList):
    listOftuple = []
    for list_el in listOfList:
        listOftuple.append(tuple(list_el))
    return listOftuple

def CoverageToParallelAccess(N, M, p, q, scheme,coverage):
    if isinstance(scheme,list):
        shapes = scheme
    elif isinstance(scheme,MappingScheme):
        shapes = availableShapes[scheme]
    else:
        print "This function accepts either a MappingScheme either a list of Shape"
        return []

    res = []
    for shape in shapes:
        i_MAX = 0
        j_MAX = 0
        i_MIN = 0
        j_MIN = 0
        if shape == Shape.RECTANGLE:
            i_MAX = (N-p)+1
            j_MAX = (M-q)+1
        elif shape == Shape.ROW:
            i_MAX = (N)
            j_MAX = (M-(p*q)+1)
        elif shape == Shape.COLUMN:
            i_MAX = (N-(p*q)+1)
            j_MAX = (M)
        elif shape == Shape.TRANSPOSED_RECTANGLE:
            i_MAX = (N-q+1)
            j_MAX = (M-p+1)
        elif shape == Shape.MAIN_DIAGONAL:
            i_MAX = (N-(p*q)+1)
            j_MAX = (M-(p*q)+1)
        elif shape == Shape.SECONDARY_DIAGONAL:
            j_MIN = (p*q)
            i_MAX = (N-(p*q)+1)
            j_MAX = (M)
        else:
            print "possibleCoverage: Unrecognized Shape"
            
        for i in range(i_MIN,i_MAX):
            for j in range(j_MIN,j_MAX):
                found=1
                currentCover = AGU(i,j,p,q,shape)
                for c in coverage:
                    if c not in currentCover:
                        found = 0
                if found:
                    return (i,j, shape)
    return (-1,-1,0)

def check_solution_existence(activePoints, possible_coverages):
    compound = []
    for coverage in possible_coverages:
        compound = compound + coverage

    compound = set(compound)
    set_active_points = set(activePoints)
    if compound <= set_active_points and set_active_points<= compound:
        return True
    else:
        return False

def solveEuristically(activePoints,p,q,scheme):
    print "Solving Euristically..."
    dimensions = find_matrix_dimension(activePoints,p,q)
    print "Computing the possible coverages"
    sets = possibleCoverage(dimensions[0],dimensions[1],p,q,scheme)
    toCover = list(activePoints)
    cover_solution=[]
    unuseful_sets=[]
    set_bins=[[] for i in range(p*q)]
    print "Starting the search"
    while not sets == [] and not toCover == []: #This step will pick all the cover with score p*q and sort the covers in bins
        s=sets.pop(0)
        score=len(list(set(s).intersection(toCover)))
        #print "Access "+str(len(cover_solution))+" current_score: "+str(score)
        if score == p*q:
            cover_solution.append(s)
            print s
            toCover = [item for item in toCover if item not in s]
        if not score == 0:
            set_bins[score].append(s)
    #this step goes over the bins, select the cover that match the bin id and reorders the others

    for bin_id in range(p*q-1,0,-1):
        print "Going over set bin "+str(bin_id)
        while not set_bins[bin_id]==[] and not toCover == []:
            s=set_bins[bin_id].pop(0)
            score=len(list(set(s).intersection(toCover)))
            #print "Access "+str(len(cover_solution))+" current_score: "+str(score)
            if score == bin_id:
                cover_solution.append(s)
                print s
                toCover = [item for item in toCover if item not in s]
            if not score ==0:
                set_bins[score].append(s)
    if not toCover == []:
        print "The following elements could not be covered:"
        print toCover
        print "The solution found was:"
        print cover_solution
        print "NOT all the elements have been covered:"
        return []
    else:
        print "All the elements have been covered:"
        print cover_solution
        print "All the elements have been covered"
    final_coverage=[]
    for c in cover_solution:
        UPA = CoverageToParallelAccess(dimensions[0],dimensions[1],p,q,scheme,c)
        shape = UPA[2]
        point=(UPA[0],UPA[1])
        if not isinstance(shape,Shape):
            print "Error converting: " +c+" returned: "+UPA
        print str(point)+", "+ str(shape.name)+" -> "+str(AGU(point[0],point[1],p,q,shape))
        final_coverage.append((point[0],point[1],shape))
    return final_coverage

def solveEuristically_getParallelAccesses(activePoints,p,q,scheme):
    print "Solving Euristically..."
    dimensions = find_matrix_dimension(activePoints,p,q)
    print "Computing the possible coverages"
    #sets = possibleCoverage(dimensions[0],dimensions[1],p,q,scheme)
    sets = possibleCoverage_and_ParallelAccesses(dimensions[0],dimensions[1],p,q,scheme)
    toCover = list(activePoints)
    cover_solution=[]
    unuseful_sets=[]
    set_bins=[[] for i in range(p*q)]
    print "Starting the search"
    while not sets == [] and not toCover == []: #This step will pick all the cover with score p*q and sort the covers in bins
        s=sets.pop(0)
        covered=list(set(s[1]).intersection(toCover))
        score=len(covered)

        #print "Access "+str(len(cover_solution))+" current_score: "+str(score)
        if score == p*q:
            cover_solution.append((s[0],covered))
            print s[1]
            toCover = [item for item in toCover if item not in s[1]]
        elif not score == 0:
            set_bins[score].append(s)
    #this step goes over the bins, select the cover that match the bin id and reorders the others

    for bin_id in range(p*q-1,0,-1):
        print "Going over set bin "+str(bin_id)
        while not set_bins[bin_id]==[] and not toCover == []:
            s=set_bins[bin_id].pop(0)
            covered=list(set(s[1]).intersection(toCover))
            score=len(covered)
            #print "Access "+str(len(cover_solution))+" current_score: "+str(score)
            if score == bin_id:
                cover_solution.append((s[0],covered))
                print s[1]
                toCover = [item for item in toCover if item not in s[1]]
            if not score ==0:
                set_bins[score].append(s)
    if not toCover == []:
        print "The following elements could not be covered:"
        print toCover
        print "The solution found was:"
        print cover_solution
        print "NOT all the elements have been covered:"
        return []
    else:
        print "All the elements have been covered:"
        print cover_solution
        print "All the elements have been covered"
    final_coverage=[]
    for c in cover_solution:
        UPA = c[0] 
        shape = UPA[2]
        point=(UPA[0],UPA[1])
        if not isinstance(shape,Shape):
            print "Error converting: " +c+" returned: "+UPA
        #print str(point)+", "+ str(shape.name)+" -> "+str(AGU(point[0],point[1],p,q,shape))
        mask=[]
        sys.stdout.write(str(point)+", "+ str(shape.name)+" -> "+"[")
        for element in  AGU(point[0],point[1],p,q,shape):
            if element in c[1]:
                    sys.stdout.write("\033[1;31m"+str(element)+"\033[1;m,")
                    mask.append(1)
            else:
                    sys.stdout.write(str(element)+",")
                    mask.append(0)
        print("]")
        print "DEBUG adding to coverage "+str( ((point[0],point[1],shape),mask))
        final_coverage.append(((point[0],point[1],shape),mask))
       # print "DEBUG adding to coverage "+str( ((point[0],point[1],shape),mask))
    return final_coverage


#Given a set of activePoints, the PRF dimensions, and a mapping scheme
#returns the optimal solution to the covering problem
def solveOptimally(activePoints,p,q,scheme,shutup=1):
    #define the minimum size of the input matrix such that it contains
    #all the active points and has a padding of p*q on the top and right
    # (this to enable the use of parellel access in the borders)
    dimensions = find_matrix_dimension(activePoints,p,q)
    sets = possibleCoverage(dimensions[0],dimensions[1],p,q,scheme)
    possible_coverages = removeNotActivePoints(activePoints,sets)



    possible_coverages_tuple = listOfListToListOfTuples(possible_coverages)
    x = pulp.LpVariable.dicts('coverage', possible_coverages_tuple, 
                                lowBound = 0,
                                upBound = 1,
                                cat = pulp.LpInteger)

    set_covering_model = pulp.LpProblem("Set Covering Problem", pulp.LpMinimize)

    #Minimize the number of sets used
    set_covering_model += sum([x[coverage] for coverage in possible_coverages_tuple])

    #An active point must be covered by at least one set
    for point in activePoints:
        set_covering_model += sum([x[coverage] for coverage in possible_coverages_tuple
                                    if point in coverage]) >= 1, "Must_cover_"+str(point)

    set_covering_model.solve()
    if(not shutup):
        print "The choosen coverages are out of a total of %s:"%len(possible_coverages_tuple)
    solution = []
    for coverage in possible_coverages_tuple:
        if x[coverage].value() == 1.0:
            if(not shutup):
                print coverage
            solution.append(coverage)
    if(not shutup):
        print "Converted in Parallel access, total of "+str(len(solution))+" accesses:"
    final_coverage=[]
    for c in solution:
        UPA = CoverageToParallelAccess(dimensions[0],dimensions[1],p,q,scheme,c)
        shape = UPA[2]
        point=(UPA[0],UPA[1])
        if not isinstance(shape,Shape):
            print "Error converting: " +c+" returned: "+UPA
        if(not shutup):
            print str(point)+", "+ str(shape.name)+" -> "+str(AGU(point[0],point[1],p,q,shape))
        final_coverage.append(AGU(point[0],point[1],p,q,shape))
    return final_coverage

def view_atrace_string(atrace_string,title="NoTitle",dimx=0,dimy=0):
    atrace =   parseATraceFromString(atrace_string)
    if dimx ==0:
        dim = find_plot_dimension(atrace)
    else:
        dim = (dimx,dimy)
    raw_image = create_plane_image(dim)
    plot_array(raw_image, atrace[0], title)



if __name__ == "__main__":
    function_map = { 
	'viewTrace': plot_array,
	#'conv': convertFile,
    }
    parser = argparse.ArgumentParser()
    parser.add_argument( 'command', nargs=1 )
    parser.add_argument( 'fileName', nargs='+' )
    args= parser.parse_args()
    parallelAccesses = parseATrace(args.fileName[0]);
    dimensions = find_plot_dimension(parallelAccesses)
    rawImage = create_plane_image(dimensions)
    function = function_map[args.command[0]]
    function( rawImage, parallelAccesses[0], "ATrace View")
