
typedef unsigned int uint16_t;

#include "g5_fpga.h"
#include "math.h"
#include <stdio.h>

#define G 9.80665
#define h1 0.0154
#define line_duration 0.000276
#define delta 0

#define MIN(a,b) ((a)<(b)?(a):(b))
#define MAX(a,b) ((a)<(b)?(b):(a)) 
#define TRUE 1
#define FALSE !TRUE

uint16_t measure_oyster_length_1(FPGA_READ *fpga_data);
uint16_t measure_oyster_length_2(FPGA_READ *fpga_data);

uint16_t velocity_ave;

void main(void) 
{
  FPGA_READ fpga;

//  while (1) 
  {
    get_input(&fpga);
    printf("\noyster length: %d, %d\n", measure_oyster_length_1(&fpga), measure_oyster_length_2(&fpga));
  }
}

int get_input(FPGA_READ *fdata){
  int i;
  for (i=0;i<1;i++)
  {
    printf("IMAGE %d:\n",i+1);
    printf("R[0]:-count:"); scanf("%d", &(fdata->image_reg[i].count));
//    printf("count is: %d\n", fdata->image_reg[i].count); 

    printf("R[2]-y_min:"); scanf("%d", &(fdata->image_reg[i].y_min));
//    printf("y_min is: %d\n", fdata->image_reg[i].y_min); 

    printf("R[3]-y_max:"); scanf("%d", &(fdata->image_reg[i].y_max));
//    printf("y_max is: %d\n", fdata->image_reg[i].y_max);
    
    printf("R[4]-x_min:"); scanf("%d", &(fdata->image_reg[i].x_min));
//    printf("x_min is: %d\n", fdata->image_reg[i].x_min); 

    printf("R[5]-x_max:"); scanf("%d", &(fdata->image_reg[i].x_max));
//    printf("x_max is: %d\n", fdata->image_reg[i].x_max);

    printf("R[6]-x_min_of_y_min:"); scanf("%d", &(fdata->image_reg[i].x_min_of_y_min));
//    printf("x_min_of_y_min is: %d\n", fdata->image_reg[i].x_min_of_y_min); 
    
    printf("R[7]-x_max_of_y_min:"); scanf("%d", &(fdata->image_reg[i].x_max_of_y_min));
//    printf("x_max_of_y_min is: %d\n", fdata->image_reg[i].x_max_of_y_min); 

    printf("R[8]-x_min_of_y_max:"); scanf("%d", &(fdata->image_reg[i].x_min_of_y_max));
//    printf("x_min_of_y_max is: %d\n", fdata->image_reg[i].x_min_of_y_max); 
    
    printf("R[9]-x_max_of_y_max:"); scanf("%d", &(fdata->image_reg[i].x_max_of_y_max));
//    printf("x_max_of_y_max is: %d\n", fdata->image_reg[i].x_max_of_y_max); 

    printf("R[11]-y_max_of_x_min:"); scanf("%d", &(fdata->image_reg[i].y_max_of_x_min));
//    printf("y_max_of_x_min is: %d\n", fdata->image_reg[i].y_max_of_x_min); 
    
    printf("R[13]-y_max_of_x_max:"); scanf("%d", &(fdata->image_reg[i].y_max_of_x_max));
//    printf("y_max_of_x_max is: %d\n", fdata->image_reg[i].y_max_of_x_max); 
        
/*
 0 uint16_t count;
 1 uint16_t spare1;
 2 uint16_t y_min;
 3 uint16_t y_max;
 4 uint16_t x_min;
 5 uint16_t x_max;
 6 uint16_t x_min_of_y_min;
 7 uint16_t x_max_of_y_min;
 8 uint16_t x_min_of_y_max;
 9 uint16_t x_max_of_y_max;
10 uint16_t y_min_of_x_min;
11 uint16_t y_max_of_x_min;
12 uint16_t y_min_of_x_max;
13 uint16_t y_max_of_x_max;
*/    
  }
  printf("velocity/delay:"); scanf("%d", &velocity_ave);

  return TRUE;
}

// return oyster's shell length in mm
uint16_t measure_oyster_length_1(FPGA_READ *fpga_data)
{
  FPGA_IMAGE_REG *reg;
  float horizontal, vertical, vertical2, diagonalH, diagonalV, leanx, leany, length=0.0; 
  int i;
  float t1, t21, t32, t22p, t32p;
  for (i=0; i<1; i++) {
  // free falling object: h(t) = 0.5 * g * t^2

    reg = (FPGA_IMAGE_REG *)&(fpga_data->image_reg[i]);

    t21 = velocity_ave * 0.000001; // t2 - t1, in seconds
    t32 = (1+ reg->y_max - reg->y_min)* line_duration; // t3 - t2, in seconds, offset 1 line
    t1 = h1/(G*t21) - t21 / 2;  // in seconds

    // vertical lean
    vertical = G/2*t32*(t32 + 2*t21 + 2*t1)*1000; // in mm    
//    vertical2 = vertical*(1+reg->y_min+delta)/(1.0 + reg->y_max - reg->y_min);
    printf("\nvert1= %f, %f\n", vertical, vertical);
    leanx = abs((reg->x_max_of_y_max + reg->x_min_of_y_max)-(reg->x_max_of_y_min + reg->x_min_of_y_min))/2; // offset 0 pixel
    diagonalV = sqrtf(vertical * vertical + leanx * leanx);
    
    // horizontal lean
    horizontal= 1+ (reg->x_max - XMAX_CORRECTION) - (reg->x_min - XMIN_CORRECTION) ; // offset 1 pixel
    leany = vertical*(abs(reg->y_max_of_x_max - reg->y_max_of_x_min))/(1+ abs(reg->y_max - reg->y_min));
    diagonalH = sqrtf(horizontal * horizontal + leany * leany);

    printf("diagonals_1= %f, %f\n", diagonalV, diagonalH);
    length = MAX(length, MAX(diagonalV, diagonalH));

//    printf("\nt21=%f\nt32=%f\nt1=%f\nvertical=%.1f\nleanx=%.1f\nhorizontal=%.1f\nleany=%.1f\ndiagonalV=%.1f\ndiagonalH=%.1f\nOYSTER_LENGTH=%.1f\n",
//      t21,t32,t1,vertical,leanx,horizontal,leany,diagonalV,diagonalH,length);
  }
#ifdef G5_DEBUG_1
  serial_putc(serDEBUG, 'L', 100);
#endif
  return (uint16_t)length;
}


uint16_t measure_oyster_length_2(FPGA_READ *fpga_data)
{
  FPGA_IMAGE_REG *reg;
  float horizontal, vertical, vertical2, diagonalH, diagonalV, leanx, leany, length=0.0; 
  float t1, t21, v0, v1, v2;
  int i;
  for (i=0; i<1; i++) {
    reg = (FPGA_IMAGE_REG *)&(fpga_data->image_reg[i]);
    
    // velocity_ave is in micro-seconds
    t1 = velocity_ave * 0.000001; //seconds, time delay between 2 CCDs
    
    v0 = h1 / t1 - G * t1 / 2.0; // velocity at CCD0
    v1 = v0 + G * t1;          // velocity at CCD1
    
    // oyster length in terms of time, in seconds
    // This is the time taken for the oyster goes pass CCD1. i.e.
    // time taken to scan the entire oyster.
    t21 = (1.0 + reg->y_max - reg->y_min)* line_duration; 
    
    v2 = v1 + G * t21;         // velocity when clear off CCD1
    
    // vertical lean
    vertical  = 1000.0*(v2 + v1)*t21/2.0; // h21, in mm
//    vertical2 = h1*1000*(1.0 + reg->y_max - reg->y_min)/(1+reg->y_min + delta);
    printf("\nvert2= %f, %f\n", vertical, vertical);
    leanx = abs((reg->x_max_of_y_max + reg->x_min_of_y_max)-(reg->x_max_of_y_min + reg->x_min_of_y_min))/2; // offset 0 pixel
    diagonalV = sqrtf(vertical * vertical + leanx * leanx);
    
    // horizontal lean
    horizontal= 1+ (reg->x_max - XMAX_CORRECTION) - (reg->x_min - XMIN_CORRECTION) ; // offset 1 pixel
    leany = vertical*(abs(reg->y_max_of_x_max - reg->y_max_of_x_min))/(1 + reg->y_max - reg->y_min);    
    diagonalH = sqrtf(horizontal * horizontal + leany * leany);

    printf("diagonals_2= %f, %f\n", diagonalV, diagonalH);
    length = MAX(length, MAX(diagonalV, diagonalH));

//    printf("\nt1=%f\nt21=%f\nv0=%f\nv1=%f\nv2=%f\nvertical=%.1f\nleanx=%.1f\nhorizontal=%.1f\nleany=%.1f\ndiagonalV=%.1f\ndiagonalH=%.1f\nOYSTER_LENGTH=%.1f\n",
//      t1,t21,v0,v1,v2,vertical,leanx,horizontal,leany,diagonalV,diagonalH,length);
  }
  return (uint16_t)length;
}
