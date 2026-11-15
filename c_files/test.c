
#define IOREG_UART_SERIN                  (*(unsigned char *) 0x800000F0)
#define IOREG_UART_SEROUT                 (*(unsigned char *) 0x800000F0)
#define IOREG_UART_AVAIL_CFG              (*(unsigned char *) 0x800000F1)

typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned long uint32_t;


typedef struct
{
   char ser_data;
   char ser_avail;
} ACIA_Interface;


uint16_t dude = 0;

uint16_t fart[1000];

char *my_string;

char message[30];


uint16_t foo(uint16_t a, uint16_t b) {
  return (a+b);
}

void print_string(char *the_str)
{
   register ACIA_Interface *acia;
   register char *str_index;
   acia = 0xFF000000;
   str_index = the_str;
   while(*str_index != 0)
   {
      if(*str_index == 10 || *str_index == 13)
      {
         acia->ser_data = 10;
         acia->ser_data = 13;
      }
      else
      {
         acia->ser_data = *str_index;
      }
      str_index++;
   }
}


uint16_t main() {
  uint16_t index;
  uint8_t p4, t1;
  uint8_t *my_buffer;
  register uint16_t michael;



  print_string("Hello there\n");
  print_string("My name is Michael Burns\n");
  while(1) {}
 
  /*

  print_string(message);

  index = 1000;
  t1 = 0;
  p4 = 23;

  michael = my_buffer[foo(45,p4)];

  uint8_t localarray[10];

  my_string[t1+c] = *my_buffer;

  while(index < 13)
  {
    michael = (index + 324) + dude;
    index++;
  }


  index++;
  michael = index + 34;
  michael = index + (my_string[t1] + 34);

  IOREG_UART_SEROUT = c;
  if(michael > 45)
  {
     michael = 0xFF00;
     michael = index + fart[dude];
     michael += 3;
  }

  michael = index + my_buffer[dude];
  index = (1223 + michael) + dude;
  michael = index + 4561;
  c = *my_buffer;
  michael = index + fart[dude];
  my_buffer[dude] = fart[index] + 12;
  my_buffer = &my_string;
  michael = index + fart[dude];
  index = fart;
  index[12] = 45;
  fart[12] = 45;

  if(index == 1000)
  {
    fart[index-1] += dude - (index+56);
     fart[index] += (index+56);
     index+=26;
  }

  for(uint16_t fred = 0; fred < 100; fred++)
  {
     if(dude > 300)
     {
        break;
     }
     else
     {
        dude = 23 * fart[fred];
     }
  }

  fart[index] = 0xEA;
  index = &dude;
   *index = dude + 12;
  dude = *index * 56; */
  return 0;
}
