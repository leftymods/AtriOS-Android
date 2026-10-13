#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>

#define WIFI_POWER_UP    _IO('m', 3)
#define WIFI_POWER_DOWN  _IO('m', 4)

int main(int argc, char **argv) {
    int fd = open("/dev/wifi_power", O_RDWR);
    if (fd < 0) {
        perror("[AtriOS] /dev/wifi_power");
        return 1;
    }
    if (argc > 1 && argv[1][0] == '0') {
        printf("[AtriOS] Powering DOWN Wi-Fi SDIO...\n");
        if (ioctl(fd, WIFI_POWER_DOWN) < 0) {
            perror("ioctl WIFI_POWER_DOWN");
            close(fd);
            return 2;
        }
    } else {
        printf("[AtriOS] Powering UP Wi-Fi SDIO...\n");
        if (ioctl(fd, WIFI_POWER_UP) < 0) {
            perror("ioctl WIFI_POWER_UP");
            close(fd);
            return 2;
        }
        printf("[AtriOS] Wi-Fi SDIO powered up successfully.\n");
    }
    close(fd);
    return 0;
}
