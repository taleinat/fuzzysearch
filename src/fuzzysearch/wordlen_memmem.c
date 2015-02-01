#include <limits.h>
#include <string.h>
#include "src/fuzzysearch/wordlen_memmem.h"

/* Endian detection, taken from: http://esr.ibiblio.org/?p=5095 */
/*
   __BIG_ENDIAN__ and __LITTLE_ENDIAN__ are define in some gcc versions
  only, probably depending on the architecture. Try to use endian.h if
  the gcc way fails - endian.h also doesn not seem to be available on all
  platforms.
*/

#if defined(__APPLE__)
    /* See: https://gist.github.com/yinyin/2027912
       Or search for: OSSwapHostToBigInt64 */
    #include <libkern/OSByteOrder.h>
    #define htobe64(x) OSSwapHostToBigInt64(x)
    #define htonl(x) OSSwapHostToBigInt32(x)
#elif defined(BSD)
    #if defined(__OpenBSD__)
        #include <sys/types.h>
    #else
        #include <sys/endian.h>
    #endif
#else
    #include <endian.h>
#endif

#if defined(__BIG_ENDIAN__)
    #define WORDS_BIGENDIAN 1
#elif defined(__LITTLE_ENDIAN__)
    #undef WORDS_BIGENDIAN
#elif defined(_WIN32)
    #undef WORDS_BIGENDIAN
#elif defined(__BYTE_ORDER) && defined(__BIG_ENDIAN) && defined(__LITTLE_ENDIAN)
    #if __BYTE_ORDER == __BIG_ENDIAN
        #define WORDS_BIGENDIAN 1
    #elif __BYTE_ORDER == __LITTLE_ENDIAN
        #undef WORDS_BIGENDIAN
    #else
        #define UNKNOWN_ENDIANNESS 1
    #endif /* __BYTE_ORDER */
#else
    #define UNKNOWN_ENDIANNESS 1
#endif

#if LONG_MAX == 2147483647
    #define LONG_INT_IS_4_BYTES 1
    #define LONG_INT_N_BYTES 4
#elif LONG_MAX == 9223372036854775807
    #define LONG_INT_IS_8_BYTES 1
    #define LONG_INT_N_BYTES 8
#else
    #define LONG_INT_IS_UNSUPPORTED_SIZE
    #define LONG_INT_N_BYTES sizeof(long)
#endif

/* define MAKE_BIGENDIAN */
#if !defined(UNKNOWN_ENDIANNESS) && defined(WORDS_BIGENDIAN)
    #define MAKE_ULONG_BIGENDIAN(x) (x)
#else
    #if defined(LONG_INT_IS_8_BYTES)
        #define MAKE_ULONG_BIGENDIAN(x) htobe64((x))
    #elif defined(LONG_INT_IS_4_BYTES)
        #define MAKE_ULONG_BIGENDIAN(x) htonl((x))
    #else
        #undef MAKE_ULONG_BIGENDIAN
    #endif
#endif /* !defined(UNKNOWN_ENDIANNESS) && defined(WORDS_BIGENDIAN) */


void *wordlen_memmem(const void *haystack, size_t haystacklen,
                     const void *needle, size_t needlelen)
{
    const void* needle_ptr;
    const void* haystack_ptr;
    int sums_diff;
    int compare_len;
    unsigned long last_needle_chars = 0;
    unsigned long last_haystack_chars = 0;

    switch (needlelen) {
        case (0):
            /* empty needle */
            return (void *) haystack;
            break;
        case (1):
            /* special case for single-character needles */
            return memchr(haystack, *((unsigned char*) needle), haystacklen);
            break;
    }

    /* start searching through haystack only from the first occurence of the
       first character of needle */
    haystack_ptr = memchr(haystack, *((unsigned char*) needle), haystacklen);
    if (!haystack_ptr) {
        /* the first character of needle isn't in haystack */
        return NULL;
    }
    haystacklen -= (haystack_ptr - haystack);
    if (haystacklen < needlelen) {
        /* the remaining haystack is smaller than needle */
        return NULL;
    }
    haystack = haystack_ptr;


    if (needlelen > LONG_INT_N_BYTES + 1)
    {
        needle_ptr = needle;
        sums_diff = 0;
#ifndef MAKE_ULONG_BIGENDIAN
        needle += needlelen - LONG_INT_N_BYTES;
        while (needle_ptr != needle) {
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }

        needle += LONG_INT_N_BYTES;
        while (needle_ptr != needle) {
            last_needle_chars <<= 8;
            last_needle_chars ^= *(unsigned char *)needle_ptr;
            last_haystack_chars <<= 8;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr;
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }
#else
        needle += needlelen;
        while (needle_ptr != needle) {
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }

        last_needle_chars = MAKE_ULONG_BIGENDIAN(*(((unsigned long *)needle_ptr) - 1));
        last_haystack_chars = MAKE_ULONG_BIGENDIAN(*(((unsigned long *)haystack_ptr) - 1));
#endif /* MAKE_ULONG_BIGENDIAN */
        needle -= needlelen;

        /* we will call memcmp() only once we know that the sums are equal and
           that LONG_INT_N_BYTES last chars are equal, so it will be enough to
           compare all but the last LONG_INT_N_BYTES + 1 characters */
        compare_len = needlelen - (LONG_INT_N_BYTES + 1);

        /* At this point:
           * needle is at least two characters long
           * haystack is at least needlelen characters long (also at least two)
           * the first characters of needle and haystack are identical
        */
        if (   sums_diff == 0
            && last_haystack_chars == last_needle_chars
            && memcmp(haystack, needle, compare_len) == 0)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the sums' difference
           and checking for identity whenever the difference is zero */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            last_haystack_chars <<= 8;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr;
            sums_diff -= *((unsigned char *) haystack++);
            sums_diff += *((unsigned char *) haystack_ptr++);

            /* if sums_diff == 0, we know that the sums are equal, so it is enough
               to compare all but the last characters */
            if (   sums_diff == 0
                && last_haystack_chars == last_needle_chars
                && memcmp(haystack, needle, compare_len) == 0)
            {
                return (void *) haystack;
            }
        }
    }
    else if (needlelen < LONG_INT_N_BYTES)
    {
        needle_ptr = needle;
        needle += needlelen;
        sums_diff = 0;
        while (needle_ptr != needle) {
            sums_diff -= *((unsigned char *) needle_ptr++);
            sums_diff += *((unsigned char *) haystack_ptr++);
        }
        needle -= needlelen;

        /* we will call memcmp() only once we know that the sums are equal, so
           it will be enough to compare all but the last characters */
        compare_len = needlelen - 1;

        /* At this point:
           * needle is at least two characters long
           * haystack is at least needlelen characters long (also at least two)
           * the first characters of needle and haystack are identical
        */
        if (   sums_diff == 0
            && memcmp(haystack, needle, compare_len) == 0)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the sums' difference
           and checking for identity whenever the difference is zero */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            sums_diff -= *((unsigned char *) haystack++);
            sums_diff += *((unsigned char *) haystack_ptr++);

            /* if sums_diff == 0, we know that the sums are equal, so it is enough
               to compare all but the last characters */
            if (   sums_diff == 0
                && memcmp(haystack, needle, compare_len) == 0)
            {
                return (void *) haystack;
            }
        }
    }
    else if (needlelen == LONG_INT_N_BYTES)
    {
#ifndef MAKE_ULONG_BIGENDIAN
        needle_ptr = needle;
        needle += needlelen;
        while (needle_ptr != needle) {
            last_needle_chars <<= 8;
            last_needle_chars ^= *(unsigned char *)needle_ptr++;
            last_haystack_chars <<= 8;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;
        }
        needle -= needlelen;
#else
        last_needle_chars = MAKE_ULONG_BIGENDIAN(*(unsigned long *)needle);
        last_haystack_chars = MAKE_ULONG_BIGENDIAN(*(unsigned long *)haystack);
        haystack_ptr += LONG_INT_N_BYTES;
#endif /* MAKE_ULONG_BIGENDIAN */

        if (last_haystack_chars == last_needle_chars)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the last char
           data and checking for equality */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            last_haystack_chars <<= 8;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;
            if (last_haystack_chars == last_needle_chars)
            {
                return (void *) (haystack_ptr - needlelen);
            }
        }
    }
    else /* needlelen == LONG_INT_N_BYTES + 1 */
    {
        needle_ptr = needle + 1;
        ++haystack_ptr; /* equivalent to: haystack_ptr = haystack + 1 */
#ifndef MAKE_ULONG_BIGENDIAN
        needle += needlelen;
        while (needle_ptr != needle) {
            last_needle_chars <<= 8;
            last_needle_chars ^= *(unsigned char *)needle_ptr++;
            last_haystack_chars <<= 8;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;
        }
        needle -= needlelen;
#else
        last_needle_chars = MAKE_ULONG_BIGENDIAN(*(unsigned long *)needle_ptr);
        last_haystack_chars = MAKE_ULONG_BIGENDIAN(*(unsigned long *)haystack_ptr);
        haystack_ptr += LONG_INT_N_BYTES;
#endif /* MAKE_ULONG_BIGENDIAN */
        if (   last_haystack_chars == last_needle_chars
            && *(unsigned char *)haystack == *(unsigned char *)needle)
        {
            return (void *) haystack;
        }

        /* iterate through the remainder of haystack, updating the last char
           data and checking for equality */
        needle_ptr = haystack + haystacklen;
        while (haystack_ptr != needle_ptr)
        {
            last_haystack_chars <<= 8;
            last_haystack_chars ^= *(unsigned char *)haystack_ptr++;

            ++haystack;
            if (   last_haystack_chars == last_needle_chars
                && *(unsigned char *)haystack == *(unsigned char *)needle)
            {
                return (void *) haystack;
            }
        }
    }

    return NULL;
}

#undef UNKNOWN_ENDIANNESS
#undef WORDS_BIGENDIAN
#undef MAKE_ULONG_BIGENDIAN
#undef LONG_INT_IS_4_BYTES
#undef LONG_INT_IS_8_BYTES
#undef LONG_INT_IS_UNSUPPORTED_SIZE
#undef LONG_INT_N_BYTES
