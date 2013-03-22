#import pylab as pl
import matplotlib.pyplot as pl
import re

#===========================================
# CONSTANTS
#===========================================

num_plots = 2       # first n oysters with individual view plots
num_plots_AiO = 100 # first n oyster with 4-in-1 view plot

h1 = 0.0153 # m, distance between to photo-diodes
g = 9.8     # m/s2, gravitational constant
d = 0.0025  # m, distance between CCD and bottom photo-diode. CCD above the bottom photo-diode.
scan_steps = 115
step_width = 2.2
line_scan = scan_steps * step_width * 10**(-6)  # seconds, length in time of 1 CCD scanline
#line_scan = 0.000253 # = 115 * 2.2

Xmin_correction = 8
Xmax_correction = 3

n_registers = 16
n_images = 4
n_rows = 256
n_cols = 7*16
lines_buff_min = 10
lines_buff_max = 7

# index to array oyster_feature[i] (registers set)
MinX = 4
MaxX = 5
MaxY_of_MinX = 11
MaxY_of_MaxX = 13

# indexes to array adjust 
MinY = 0
MaxY = 1
MinX_of_MinY = 2
MaxX_of_MinY = 3
MinX_of_MaxY = 4
MaxX_of_MaxY = 5
MinY_of_MinX = 6
MinY_of_MaxX = 7


#===========================================
#===========================================
# GLOBAL VARIABLES:
#   oyster_images, oyster_features, oyster_velocity, oyster_length, oyster_grade, \
#   fin, fout, current_line, num_oysters, scatter_x, scatter_y, contour_x, contour_y, \
#   adjust, maxDiagonal, len_nlines_ratio, dots_count
#===========================================
#===========================================


# initialize global variables
def oystek_reset(fname):
  global oyster_images, oyster_features, oyster_velocity, oyster_length, oyster_grade, \
         fin, fout, current_line, num_oysters, scatter_x, scatter_y, contour_x, contour_y, \
         adjust, maxDiagonal, len_nlines_ratio, dots_count

  oyster_images = [[] for _ in range(n_images)]
  oyster_features = [([0] * n_registers) for _ in range(n_images)]
  oyster_velocity = 0
  oyster_length = 0
  oyster_grade = 0
  fin  = open(fname, 'r')        # error check and handle?!
  fout = open(fname+'.out', 'w') # error check and handle?!
  current_line = ''
  num_oysters = 0
  scatter_x = [[] for _ in range(n_images)]
  scatter_y = [[] for _ in range(n_images)]
  contour_x = [[] for _ in range(n_images)]
  contour_y = [[] for _ in range(n_images)]
  maxDiagonal = [[] for _ in range(n_images)]
  len_nlines_ratio = [0] * n_images
  dots_count =  [0] * n_images
  adjust = [([0] * 8) for _ in range(n_images)]
  return


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
  return True


def fetch_dimension(i):
  global oyster_features, current_line

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
      oyster_features[i][int(regno)] = int(val)
      #print 'register #',reg, aline
    else:
      # not recognize pattern, save for the next field
      current_line = aline
      break
  return True


def fetch_velocity():
  global oyster_velocity

  # velocity (delay) immediately follow dimension
  # the line has format: '%d %d\n'
  velocity, _ = re.split(' ', current_line)
  oyster_velocity = int(velocity)
  #print 'oyster velocity (delay):', oyster_velocity
  return True


def fetch_grade_and_length():
  global oyster_grade, oyster_length

  # line starts with '>%EG,'
  while (True):
    aline = fin.readline()
    if (aline == ''):
      return False
    if (aline.find('>%EG,') == 0):
      p = re.split(',',aline)
      oyster_grade = int(p[2])
      oyster_length = float(p[3])
      #print 'oyster_grade=', oyster_grade, ', oyster_length=', oyster_length
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

  print 'grade=', oyster_grade, ', length=', oyster_length
  print 'velocity (delay):', oyster_velocity
  return True


def is_on_contour(i,j,k):
  if ((k==0) or (j>oyster_features[i][3]+lines_buff_max) or (j<oyster_features[i][2]-lines_buff_min)):
    return False
  if ((j>0) and (oyster_images[i][j-1][k] == '#') and
      (j+2<len(oyster_images[i])) and (oyster_images[i][j+1][k] == '#') and
      (k>0) and (oyster_images[i][j][k-1] == '#') and
      (k+2<n_cols) and (oyster_images[i][j][k+1] == '#')):
    return False
  return True


# this is called each time an oyster is fetched
def prepare_scatter_images():
  global scatter_x, scatter_y, contour_x, contour_y, dots_count,\
         oyster_features, adjust, maxDiagonal, len_nlines_ratio
  
  scatter_x = [[] for _ in range(n_images)]
  scatter_y = [[] for _ in range(n_images)]
  contour_x = [[] for _ in range(n_images)]
  contour_y = [[] for _ in range(n_images)]
  # convert to scatter form
  for i in range(n_images):
    # for each image
    dots_count[i] = 0
    adjust[i][MinY] = 0
    adjust[i][MaxY] = 0
    adjust[i][MinX_of_MinY] = 0
    adjust[i][MaxX_of_MinY] = 0
    adjust[i][MinX_of_MaxY] = 0
    adjust[i][MaxX_of_MaxY] = 0
    adjust[i][MinY_of_MinX] = 0
    adjust[i][MinY_of_MaxX] = 0
    
    for j in range(len(oyster_images[i])):
    # for each line
      first_dot = False
      for k in range(len(oyster_images[i][j])-1):
      # for each dot on the line
        if (oyster_images[i][j][k] == '#'):
          # dot is marked '#', it's part of the oyster
          scatter_x[i].append(k)
          scatter_y[i].append(-j)
          dots_count[i] += 1
          # check if it's on contour
          if (is_on_contour(i,j,k)):
            contour_x[i].append(k)
            contour_y[i].append(-j)
            if (adjust[i][MinY] == 0):  # MinY detected
              adjust[i][MinY] = j
              if (adjust[i][MinX_of_MinY] == 0):
                adjust[i][MinX_of_MinY] = k
            if (j == adjust[i][MinY]):
              adjust[i][MaxX_of_MinY] = k
            # update MaxY
            adjust[i][MaxY] = j
            adjust[i][MaxX_of_MaxY] = k
            if (first_dot == False):
              adjust[i][MinX_of_MaxY] = k
              first_dot = True
            #check it's Ymin_of_Xmin or Ymin_of_Xmax
            if ((adjust[i][MinY_of_MinX] == 0) and (k==(oyster_features[i][4]-Xmin_correction))):
              adjust[i][MinY_of_MinX]=j
            if ((adjust[i][MinY_of_MaxX] == 0) and (k==(oyster_features[i][5]-Xmax_correction))):
              adjust[i][MinY_of_MaxX]=j

    len_nlines_ratio[i] = length_to_numlines_ratio(i)
    maxDiagonal[i] = find_max_diagonal(i)
  return


def plot_oyster_images():
  # only plot the first few oysters
  if (num_oysters>num_plots):
    return

  for i in range(len(oyster_images)):
    pl.scatter(scatter_x[i], scatter_y[i], color='lightgrey')
    pl.hold(True)
    pl.scatter(contour_x[i], contour_y[i], color='y')
    pl.xlabel('mm')
    pl.ylabel('# lines')
    image_title = 'oyster #'+str(num_oysters)+', image '+str(i+1)
    pl.title(image_title)
    annotate_text = ('dots='+str(int(oyster_features[i][0]))+
                     ', Ymin='+str(int(oyster_features[i][2]))+', Ymax='+str(int(oyster_features[i][3]))+
                     ', Xmin='+str(int(oyster_features[i][4]-Xmin_correction))+', Xmax='+str(int(oyster_features[i][5]-Xmax_correction))+
                     ',\nXmin_o_Ymin='+str(int(oyster_features[i][6]-Xmin_correction))+', Xmax_o_Ymin='+str(int(oyster_features[i][7]-Xmax_correction))+
                     ', Xmin_o_Ymax='+str(int(oyster_features[i][8]-Xmin_correction))+', Xmax_o_Ymax='+str(int(oyster_features[i][9]-Xmax_correction))+
                     ',\nYmin_o_Xmin='+str(int(oyster_features[i][10]))+', Ymax_o_Xmin='+str(int(oyster_features[i][11]))+
                     ', Ymin_o_Xmax='+str(int(oyster_features[i][12]))+', Ymax_o_Xmax='+str(int(oyster_features[i][13]))+
                     ',\ndelay='+str(int(oyster_velocity))+', Grade='+str(int(oyster_grade))+', Length='+str(int(oyster_length))
                    )
    pl.annotate(annotate_text, [5,-250],[5,-250])
    pl.grid(True)
    pl.xlim([0,n_cols-1])
    pl.ylim([-n_rows+1,0])
    pl.axes().set_aspect(len_nlines_ratio[i])
    pl.plot([0,n_cols-1],[-oyster_features[i][2],-oyster_features[i][2]], color='b')
    pl.plot([0,n_cols-1],[-oyster_features[i][3],-oyster_features[i][3]], color='b')
    pl.plot([oyster_features[i][4]-Xmin_correction,oyster_features[i][4]-Xmin_correction],[1-n_rows,0], color='b')
    pl.plot([oyster_features[i][5]-Xmax_correction,oyster_features[i][5]-Xmax_correction],[1-n_rows,0], color='b')

    #pl.plot([oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],[-oyster_features[i][11],-oyster_features[i][13]], color='r')
    #pl.plot([(oyster_features[i][6]+oyster_features[i][7]-11)/2,(oyster_features[i][8]+oyster_features[i][9]-11)/2],[-oyster_features[i][2],-oyster_features[i][3]], color='r')
    pl.plot([maxDiagonal[i][0],maxDiagonal[i][2]],[-maxDiagonal[i][1],-maxDiagonal[i][3]], color='r')

    pl.scatter([oyster_features[i][6]-Xmin_correction,oyster_features[i][7]-Xmax_correction,oyster_features[i][8]-Xmin_correction,oyster_features[i][9]-Xmax_correction,oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction], [-oyster_features[i][2],-oyster_features[i][2],-oyster_features[i][3],-oyster_features[i][3],-oyster_features[i][11],-oyster_features[i][13]], color='k')
    pl.scatter([oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],[-adjust[i][MinY_of_MinX],-adjust[i][MinY_of_MaxX]], color='r')

    pl.scatter([adjust[i][MinX_of_MinY], adjust[i][MaxX_of_MinY], adjust[i][MinX_of_MaxY], adjust[i][MaxX_of_MaxY]], [-adjust[i][MinY], -adjust[i][MinY], -adjust[i][MaxY], -adjust[i][MaxY]], color='r')
    
    pl.hold(False)
    #pl.savefig(image_title+'.png')
    pl.show()
  return


def plot_oyster_images_AiO():
  # only plot the first few oysters
  if (num_oysters>num_plots_AiO):
    return

  f, axarr = pl.subplots(2, 2)

  for i in range(n_images):
    axarr[i/2,i%2].scatter(scatter_x[i], scatter_y[i], color='lightgrey')
    axarr[i/2,i%2].hold(True)
    axarr[i/2,i%2].scatter(contour_x[i], contour_y[i], color='y')
    if (i==1 or i==3):
      pl.setp( axarr[i/2,i%2].axes.get_yticklabels(), visible=False)
    if (i==0 or i==1):
      pl.setp( axarr[i/2,i%2].axes.get_xticklabels(), visible=False)
    if (i==0):
      axarr[i/2,i%2].set_title('oyster #'+str(num_oysters))

    axarr[i/2,i%2].grid(True)
    axarr[i/2,i%2].set_ylim([-255,0])
    axarr[i/2,i%2].set_xlim([0,111])
    axarr[i/2,i%2].set_aspect(len_nlines_ratio[i])
    axarr[i/2,i%2].plot([0,111],[-oyster_features[i][2],-oyster_features[i][2]], color='b')
    axarr[i/2,i%2].plot([0,111],[-oyster_features[i][3],-oyster_features[i][3]], color='b')
    axarr[i/2,i%2].plot([oyster_features[i][4]-Xmin_correction,oyster_features[i][4]-Xmin_correction],[-255,0], color='b')
    axarr[i/2,i%2].plot([oyster_features[i][5]-Xmax_correction,oyster_features[i][5]-Xmax_correction],[-255,0], color='b')

    #axarr[i/2,i%2].plot([oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],[-oyster_features[i][11],-oyster_features[i][13]], color='r')
    #axarr[i/2,i%2].plot([(oyster_features[i][6]+oyster_features[i][7]-11)/2,(oyster_features[i][8]+oyster_features[i][9]-11)/2],[-oyster_features[i][2],-oyster_features[i][3]], color='r')
    axarr[i/2,i%2].plot([maxDiagonal[i][0],maxDiagonal[i][2]],[-maxDiagonal[i][1],-maxDiagonal[i][3]], color='r')

    axarr[i/2,i%2].scatter([oyster_features[i][6]-Xmin_correction,oyster_features[i][7]-Xmax_correction,oyster_features[i][8]-Xmin_correction,oyster_features[i][9]-Xmax_correction,oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction], [-oyster_features[i][2],-oyster_features[i][2],-oyster_features[i][3],-oyster_features[i][3],-oyster_features[i][11],-oyster_features[i][13]], color='k')
    axarr[i/2,i%2].scatter([oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],[-adjust[i][MinY_of_MinX],-adjust[i][MinY_of_MaxX]], color='r')
    axarr[i/2,i%2].scatter([adjust[i][MinX_of_MinY], adjust[i][MaxX_of_MinY], adjust[i][MinX_of_MaxY], adjust[i][MaxX_of_MaxY]], [-adjust[i][MinY], -adjust[i][MinY], -adjust[i][MaxY], -adjust[i][MaxY]], color='r')

    axarr[i/2,i%2].annotate(str(i+1), [5,-250],[5,-250], color = 'r')
    axarr[i/2,i%2].hold(False)
  f.subplots_adjust(hspace=0.01)
  f.subplots_adjust(wspace=0.01)
  #pl.savefig(image_title+'.png')
  pl.show()
  return

# 1st image of an oyster starts with '1:\n' string
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
    for reg in oyster_features[i]:
      fout.write(str(int(reg))+'\t')
    fout.write(str(oyster_velocity)+'\t'+str(oyster_grade)+'\t'+str(int(oyster_length)))
    for reg in adjust[i]:
      fout.write('\t'+str(reg))
    for val in maxDiagonal[i]:
      fout.write('\t'+str(val))
    fout.write('\n')
  return True


# Return length/numlines ratio, for image i
def length_to_numlines_ratio(i):
  t1 = oyster_velocity * 10.**(-6)  # delay second
  v0 = (h1 - 0.5*g*t1**2)/t1
  h2 = h1 - d
  v2 = (v0**2 + 2*g*h2)**0.5
  t2 = (v2 - v0) / g
  t3 = t2 + (adjust[i][MaxY]-adjust[i][MinY]) * line_scan
  h3 = v0 * t3 + 0.5*g*t3**2
  h23 = (h3-h2)*1000 # mm
  return h23 / (adjust[i][MaxY]-adjust[i][MinY]+1)


#distance between 2 points (x1,y1) and (x2,y2)
def distance(x1,y1,x2,y2):
  return ((abs(x1-x2)+1)**2 + (abs(y1-y2)+1)**2)**0.5


def find_max_diagonal(i):
  dmax = 0
  pairs = [ \
    [adjust[i][MinX_of_MaxY], adjust[i][MaxY], oyster_features[i][MaxX]-Xmax_correction, adjust[i][MinY_of_MaxX]], \
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MaxY_of_MinX], adjust[i][MaxX_of_MinY], adjust[i][MinY]],\
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MaxY_of_MinX], adjust[i][MaxX_of_MinY], adjust[i][MinY]],\
    [adjust[i][MinX_of_MinY], adjust[i][MinY], oyster_features[i][MaxX]-Xmax_correction, oyster_features[i][MaxY_of_MaxX]],\
    [adjust[i][MinX_of_MinY], adjust[i][MinY],adjust[i][MaxX_of_MaxY], adjust[i][MaxY]],\
    [adjust[i][MaxX_of_MinY], adjust[i][MinY],adjust[i][MinX_of_MaxY], adjust[i][MaxY]],\
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MaxY_of_MinX], oyster_features[i][MaxX]-Xmax_correction, adjust[i][MinY_of_MaxX]],\
    [oyster_features[i][MinX]-Xmin_correction, adjust[i][MinY_of_MinX], oyster_features[i][MaxX]-Xmax_correction, oyster_features[i][MaxY_of_MaxX]]\
  ]
  for [x1,y1,x2,y2] in pairs:
    dtemp = distance(x1,y1*len_nlines_ratio[i], x2,y2*len_nlines_ratio[i])
    if (dmax < dtemp):
      [dmax,xx1,yy1,xx2,yy2] = [dtemp,x1,y1,x2,y2]
  return [xx1,yy1,xx2,yy2,dmax]


##def find_max_diagonal_ALL():
##  global maxDiagonal, len_nlines_ratio
##  for i in range(n_images):
##    len_nlines_ratio[i] = length_to_numlines_ratio(i)
##    maxDiagonal[i] = find_max_diagonal(i)
##    print 'maxDiag=', maxDiagonal[i][0:4], ', length/nlines=%.4f'%len_nlines_ratio[i], ', length=%.1f'%maxDiagonal[i][4]
##  return


def print_measurement():
  for i in range(n_images):
    print 'View #%d:'%(i+1)
    print '  ', oyster_features[i]
    print '   dots count=%d'%dots_count[i], \
          ', num_lines=%d'%(adjust[i][MaxY] - adjust[i][MinY] + 1), \
          ', num_cols=%d'%((oyster_features[i][MaxX]-Xmax_correction) - (oyster_features[i][MinX]-Xmin_correction) + 1)
    print '  ', adjust[i]
    print '   maxDiag=', maxDiagonal[i][0:4], ', length/nlines=%.4f'%len_nlines_ratio[i], ', length=%.1f'%maxDiagonal[i][4]
  return


def oystek_start(fname):
  global num_oysters

  pl.ioff()  # interactive

  # initialize
  oystek_reset(fname)

  while (True):
    print '\nfetching oyster ', num_oysters+1, ' ...'
    if (skip_to_image() != True):
      break
    if (fetch_1_oyster() != True):
      break
    num_oysters += 1
    prepare_scatter_images()
    log_to_file()
    print_measurement()
    plot_oyster_images()
    plot_oyster_images_AiO()

  # clean up before exit
  fin.close()
  fout.close()
  print '\ntotal # oysters: ', num_oysters
  return


# To run interactively, from Python shell prompt, type:
#>>> from oystek_plot import *
#>>> oystek_start('sample.log')
#>>> oystek_start('sample_5.log')
#oystek_start('32mm X30 ball hand drop.log')
oystek_start('73.0mm Wooden Oyster.log')
