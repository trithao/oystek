import pylab
import re


# CONSTANTS
n_registers = 16
n_images = 4
n_rows = 256
n_cols = 7*16

# GLOBAL VARS
oyster_images = [[] for _ in range(n_images)]
oyster_dim = [([0] * n_registers) for _ in range(n_images)]
oyster_velocity = 0
oyster_length = 0
oyster_grade = 0
fin = 0
fout = 0
current_line = ''
num_oysters = 0
scatter_x = [[] for _ in range(n_images)]
scatter_y = [[] for _ in range(n_images)]
contour_x = [[] for _ in range(n_images)]
contour_y = [[] for _ in range(n_images)]

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
  #print 'image #', i, ', ', len(oyster_images[i]), ' lines'
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
  print 'Registers set #',i+1
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

def is_on_contour(i,j,k):
  if ((k==0) or (j>oyster_dim[i][3]+5)):
    return False
  if ((j>0) and (oyster_images[i][j-1][k] == '#') and
      (j+2<len(oyster_images[i])) and (oyster_images[i][j+1][k] == '#') and
      (k>0) and (oyster_images[i][j][k-1] == '#') and
      (k+2<n_cols) and (oyster_images[i][j][k+1] == '#')):
    return False
  return True

def prepare_scatter_images():
  global scatter_x
  global scatter_y
  global contour_x
  global contour_y
  
  scatter_x = [[] for _ in range(n_images)]
  scatter_y = [[] for _ in range(n_images)]
  contour_x = [[] for _ in range(n_images)]
  contour_y = [[] for _ in range(n_images)]
  # convert to scatter form  
  for i in range(n_images):
    dots = 0
    # for each image
    for j in range(len(oyster_images[i])):
    # for each line
      for k in range(len(oyster_images[i][j])-1):
      # for each dot on the line
        if (oyster_images[i][j][k] == '#'):
          # dot is marked '#', it's part of the oyster
          scatter_x[i].append(k)
          scatter_y[i].append(-j)
          dots += 1
          # check if it's on contour
          if (is_on_contour(i,j,k)):
            contour_x[i].append(k)
            contour_y[i].append(-j)
          

    print 'image #', i+1, 'dots count= ', dots
  return


def plot_oyster_images():
  # only plot the first few oysters
  if (num_oysters>7):
    return

  for i in range(len(oyster_images)):
    pylab.scatter(scatter_x[i], scatter_y[i], color='lightgrey')
    pylab.hold(True)
    pylab.scatter(contour_x[i], contour_y[i], color='y')
    pylab.xlabel('mm')
    pylab.ylabel('# lines')
    image_title = 'oyster #'+str(num_oysters)+', image '+str(i+1)
    pylab.title(image_title)
    annotate_text = ('dots='+str(int(oyster_dim[i][0]))+
                     ', Ymin='+str(int(oyster_dim[i][2]))+', Ymax='+str(int(oyster_dim[i][3]))+
                     ', Xmin='+str(int(oyster_dim[i][4]-8))+', Xmax='+str(int(oyster_dim[i][5]-3))+
                     ',\nXmin_o_Ymin='+str(int(oyster_dim[i][6]-8))+', Xmax_o_Ymin='+str(int(oyster_dim[i][7]-3))+
                     ', Xmin_o_Ymax='+str(int(oyster_dim[i][8]-8))+', Xmax_o_Ymax='+str(int(oyster_dim[i][9]-3))+
                     ',\nYmax_o_Xmin='+str(int(oyster_dim[i][11]))+', Ymax_o_Xmax='+str(int(oyster_dim[i][13]))+
                     ',\ndelay='+str(int(oyster_velocity))+', Grade='+str(int(oyster_grade))+', Length='+str(int(oyster_length))
                    )
    pylab.annotate(annotate_text, [5,-250],[5,-250])
    pylab.grid(True)
    pylab.xlim([0,111])  #pylab.xlim([ oyster_dim[i][4]-8-5, oyster_dim[i][5]-3+5])
    pylab.ylim([-255,0]) #pylab.ylim([-oyster_dim[i][2]+5,  -oyster_dim[i][3]-5])
    
    pylab.plot([0,111],[-oyster_dim[i][2],-oyster_dim[i][2]], color='b')
    pylab.plot([0,111],[-oyster_dim[i][3],-oyster_dim[i][3]], color='b')
    pylab.plot([oyster_dim[i][4]-8,oyster_dim[i][4]-8],[-255,0], color='g')
    pylab.plot([oyster_dim[i][5]-3,oyster_dim[i][5]-3],[-255,0], color='g')
    
    pylab.plot([oyster_dim[i][4]-8,oyster_dim[i][5]-3],[-oyster_dim[i][11],-oyster_dim[i][13]], color='r')
    pylab.plot([(oyster_dim[i][6]+oyster_dim[i][7]-11)/2,(oyster_dim[i][8]+oyster_dim[i][9]-11)/2],[-oyster_dim[i][2],-oyster_dim[i][3]], color='r')

    pylab.scatter([oyster_dim[i][6]-8,oyster_dim[i][7]-3,oyster_dim[i][8]-8,oyster_dim[i][9]-3,oyster_dim[i][4]-8,oyster_dim[i][5]-3], [-oyster_dim[i][2],-oyster_dim[i][2],-oyster_dim[i][3],-oyster_dim[i][3],-oyster_dim[i][11],-oyster_dim[i][13]], color='k')
    
    pylab.hold(False)
    #pylab.savefig(image_title+'.png')
    pylab.show()
  return


def plot_oyster_images_AiO():
  # only plot the first few oysters
  if (num_oysters>17):
    return

  f, axarr = pylab.subplots(2, 2)
  
  for i in range(n_images):
    axarr[i/2,i%2].scatter(scatter_x[i], scatter_y[i], color='lightgrey')
    axarr[i/2,i%2].hold(True)
    if (i==1 or i==3):
      pylab.setp( axarr[i/2,i%2].axes.get_yticklabels(), visible=False)
    if (i==0 or i==1):
      pylab.setp( axarr[i/2,i%2].axes.get_xticklabels(), visible=False)
    if (i==0):
      axarr[i/2,i%2].set_title('oyster #'+str(num_oysters))
      
    axarr[i/2,i%2].grid(True)
    axarr[i/2,i%2].set_ylim([-255,0])
    axarr[i/2,i%2].set_xlim([0,111])
    axarr[i/2,i%2].plot([0,111],[-oyster_dim[i][2],-oyster_dim[i][2]], color='b')
    axarr[i/2,i%2].plot([0,111],[-oyster_dim[i][3],-oyster_dim[i][3]], color='b')
    axarr[i/2,i%2].plot([oyster_dim[i][4]-8,oyster_dim[i][4]-8],[-255,0], color='g')
    axarr[i/2,i%2].plot([oyster_dim[i][5]-3,oyster_dim[i][5]-3],[-255,0], color='g')
    
    axarr[i/2,i%2].plot([oyster_dim[i][4]-8,oyster_dim[i][5]-3],[-oyster_dim[i][11],-oyster_dim[i][13]], color='r')
    axarr[i/2,i%2].plot([(oyster_dim[i][6]+oyster_dim[i][7]-11)/2,(oyster_dim[i][8]+oyster_dim[i][9]-11)/2],[-oyster_dim[i][2],-oyster_dim[i][3]], color='r')

    axarr[i/2,i%2].scatter([oyster_dim[i][6]-8,oyster_dim[i][7]-3,oyster_dim[i][8]-8,oyster_dim[i][9]-3,oyster_dim[i][4]-8,oyster_dim[i][5]-3], [-oyster_dim[i][2],-oyster_dim[i][2],-oyster_dim[i][3],-oyster_dim[i][3],-oyster_dim[i][11],-oyster_dim[i][13]], color='k')

    axarr[i/2,i%2].annotate(str(i+1), [5,-250],[5,-250], color = 'r')
    axarr[i/2,i%2].hold(False)
  f.subplots_adjust(hspace=0.01)
  f.subplots_adjust(wspace=0.01)
  #pylab.savefig(image_title+'.png')
  pylab.show()
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
    prepare_scatter_images()
    plot_oyster_images()
    plot_oyster_images_AiO()

  # clean up before exit
  fin.close()
  fout.close()
  print '\ntotal # oysters: ', num_oysters
  return


def contour_filtering():
  global contour_x
  global contour_y
  
  return

#oystek_start('74mm wooden 100x random orientation.log')
oystek_start('sample_4.log')

