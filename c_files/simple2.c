
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;

uint32_t fart[100];

uint16_t dude;

uint16_t foo(uint16_t a, uint16_t b) {
  return (((a+b)/8)+(23*b));
}

uint16_t main() {
  uint16_t index;
  uint32_t *buffer;

  index = 23;
  buffer = &fart;
  buffer[index] = 45;
  return 0;
}
