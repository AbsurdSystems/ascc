

#define IOREG_REGION         0xFFFF0000
#define IOREG_UART_SERIN                  (*(unsigned char *) IOREG_REGION)
#define IOREG_UART_SEROUT                 (*(unsigned char *) IOREG_REGION)
#define IOREG_UART_AVAIL_CFG              (*(unsigned char *) (IOREG_REGION+1))


typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned long uint32_t;


typedef struct
{
   char ser_data;
   char ser_avail;
} ACIA_Interface;

// Hello there!


char buffer[50];


char input_char();
char print_char(char the_char);
void print_string(char *the_str);

/*
void print_string(char *the_str)
{
   register ACIA_Interface *acia;
   register uint32_t str_index;
   acia = IOREG_REGION;
   str_index = 0;
   while(1)
   {
      switch(the_str[str_index])
      {
         case 0:
            return;
         case 10:
         case 13:
            acia->ser_data = 10;
            acia->ser_data = 13;
            str_index++;
            break;
         default:
            acia->ser_data = the_str[str_index];
            str_index++;
            break;
      }
   }       
}

char input_char()
{
   register ACIA_Interface *acia;
   acia = IOREG_REGION;
   while(acia->ser_avail == 0);
   return acia->ser_data;
}
*/

void input_str(char *in_str, uint8_t maxcount)
{
   //register ACIA_Interface *acia;
   char in_char;
   uint8_t currcount;

   //acia = IOREG_REGION;
   currcount = 0;
   while(1)
   {
      in_char = input_char();
      switch(in_char)
      {
         case 13:  
         case 10:  
            in_str[currcount] = 10;
            currcount++;
            in_str[currcount] = 0;
            //print_string("\n");
            print_char(10);
            print_char(13);
            return;
         case 0x7F: 
         case 8:     
            if(currcount>0)
            {
               print_char(0x8);
               print_char(' ');
               print_char(0x8);
               currcount--;
            } 
            break;
         default:
            if(currcount<maxcount)
            {
               in_str[currcount] = in_char;
               currcount++;
               print_char(in_char);
            } 
            break;
      }
   }
}



int main()
{
  print_string("AS32X BIOS v0.1\n");
  print_string("by Michael Burns 2024\n");  

  input_char();
  print_string("Beginning...\n\n");

  while(1)
  {
     print_string(" > ");
     input_str(buffer,30); 
     print_string("\n = ");
     print_string(buffer);
  }
  return(0);
}




