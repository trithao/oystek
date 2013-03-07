#ifndef G5_FPGA_H
#define G5_FPGA_H


// Start of FPGA memory in MCU space
// This is set by the chip select used, each of which has a fixed mapping
// Memory comes first within this space, followed by registers
// Read and write registers are unrelated, but each share the same space
#define FPGA_BASE        0x10000000

// Start of registers within the FPGA
#define FPGA_REGISTERS   (FPGA_BASE + 0x00008000)

#define SCANNER_IMAGE_COUNT 5
#define SCANNER_REGISTER_COUNT 4


// There are 7 16-bit words worth of pixels per line, however,
// the line stride is 8 words (i.e. ignore the last word on each line).
#define IMAGE_LINE_STRIDE_WORDS 8
#define IMAGE_LINE_ACTIVE_WORDS 7

// Size of address space of each image memory region (in lines).
#define IMAGE_TOTAL_LINE_COUNT 256
// Size of populated image region (in lines).
#define IMAGE_ACTIVE_LINE_COUNT 255

// Dip, Velocity and Unused registers
//#define FPGA_DIP (FPGA_BASE + 0x000020A0)
//#define FPGA_VEL (FPGA_BASE + 0x000020A2)
//#define FPGA_UNU (FPGA_BASE + 0x000020A2)

#define FPGA_DIP (FPGA_REGISTERS + 0x000000A0)
#define FPGA_VEL (FPGA_REGISTERS + 0x000000A2)
#define FPGA_VER (FPGA_REGISTERS + 0x000000A4)

#define FORCE_SCAN_DEFAULT 0
//#define BREAK_WIDTH_DEFAULT 4
#define BREAK_WIDTH_DEFAULT 100
#define INTER_LINE_DELAY_DEFAULT 0   // in # pixels

#define PIXEL_DELAY 2.4              // micro seconds
#define LINE_STEPS 115
#define LINE_DELAY_DEFAULT 276 
// 276= PIXEL_DELAY * (LINE_STEPS + INTER_LINE_DELAY_DEFAULT)

#define XMIN_CORRECTION 8
#define XMAX_CORRECTION 3

typedef struct
{
  uint16_t view[IMAGE_ACTIVE_LINE_COUNT * IMAGE_LINE_STRIDE_WORDS];
  uint16_t padding[(IMAGE_TOTAL_LINE_COUNT - IMAGE_ACTIVE_LINE_COUNT) * IMAGE_LINE_STRIDE_WORDS];
} FPGA_IMAGE_VIEW;

typedef struct
{
  uint16_t count;
  uint16_t spare1;
  uint16_t y_min;
  uint16_t y_max;
  uint16_t x_min;
  uint16_t x_max;
  uint16_t x_min_of_y_min;
  uint16_t x_max_of_y_min;
  uint16_t x_min_of_y_max;
  uint16_t x_max_of_y_max;
  uint16_t y_min_of_x_min;
  uint16_t y_max_of_x_min;
  uint16_t y_min_of_x_max;
  uint16_t y_max_of_x_max;
  uint16_t spare2;
  uint16_t spare3;
} FPGA_IMAGE_REG;

// *****************************************************************************
// *
// *  Global variables defined by this module
// *
// *****************************************************************************

typedef struct
{
  FPGA_IMAGE_VIEW view[SCANNER_IMAGE_COUNT];        // images as bitmaps
  FPGA_IMAGE_VIEW padding[8-SCANNER_IMAGE_COUNT];   // pad out to the size of 8 images
  FPGA_IMAGE_REG image_reg[SCANNER_REGISTER_COUNT]; // statistic registers, for each image
  uint16_t dip;                   // dip switch, as bits
  uint16_t velocity_us;           // velocity as delay between ccds, in uS
  uint16_t unused;                // next unused register, for testing
} FPGA_READ;

typedef struct
{
  // bit 0 is force_scan, forces a break detection when set
  uint16_t force_scan;
  // width of break in pixels (not necessarily consecutive)
  // to trigger the beam break detector
  uint16_t break_width;
  // extra delay after each line, in pixels, to slow the line scan rate
  uint16_t line_delay;
} FPGA_WRITE;

/* Commands sent from FPGA thread to Grading thread via 
 * a global variable flag.
 * Grading thread reset this flag to acknowledge the command.
 */
typedef enum {
  MOTOR_ACK=0, // acknowlegde
  MOTOR_TURN,
} fpga_grader_cmd_t;

typedef enum {
  GRADING_ACK=0, // acknowlegde
  GRADING_START,
  GRADING_ABORT
} motor_cmd_t;


extern fpga_grader_cmd_t fpga_grader_cmd; // command sent from FPGA to Grading thread
extern motor_cmd_t motor_cmd;

extern volatile uint16_t *fpga_ptr;

//extern int accept_new_oyster;  // TRUE or FALSE

void g5_fpga(void *pvParameters);

/* The ISR can cause a context switch so is declared naked. 
void vFPGA_ISR( void ); // __attribute__ ((naked));
*/
#endif
