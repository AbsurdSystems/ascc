
typedef struct
{
   int pidm;
   char name[30];
   short age;
} StudentRecord;

/*
char uart_in_buffer[256];
*/

StudentRecord the_record;

StudentRecord the_list[10];

int main()
{
   register StudentRecord *dude;
   unsigned int index;
   dude = &the_list[index];
   dude->age = ((index + 45) * 23);

   dude = &the_record;
   dude->age = index;
   index = dude->age;
   dude->age += 45;

   return 0;
}
