from matplotlib import *
import numpy
import pylab
import re


# CONSTANTS
n_registers = 16
n_images = 4
n_rows = 256
n_cols = 7*16

# GLOBAL VARS
oyster_images = [[] for _ in range(n_images)]
oyster_dim = [numpy.zeros(n_registers) for _ in range(n_images)]
oyster_velocity = 0
oyster_length = 0
oyster_grade = 0
fin = 0
fout = 0
current_line = ''
num_oysters = 0

def fetch_image(i):
  global oyster_image
  oyster_images[i] = []
  # oyster image starts with the line: 'i:\n'
  # immediately followed by a line with length == 112 chars (plus '\n')
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if (len(aline) == 113):
      # correct length, consider as an image scan line
      oyster_images[i] = oyster_images[i]+[aline]
    else:
      break
  print 'image #', i, ', ', len(oyster_images[i]), ' lines'
##  for el in oyster_images[i]:
##    print el  
  return True


def fetch_dimension(i):
  global oyster_dim
  global current_line
  # oyster dimensions immediately follow the images,
  # starts with the line: 'i:\n'
  # and immediately followed by a line starts with 'Reg 0 = '
  r = re.compile('[ =]+')
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if ((len(aline) < 20) and (len(aline)>3) and aline.find('Reg ')==0):
      # correct length and pattern, consider as register
      _, regno, val = r.split(aline)
      oyster_dim[i][int(regno)] = int(val)
      #print 'register #',reg, aline
    else:
      # not recognize pattern, save for the next field
      current_line = aline
      #print 'ohoh...', current_line
      break
  print 'Registers set #',i
  print oyster_dim[i]
  return True


def fetch_velocity():
  global oyster_velocity
  # velocity (delay) immediately follow dimension
  # the line has format: '%d %d\n'
  velocity, _ = re.split(' ', current_line)
  oyster_velocity = int(velocity)
  print 'oyster velocity (delay):', oyster_velocity
  return True


def fetch_grade_and_length():
  global oyster_grade
  global oyster_length
  # line starts with '>%'
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if (aline.find('>%') == 0):
      p = re.split(',',aline)
      oyster_grade = int(p[2])
      oyster_length = float(p[3])
      print 'oyster_grade=', oyster_grade, ', oyster_length=', oyster_length
      break
  return True


def fetch_1_oyster():
  # input 1 oyster info from file
  # save oyster's dimension and velocity to a text tabular format for post-processing by Excel
  
  # images
  for i in range(n_images):
    if(fetch_image(i) == False):
      return False

  # dimensions
  for i in range(n_images):
    if (fetch_dimension(i) == False):
      return False

  # velocity, delay
  if (fetch_velocity() == False):
    return False

  # grade and length
  if (fetch_grade_and_length() == False):
    return False
  
  return True


def plot_oyster_images():

##  for i in range(n_images):
##    print 'image #', i
##    for ln in oyster_images[i]:
##      ln = ln[0:len(ln)-1] # remove '\n' at the end
##      print ln

  # convert to scatter form
  
  for i in range(len(oyster_images)):
    # for each image
    scatter_x = []
    scatter_y = []
    for j in range(len(oyster_images[i])):
    # for each line
      for k in range(len(oyster_images[i][j])-1):
      # for each dot on the line
        if (oyster_images[i][j][k] == '#'):
          scatter_x.append(k)
          scatter_y.append(-j)
    pylab.scatter(scatter_x, scatter_y)
    pylab.xlabel('mm')
    pylab.ylabel('# lines')
    image_title = 'oyster #'+str(num_oysters)+', image '+str(i+1)
    pylab.title(image_title)
    pylab.grid(True)
    #pylab.savefig(image_title+'.png')
    pylab.ylim([-255,0])
    pylab.xlim([0,111])
    pylab.show()

    # plot all images in one window
    
  return


def skip_to_image():
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if (aline == '1:\n'):
      break
    #print 'skipped: ',aline
  return True


def log_to_file():
  for i in range(n_images):
    for reg in oyster_dim[i]:
      fout.write(str(int(reg))+'\t')
    fout.write(str(oyster_velocity)+'\t'+str(oyster_grade)+'\t'+str(int(oyster_length))+'\n')
  return True


def oystek_start(fname):
  global fin
  global fout
  global num_oysters
  # initialize
  pylab.ioff()  # interactive 
  fin  = open(fname, 'r')        # error check and handle?!
  fout = open(fname+'.out', 'w') # error check and handle?!
  
  while (True):  
    if (skip_to_image() != True):
      break
    if (fetch_1_oyster() != True):
      break
    log_to_file()
    num_oysters += 1
    print 'oyster #', num_oysters, ' fetched\n'
    #plot_oyster_images()

  # clean up before exit
  fin.close()
  fout.close()
  print '\ntotal # oysters: ', num_oysters
  return
  
##def oystek_start_interactive():
##  return


#oystek_start('74mm wooden 100x random orientation.log')
oystek_start('sample_4.log')

