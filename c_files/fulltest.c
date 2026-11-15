
typedef struct
{
   int pidm;
   char name[30];
   int age;
} StudentRecord;

int fart=45;

char uart_in_buffer[256];
StudentRecord the_list[10];
short buffergrid[] = {3,4,52,1,3,2};

char *message= "Hello there";

int *dude;

void cheese()
{
   int food;
   const int poop;
   register int peebles;
   char c;

   peebles = 12;
   food = peebles + 2;

   peebles= food++ - poop;
}

int main()
{
   int geez;

   /* the_list.age=34+geez; */


   dude=geez= sizeof(StudentRecord);
   if((geez>1) && (geez==5))
   {
      dude=&the_list[1].age;
   }
   else
   {
      buffergrid[3]=34;
   }

   return 0;
}
