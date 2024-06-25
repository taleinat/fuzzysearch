#ifndef _FUZZYSEARCH_C_EXT_BASE_H
#define _FUZZYSEARCH_C_EXT_BASE_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#ifndef unlikely
    #ifdef __GNUC__
      /* Test for GCC > 2.95 */
      #if __GNUC__ > 2 || (__GNUC__ == 2 && (__GNUC_MINOR__ > 95))
        #define likely(x)   __builtin_expect(!!(x), 1)
        #define unlikely(x) __builtin_expect(!!(x), 0)
      #else /* __GNUC__ > 2 ... */
        #define likely(x)   (x)
        #define unlikely(x) (x)
      #endif /* __GNUC__ > 2 ... */
    #else /* __GNUC__ */
      #define likely(x)   (x)
      #define unlikely(x) (x)
    #endif /* __GNUC__ */
#endif

#if defined(_MSC_VER)
#define inline __inline
#endif

inline static int is_simple_buffer(Py_buffer pybuf) {
    return (
        pybuf.itemsize == 1 &&
        pybuf.ndim == 1 &&
        (pybuf.strides == NULL || pybuf.strides[0] == 1) &&
        pybuf.suboffsets == NULL
    );
}

#endif
