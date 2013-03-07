from matplotlib import *

n_registers = 16
oyster_dim = numpy.zeros(n_registers)

n_images = 4
n_rows = 256
n_cols = 16 * 7
oyster_images= numpy.zeros([n_images, n_rows, n_cols])

oyster_velocity = 0

def oystek_init(fname):
  fin  = open(fname, 'r')
  fout = open(fname+'.out', 'w')
  return fin, fout

def fetch_1_oyster(fin, fout):
  # input 1 oyster info from file
  # save oyster's dimension and velocity to a text tabular format for post-processing by Excel
  return oyster_dim, oyster_images, oyster_velocity

def plot_oyster_images():
  for i in range(n_images):
    pyplot.scatter(oyster_images[i].T[0], oyster_images[i].T[0])
    # wait for a CR then plot the next image
  # plot all images in one window
  return

def fetch_1_oyster_interactive():
  # wait for and get oyster data from COM port
  # interactive / blocking I/O operation
  return oyster_dim, oyster_images, oyster_velocity

def oystek_start(fname):
  fin, fout = oystek_init(fname)
  while (1):  
  # read data till EOF
  fin.close()
  fout.close()
  return
  
def oystek_start_interactive():
  return


