#include <stdio.h>
#include <SDL3/SDL.h>

int main(int argc, char *argv[]) {
    if (SDL_Init(0) != 0) {
        // fprintf(stderr, "Error initializing SDL: %s\n", SDL_GetError());
        // return 1;
    }

    // Get the starting time
    Uint64 start_time = SDL_GetTicks();

    // Simulate some work with SDL_Delay
    SDL_Delay(2000);  // Delay for 2000 milliseconds (2 seconds)

    // Get the ending time
    Uint64 end_time = SDL_GetTicks();

    printf("Elapsed time: %llu ms\n", (unsigned long long)(end_time - start_time));

    SDL_Quit();
    return 0;
}