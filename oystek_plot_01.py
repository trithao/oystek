from matplotlib import *
import pylab

# CONSTANTS
n_registers = 16
n_images = 4
n_rows = 256
n_cols = 16 * 7

# GLOBAL VARS
#oyster_images= numpy.zeros([n_images, n_rows, n_cols])
oyster_images = [[], [], [], []]
oyster_dim = numpy.zeros(n_registers)
oyster_velocity = 0
oyster_length = 0
oyster_grade = 0
fin = 0
fout = 0


def fetch_image(fin, i):
  oyster_images[i] = []
  # oyster image starts with the line: 'i:\n'
  # immediately followed by a line with length == 112 chars (plus '\n')
  print 'image #', i
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if (len(aline) == 113):
      # correct length, consider as an image scan line
      oyster_images[i] += [aline]
    else:
      current_line = aline
      break
  
  return True


def fetch_dimension(fin, i):
  # oyster dimensions immediately follow the images,
  # starts with the line: 'i:\n'
  # and immediately followed by a line starts with 'Reg 0 = '
  print 'Registers set #',i
  reg = 0
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if ((len(aline) < 20) and (len(aline)>3) and aline[0] == 'R'):
      # correct length, consider as register
      reg += 1 
      #print 'register #',reg, aline
    else:
      current_line = aline
      break
  return True


def fetch_velocity():
  # velocity (delay) immediately follow dimension
  # the line has format: '%d %d\n'
  return True


def fetch_grade_and_length():
  # line starts with '>%'
  return True


def fetch_1_oyster(fin):
  # input 1 oyster info from file
  # save oyster's dimension and velocity to a text tabular format for post-processing by Excel
  
  # images
  for i in range(n_images):
    if( fetch_image(fin, i) == False):
      return False

  # dimensions
  for i in range(n_images):
    if (fetch_dimension(fin, i) == False):
      return False

  # velocity, delay
  if (fetch_velocity() == False):
    return False

  # grade and length
  if (fetch_grade_and_length() == False):
    return False
  
  return True

##  while (stat==True):
##    str = fin.readline()
##    if str == '':
##      stat=False
##      break
##    count += 1
##
##    if str.__subclasshook__
##
##  print 'lines count: ', count
##  #return stat, oyster_dim, oyster_images, oyster_velocity
##  return stat


def plot_oyster_images():
  return
##  for i in range(n_images):
##    #pylab.scatter(oyster_images[i].T[0], oyster_images[i].T[0])
##    #pylab.show()
##    # wait for a CR then plot the next image
##    # plot all images in one window
##  return


##def fetch_1_oyster_interactive():
##  # wait for and get oyster data from COM port
##  # interactive / blocking I/O operation
##  return oyster_dim, oyster_images, oyster_velocity

def skip_to_image(fin):
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if (aline == '1:\n'):
      break
  return

def oystek_start(fname):
  # initialize
  pylab.ioff()  # interactive 
  fin  = open(fname, 'r')        # error check and handle?!
  fout = open(fname+'.out', 'w') # error check and handle?!
  num_oysters = 0
  
  skip_to_image(fin)
  
  while (True):  
    if (fetch_1_oyster(fin) != True):
      break
    num_oysters += 1
    print 'oyster #', num_oysters
    plot_oyster_images()

  # clean up before exit
  fin.close()
  fout.close()
  print 'total $ oysters: ', num_oysters
  return
  
##def oystek_start_interactive():
##  return


#oystek_start('74mm wooden 100x random orientation.log')
oystek_start('sample.log')

