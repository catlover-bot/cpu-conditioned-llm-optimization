#define _POSIX_C_SOURCE 200809L

#include "kernel.h"

#include <errno.h>
#include <float.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_N 1024

_Static_assert(sizeof(double) == sizeof(uint64_t), "binary64 double required");
_Static_assert(FLT_RADIX == 2 && DBL_MANT_DIG == 53 && DBL_MAX_EXP == 1024,
               "IEEE-754 binary64 double required");

static volatile uint64_t output_sink;

/* The unsigned 32-bit LCG wraps modulo 2^32; zero is a valid seed.
 * Taking the upper 17 bits and dividing by 2^16 gives exactly representable
 * finite dyadics in [-1, 1 - 2^-16], with spacing 2^-16. a and b draws are
 * interleaved: a[0], b[0], a[1], b[1], ... . No external input data is used.
 */
static double next_input(uint32_t *state)
{
    *state = *state * UINT32_C(1664525) + UINT32_C(1013904223);
    return (double)(*state >> 15) / 65536.0 - 1.0;
}

static int parse_decimal(const char *text, uint64_t maximum, uint64_t *value)
{
    if (*text == '\0') {
        return 0;
    }
    for (const char *p = text; *p != '\0'; ++p) {
        if (*p < '0' || *p > '9') {
            return 0;
        }
    }
    errno = 0;
    char *end;
    const uintmax_t parsed = strtoumax(text, &end, 10);
    if (errno == ERANGE || *end != '\0' || parsed > maximum) {
        return 0;
    }
    *value = (uint64_t)parsed;
    return 1;
}

static uint64_t bits_of(double value)
{
    uint64_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

/* Consume every output after the timer. This hash is an anti-elimination
 * mechanism only: correctness uses the entire verify output, never this hash.
 * The kernel is compiled in its own translation unit, without LTO.
 */
static uint64_t consume_output(const double *c, size_t count)
{
    uint64_t checksum = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < count; ++i) {
        checksum ^= bits_of(c[i]);
        checksum *= UINT64_C(1099511628211);
    }
    output_sink = checksum;
    return checksum;
}

int main(int argc, char **argv)
{
    uint64_t parsed_n, parsed_seed;
    if (argc != 4 ||
        (strcmp(argv[1], "verify") != 0 && strcmp(argv[1], "measure") != 0) ||
        !parse_decimal(argv[2], MAX_N, &parsed_n) || parsed_n == 0 ||
        !parse_decimal(argv[3], UINT32_MAX, &parsed_seed)) {
        fprintf(stderr, "usage: %s {verify|measure} N SEED; "
                        "N=1..1024, SEED=0..4294967295, decimal digits only\n",
                argv[0]);
        return 2;
    }
    const size_t n = (size_t)parsed_n;
    const size_t count = n * n;
    if (count > SIZE_MAX / sizeof(double)) {
        fprintf(stderr, "matrix allocation size overflow\n");
        return 3;
    }
    double *a = malloc(count * sizeof(*a));
    double *b = malloc(count * sizeof(*b));
    double *c = malloc(count * sizeof(*c));
    if (a == NULL || b == NULL || c == NULL) {
        fprintf(stderr, "matrix allocation failed\n");
        free(a);
        free(b);
        free(c);
        return 3;
    }
    uint32_t state = (uint32_t)parsed_seed;
    for (size_t i = 0; i < count; ++i) {
        a[i] = next_input(&state);
        b[i] = next_input(&state);
        c[i] = 0.0;
    }

    int status = 0;
    if (strcmp(argv[1], "verify") == 0) {
        kernel(n, a, b, c);
        printf("CPUCOND_F64 %zu\n", count);
        for (size_t i = 0; i < count; ++i) {
            printf("%016" PRIx64 "\n", bits_of(c[i]));
        }
    } else {
        struct timespec start, end;
        if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
            perror("clock_gettime start");
            status = 4;
            goto cleanup;
        }
        kernel(n, a, b, c);
        if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
            perror("clock_gettime end");
            status = 4;
            goto cleanup;
        }
        const int64_t seconds = (int64_t)end.tv_sec - (int64_t)start.tv_sec;
        const int64_t nanoseconds = (int64_t)end.tv_nsec - (int64_t)start.tv_nsec;
        if (seconds < 0 ||
            seconds > (INT64_MAX - INT64_C(999999999)) / INT64_C(1000000000)) {
            fprintf(stderr, "invalid clock interval\n");
            status = 4;
            goto cleanup;
        }
        const int64_t elapsed_ns = seconds * INT64_C(1000000000) + nanoseconds;
        const uint64_t checksum = consume_output(c, count);
        if (elapsed_ns <= 0) {
            fprintf(stderr, "clock interval is not positive\n");
            status = 4;
            goto cleanup;
        }
        printf("{\"elapsed_ns\":%" PRId64 ",\"checksum_bits\":\"%016" PRIx64 "\"}\n",
               elapsed_ns, checksum);
    }
    if (fflush(stdout) == EOF || ferror(stdout)) {
        fprintf(stderr, "output write failed\n");
        status = 5;
    }

cleanup:
    free(a);
    free(b);
    free(c);
    return status;
}
