
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;

uint8_t fart[1000];

uint16_t dude;

uint16_t foo(uint16_t a, uint16_t b) {
  return (((a+b)/8)+(23*b));
}

uint16_t main() {
  uint16_t index;
  uint8_t *buffer;
  buffer = &fart;
  dude = 611;
  buffer[23+index] = (((dude+67)+foo(12,34))*(index+12)); 
  //fart[24] = dude+35; 
  //index = (((dude+67)+foo(12,34))*(index+12));
  //index = dude+67+index+12;
  return 0;
}
