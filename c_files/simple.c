

#define IOREG_REGION         0xFF000000
#define IOREG_UART_SERIN                  (*(unsigned char *) IOREG_REGION)
#define IOREG_UART_SEROUT                 (*(unsigned char *) IOREG_REGION)
#define IOREG_UART_AVAIL_CFG              (*(unsigned char *) (IOREG_REGION+1))

typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;

uint8_t fart[100];

uint16_t fred = 45;
uint16_t dude = 45;
uint32_t my_list[10] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
char *my_string = "Hello there!\n";


void syscall(uint8_t sysnum);

uint32_t unsigned_multiply(uint32_t a, uint32_t b) 
{
	register uint32_t product = 0;
	register uint32_t multiplier = b + 1;
	//uint8_t i;

	//multiplier = b;
    
	for (register uint8_t i = 0; i < 32; i++) 
	{
		// Check if the current bit of the multiplier is 1
		if ((multiplier & 1) == 1) 
		{
			product += (a << i);
		}
        multiplier >>= 1; // Shift to evaluate the next bit
    }    
    return product;
}

/*
uint32_t __unsigned_divide__(uint32_t a, uint32_t b) 
{
  return 1;
}
*/

uint16_t foo(uint32_t a, uint32_t b) {
  return (((a+b)/10)+(b*2));
}

uint16_t main() {
  register uint16_t index;
  uint32_t temp;
  register uint16_t *ptr1;
  uint16_t local_array[30];

  //index += (temp-30);
  //IOREG_UART_SEROUT = 'G';
  //temp = ptr1[index+30]+temp;

  syscall(4);

  ptr1 = &local_array;
  while(index == 10)
  {
     temp = ptr1[index+12]; 
  }
  //local_array[index] = temp*32;
  //temp += (local_array[index] + 45);

  return 0;
}
