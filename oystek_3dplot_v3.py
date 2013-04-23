#import pylab as pl

from mpl_toolkits.mplot3d import axes3d
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import re

#===========================================
# CONSTANTS
#===========================================
radius = 135.2
num_plots = 20       # first n oysters with individual view plots
num_plots_AiO = 20 # first n oyster with 4-in-1 view plot
num_samples = 700000
h1 = 0.0153 # m, distance between to photo-diodes
g = 9.8     # m/s2, gravitational constant
d = 0.0025  # m, distance between CCD and bottom photo-diode. CCD above the bottom photo-diode.
#scan_steps = 115
#step_width = 2.2
line_scan = 0.000276
#line_scan = scan_steps * step_width * 10**(-6)  # seconds, length in time of 1 CCD scanline
#line_scan = 0.000253 # = 115 * 2.2

Xmin_correction = 5
Xmax_correction = 3

n_registers = 16
n_images = 4
n_rows = 256
n_cols = 7*16
lines_buff_min = 10
lines_buff_max = 7
point_size = 1

# index to array oyster_feature[i] (registers set)
#MinY = 2
#MaxY = 3
MinX = 4
MaxX = 5
#MinX_of_MinY = 6
#MaxX_of_MinY = 7
#MinX_of_MaxY = 8
#MaxX_of_MaxY = 9
MinY_of_MinX = 10
MaxY_of_MinX = 11
MinY_of_MaxX = 12
MaxY_of_MaxX = 13

# indexes to array adjust 
MinY = 0
MaxY = 1
MinX_of_MinY = 2
MaxX_of_MinY = 3
MinX_of_MaxY = 4
MaxX_of_MaxY = 5


#===========================================
#===========================================
# GLOBAL VARIABLES:
#   oyster_images, oyster_features, oyster_velocity, oyster_length, oyster_grade, \
#   fin, fout, current_line, num_oysters, scatter_x, scatter_y, contour_x, contour_y, \
#   adjust, maxDiagonal, len_nlines_ratio, dots_count, volume
#===========================================
#===========================================


# initialize global variables
def oystek_reset(fname):
  global oyster_images, oyster_features, oyster_velocity, oyster_length, oyster_grade, \
         fin, fout, current_line, num_oysters, scatter_x, scatter_y, contour_x, contour_y, \
         adjust, maxDiagonal, len_nlines_ratio, dots_count, volume

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
  adjust = [([0] * 6) for _ in range(n_images)]
# volume = [[],[],[]]
  volume = [[[],[],[]],[[],[],[]],[[],[],[]],[[],[],[]]]
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

# i: image number
# j: line number
# k: character index in line
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
    #oyster_features[i][MinY_of_MinX] = 0
    #oyster_features[i][MinY_of_MaxX] = 0
    
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
            #if ((oyster_features[i][MinY_of_MinX] == 0) and (k==(oyster_features[i][4]-Xmin_correction))):
            #  oyster_features[i][MinY_of_MinX]=j
            #if ((oyster_features[i][MinY_of_MaxX] == 0) and (k==(oyster_features[i][5]-Xmax_correction))):
            #  oyster_features[i][MinY_of_MaxX]=j

    len_nlines_ratio[i] = length_to_numlines_ratio(i)
    maxDiagonal[i] = find_max_diagonal(i)
  return


def plot_oyster_images():
  # only plot the first few oysters
  if (num_oysters>num_plots):
    return

  for i in range(len(oyster_images)):
    plt.scatter(scatter_x[i], scatter_y[i], s=1, color='lightgrey')
    plt.hold(True)
    plt.scatter(contour_x[i], contour_y[i], s=1, color='y')
    plt.xlabel('mm')
    plt.ylabel('# lines')
    image_title = 'oyster #'+str(num_oysters)+', image '+str(i+1)
    plt.title(image_title)
    annotate_text = ('dots='+str(int(oyster_features[i][0]))+
                     ', Ymin='+str(int(oyster_features[i][2]))+', Ymax='+str(int(oyster_features[i][3]))+
                     ', Xmin='+str(int(oyster_features[i][4]-Xmin_correction))+', Xmax='+str(int(oyster_features[i][5]-Xmax_correction))+
                     ',\nXmin_o_Ymin='+str(int(oyster_features[i][6]-Xmin_correction))+', Xmax_o_Ymin='+str(int(oyster_features[i][7]-Xmax_correction))+
                     ', Xmin_o_Ymax='+str(int(oyster_features[i][8]-Xmin_correction))+', Xmax_o_Ymax='+str(int(oyster_features[i][9]-Xmax_correction))+
                     ',\nYmin_o_Xmin='+str(int(oyster_features[i][10]))+', Ymax_o_Xmin='+str(int(oyster_features[i][11]))+
                     ', Ymin_o_Xmax='+str(int(oyster_features[i][12]))+', Ymax_o_Xmax='+str(int(oyster_features[i][13]))+
                     ',\ndelay='+str(int(oyster_velocity))+', Grade='+str(int(oyster_grade))+', Length='+str(int(oyster_length))
                    )
    plt.annotate(annotate_text, [5,-250],[5,-250])
    plt.grid(True)
    plt.xlim([0,n_cols-1])
    plt.ylim([-n_rows+1,0])
    plt.axes().set_aspect(len_nlines_ratio[i])
    plt.plot([0,n_cols-1],[-oyster_features[i][2],-oyster_features[i][2]], color='b')
    plt.plot([0,n_cols-1],[-oyster_features[i][3],-oyster_features[i][3]], color='b')
    plt.plot([oyster_features[i][4]-Xmin_correction,oyster_features[i][4]-Xmin_correction],[1-n_rows,0], color='b')
    plt.plot([oyster_features[i][5]-Xmax_correction,oyster_features[i][5]-Xmax_correction],[1-n_rows,0], color='b')

    #plt.plot([oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],[-oyster_features[i][11],-oyster_features[i][13]], color='r')
    #plt.plot([(oyster_features[i][6]+oyster_features[i][7]-11)/2,(oyster_features[i][8]+oyster_features[i][9]-11)/2],[-oyster_features[i][2],-oyster_features[i][3]], color='r')
    plt.plot([maxDiagonal[i][0],maxDiagonal[i][2]],[-maxDiagonal[i][1],-maxDiagonal[i][3]], color='r')

    plt.scatter([oyster_features[i][6]-Xmin_correction,oyster_features[i][7]-Xmax_correction,oyster_features[i][8]-Xmin_correction,oyster_features[i][9]-Xmax_correction,oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction,oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],\
               [-oyster_features[i][2],-oyster_features[i][2],-oyster_features[i][3],-oyster_features[i][3],-oyster_features[i][11],-oyster_features[i][13],-oyster_features[i][MinY_of_MinX],-oyster_features[i][MinY_of_MaxX]], color='k')
    #plt.scatter([oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],\
    #           [-oyster_features[i][MinY_of_MinX],-oyster_features[i][MinY_of_MaxX]], color='r')

    plt.scatter([adjust[i][MinX_of_MinY], adjust[i][MaxX_of_MinY], adjust[i][MinX_of_MaxY], adjust[i][MaxX_of_MaxY]], [-adjust[i][MinY], -adjust[i][MinY], -adjust[i][MaxY], -adjust[i][MaxY]], color='r')
    
    plt.hold(False)
    #plt.savefig(image_title+'.png')
    plt.show()
  return


# rotate (x,y) by angle a (in radian)
def rotate(a, x, y):
  xx = np.subtract(np.multiply(x,np.cos(a)), np.multiply(y,np.sin(a)))
  yy = np.add(np.multiply(x,np.sin(a)), np.multiply(y,np.cos(a)))
  return xx, yy


def point_on_contour(xy,z,i):
  if z>=len(oyster_images[i]):
    return False
  x = xy[0]
  y = xy[1]
  if i==0:
    return (oyster_images[0][z][x+n_cols/2] == '#') and (is_on_contour(0,z,x+n_cols/2) or is_on_contour(0,z,x+n_cols/2-1) or is_on_contour(0,z,x+n_cols/2+1) or is_on_contour(0,z+1,x+n_cols/2-1) or is_on_contour(0,z-1,x+n_cols/2-1))
  elif i==2:
    return (oyster_images[2][z][-y+n_cols/2] == '#') and (is_on_contour(2,z,-y+n_cols/2) or is_on_contour(2,z,-y+n_cols/2-1) or is_on_contour(2,z,-y+n_cols/2+1) or is_on_contour(2,z+1,-y+n_cols/2) or is_on_contour(2,z-1,-y+n_cols/2))
  elif i==1:
    return (oyster_images[1][z][-x+n_cols/2] == '#') and (is_on_contour(1,z,-x+n_cols/2)  or is_on_contour(1,z,-x+n_cols/2-1) or is_on_contour(1,z,-x+n_cols/2+1) or is_on_contour(1,z+1,-x+n_cols/2) or is_on_contour(1,z-1,-x+n_cols/2))
  elif i==3:
    return (oyster_images[3][z][-y+n_cols/2] == '#') and (is_on_contour(3,z,-y+n_cols/2) or is_on_contour(3,z,-y+n_cols/2-1) or is_on_contour(3,z,-y+n_cols/2+1) or is_on_contour(3,z+1,-y+n_cols/2) or is_on_contour(3,z-1,-y+n_cols/2))
  return False


def point_in_view(xy,z,i):
  if z>=len(oyster_images[i]):
    return False
  x = xy[0]
  y = xy[1]
  if i==0:
    return (oyster_images[0][z][x+n_cols/2] == '#')
  elif i==2:
    return (oyster_images[2][z][-y+n_cols/2] == '#')
  elif i==1:
    return (oyster_images[1][z][-x+n_cols/2] == '#')
  elif i==3:
    return (oyster_images[3][z][-y+n_cols/2] == '#')
  return False


def plot_oyster_3Dimages():
    global volume
    volume = [[[],[],[]],[[],[],[]],[[],[],[]],[[],[],[]]]
    
    # only plot the first few oysters
    if (num_oysters>num_plots):
      return

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    fig.subplots_adjust(left=0)
    fig.subplots_adjust(right=1.0)
    fig.subplots_adjust(bottom=0)
    fig.subplots_adjust(top=1.0)
    
    # images 1 & 3
    ax.scatter(contour_x[0]-n_cols*np.ones(len(contour_x[0]))/2, -radius*np.ones(len(contour_x[0])), contour_y[0], s=1, color='grey')
    ax.text(0, -radius, 0, "1", color='black')
    ax.scatter(contour_x[0]-n_cols*np.ones(len(contour_x[0]))/2,  radius*np.ones(len(contour_x[0])), contour_y[0], s=1, color='lightgrey')

    ax.scatter( radius*np.ones(len(contour_x[2])), n_cols*np.ones(len(contour_x[2]))/2 - contour_x[2], contour_y[2], s=1, color='grey')
    ax.text(radius, 0, 0, "3", color='black')
    ax.scatter(-radius*np.ones(len(contour_x[2])), n_cols*np.ones(len(contour_x[2]))/2 - contour_x[2], contour_y[2], s=1, color='lightgrey')

    # images 2 & 4. Rotate by 45 degree (pi/4) before display
    xx2, yy2 = rotate(np.pi/4, n_cols*np.ones(len(contour_x[1]))/2-contour_x[1], -radius*np.ones(len(contour_x[1])))
    ax.scatter(xx2, yy2, contour_y[1], s=1, color='grey')
    ax.text(radius*np.cos(np.pi/4), -radius*np.cos(np.pi/4), 0, "2", color='black')
    xx2p, yy2p = rotate(np.pi/4, n_cols*np.ones(len(contour_x[1]))/2 - contour_x[1],  radius*np.ones(len(contour_x[1])))
    ax.scatter(xx2p, yy2p, contour_y[1], s=1, color='lightgrey')

    xx4,  yy4  = rotate(np.pi/4,  radius*np.ones(len(contour_x[3])), n_cols*np.ones(len(contour_x[3]))/2-contour_x[3])
    ax.scatter(xx4,  yy4,  contour_y[3], s=1, color='grey')
    ax.text(radius*np.cos(np.pi/4), radius*np.cos(np.pi/4), 0, "4", color='black')
    xx4p, yy4p = rotate(np.pi/4, -radius*np.ones(len(contour_x[3])), n_cols*np.ones(len(contour_x[3]))/2 - contour_x[3])
    ax.scatter(xx4p, yy4p, contour_y[3], s=1, color='lightgrey')
    
    max_rows = max(adjust[i][MaxY] for i in range(4))
    min_rows = min(adjust[i][MinY] for i in range(4))
    #print 'max_rows=', max_rows, ', min_rows=', min_rows
    xxx= np.random.randint(-n_cols/2,  n_cols/2, num_samples)
    yyy= np.random.randint(-n_cols/2,  n_cols/2, num_samples)
    zzz= np.random.randint(-max_rows, -min_rows, num_samples)

    for x,y,z in zip(xxx,yyy,zzz):
      x1i, y1i = rotate(-np.pi/4, x, y)
      #x3i, y3i = rotate(np.pi/4, x, y)
      x3i, y3i = x1i, y1i
      if (x1i<-n_cols/2) or (x1i>=n_cols/2) or \
         (y1i<-n_cols/2) or (y1i>=n_cols/2) or \
         (x3i<-n_cols/2) or (x3i>=n_cols/2) or \
         (y3i<-n_cols/2) or (y3i>=n_cols/2) :
        continue
      if (point_on_contour([x,y],-z,0) and point_on_contour([int(x1i),int(y1i)],-z,1) and point_in_view([x,y],-z,2) and point_in_view([int(x1i),int(y1i)],-z,3)):
        volume[0][0].append(x)
        volume[0][1].append(y)
        volume[0][2].append(z)
      if (point_on_contour([int(x1i),int(y1i)],-z,1) and point_on_contour([x,y],-z,2) and point_in_view([int(x1i),int(y1i)],-z,3) and point_in_view([x,y],-z,0)):
        volume[1][0].append(x)
        volume[1][1].append(y)
        volume[1][2].append(z)
      if (point_on_contour([x,y],-z,2) and point_on_contour([int(x1i),int(y1i)],-z,3) and point_in_view([x,y],-z,0) and point_in_view([int(x1i),int(y1i)],-z,1)):
        volume[2][0].append(x)
        volume[2][1].append(y)
        volume[2][2].append(z)
      if (point_on_contour([int(x1i),int(y1i)],-z,3) and point_on_contour([x,y],-z,0) and point_in_view([int(x1i),int(y1i)],-z,1) and point_in_view([x,y],-z,2)):
        volume[3][0].append(x)
        volume[3][1].append(y)
        volume[3][2].append(z)

    ax.scatter(volume[0][0], volume[0][1], volume[0][2], s=point_size, color='red' )
    ax.scatter(volume[1][0], volume[1][1], volume[1][2], s=point_size, color='green' )
    ax.scatter(volume[2][0], volume[2][1], volume[2][2], s=point_size, color='blue' )
    ax.scatter(volume[3][0], volume[3][1], volume[3][2], s=point_size, color='black' )

    ax.set_xlim3d(-radius, radius)
    ax.set_ylim3d(-radius, radius)
    ax.set_zlim3d(-n_rows, 0)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    image_title = 'oyster #'+str(num_oysters)
    plt.title(image_title)
    plt.grid(False)
    plt.show(block=True)
    return



def plot_oyster_images_AiO():
  # only plot the first few oysters
  if (num_oysters>num_plots_AiO):
    return

  f, axarr = plt.subplots(2, 2)

  for i in range(n_images):
    axarr[i/2,i%2].scatter(scatter_x[i], scatter_y[i], color='lightgrey')
    axarr[i/2,i%2].hold(True)
    axarr[i/2,i%2].scatter(contour_x[i], contour_y[i], color='y')
    if (i==1 or i==3):
      plt.setp( axarr[i/2,i%2].axes.get_yticklabels(), visible=False)
    if (i==0 or i==1):
      plt.setp( axarr[i/2,i%2].axes.get_xticklabels(), visible=False)
    if (i==0):
      axarr[i/2,i%2].set_title('oyster #'+str(num_oysters)+', length='+str(int(max(maxDiagonal[j][4] for j in range(4))))+'mm')

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

    axarr[i/2,i%2].scatter([oyster_features[i][6]-Xmin_correction,oyster_features[i][7]-Xmax_correction,oyster_features[i][8]-Xmin_correction,oyster_features[i][9]-Xmax_correction,oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction,oyster_features[i][4]-Xmin_correction,oyster_features[i][5]-Xmax_correction],\
                           [-oyster_features[i][2],-oyster_features[i][2],-oyster_features[i][3],-oyster_features[i][3],-oyster_features[i][11],-oyster_features[i][13],-oyster_features[i][MinY_of_MinX],-oyster_features[i][MinY_of_MaxX]], color='k')
    axarr[i/2,i%2].scatter([adjust[i][MinX_of_MinY], adjust[i][MaxX_of_MinY], adjust[i][MinX_of_MaxY], adjust[i][MaxX_of_MaxY]], [-adjust[i][MinY], -adjust[i][MinY], -adjust[i][MaxY], -adjust[i][MaxY]], color='r')

    axarr[i/2,i%2].annotate(str(i+1), [5,-250],[5,-250], color = 'r')
    axarr[i/2,i%2].hold(False)
  f.subplots_adjust(hspace=0.01)
  f.subplots_adjust(wspace=0.01)
  #plt.savefig(image_title+'.png')
  plt.show(block=False)
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
  t3 = t2 + (adjust[i][MaxY]-adjust[i][MinY]+1) * line_scan
  h3 = v0 * t3 + 0.5*g*t3**2
  h23 = (h3-h2)*1000 # mm
  return h23 / (adjust[i][MaxY]-adjust[i][MinY]+1)


#distance between 2 points (x1,y1) and (x2,y2)
def distance(x1,y1,x2,y2,yscale):
  return ((abs(x1-x2)+1)**2 + ((abs(y1-y2)+1)*yscale)**2)**0.5


def find_max_diagonal(i):
  dmax = 0
  pairs = [ \
    [adjust[i][MinX_of_MaxY], adjust[i][MaxY], oyster_features[i][MaxX]-Xmax_correction, oyster_features[i][MinY_of_MaxX]],\
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MaxY_of_MinX], adjust[i][MaxX_of_MinY], adjust[i][MinY]],\
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MinY_of_MinX], adjust[i][MaxX_of_MaxY], adjust[i][MaxY]],\
    [adjust[i][MinX_of_MinY], adjust[i][MinY], oyster_features[i][MaxX]-Xmax_correction, oyster_features[i][MaxY_of_MaxX]],\
    
    [adjust[i][MinX_of_MinY], adjust[i][MinY], adjust[i][MaxX_of_MaxY], adjust[i][MaxY]],\
    [adjust[i][MaxX_of_MinY], adjust[i][MinY], adjust[i][MinX_of_MaxY], adjust[i][MaxY]],\
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MaxY_of_MinX], oyster_features[i][MaxX]-Xmax_correction, oyster_features[i][MinY_of_MaxX]],\
    [oyster_features[i][MinX]-Xmin_correction, oyster_features[i][MinY_of_MinX], oyster_features[i][MaxX]-Xmax_correction, oyster_features[i][MaxY_of_MaxX]]\
  ]
  for [x1,y1,x2,y2] in pairs:
    dtemp = distance(x1,y1, x2,y2,len_nlines_ratio[i])
    #print 'view #%d'%(i+1), x1, y1, x2,y2, ', length=%d'%dtemp
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
  print 'estimated length=%d'%(max(maxDiagonal[i][4] for i in range(4)))
  return


def oystek_start(fname):
  global num_oysters

  plt.ioff()  # interactive

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
    #plot_oyster_images()
    plot_oyster_images_AiO()
    plot_oyster_3Dimages()
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
#oystek_start(u"1sample.log")
oystek_start(u"28Mar13\\97mm Wide Oyster Random x20 2013-Mar-28.log")
