# Usage
```
usage: mkl_parse.py [-h] [filename]

Generate a summary for "MKL_verbosed" log files

positional arguments:
  filename    If filename not provided, std.in will be used

optional arguments:
  -h, --help  show this help message and exit
```


# Output

```
zcat log.out | ./mkl_parse.py
--Group by function--
Name fct         n    Time (s)  Tot_time (%)
----------  ------  ----------  --------------
DGEMM        45235    88.2884   84%
DLAED4       58902     6.17073  6%
DGEMV       137995     3.21332  3%
DSTEQR          26     1.9052   2%
DGETRF          64     1.39246  1%

--Min Max arguments of function--
Name fct    Name_argv       Min     Max
----------  -----------  ------  ------
DGEMM       m                 1   24576
DGEMM       n                 1   12672
DGEMM       k                 2   24576
DGEMM       lda               4   24785
DGEMM       ldb               1   25145
DGEMM       ldc               1   24963
DLAED4      n               420    6480
DLAED4      i                 6     116
DLAED4      info          58902   58902
DGEMV       m                65   28642
DGEMV       n               227   10255
DGEMV       lda            2712   36113
DGEMV       incx            630  130957
DGEMV       incy         137995  137995
DSTEQR      n                 1       6
DSTEQR      ldz               5       6
DSTEQR      info             26      26
DGETRF      m                64      64
DGETRF      n                64      64
DGETRF      lda              64      64
DGETRF      info             64      64

--Group by arguments--
Name fct    Argv                                                                               Count      Time (s)  Time (%)
----------  ---------------------------------------------------------------------------------  -------  ----------  ----------
DGEMM       [('m', 210), ('n', 210), ('k', 2438), ('lda', 2438), ('ldb', 2438), ('ldc', 210)]  280         4.11834  4%
DGEMM       [('m', 2438), ('n', 140), ('k', 140), ('lda', 2438), ('ldb', 140), ('ldc', 2438)]  560         3.89197  4%
DGEMM       [('m', 140), ('n', 140), ('k', 2438), ('lda', 2438), ('ldb', 2438), ('ldc', 140)]  504         3.80544  4%
DGEMM       [('m', 210), ('n', 210), ('k', 2444), ('lda', 2444), ('ldb', 2444), ('ldc', 210)]  220         3.18579  3%
DGEMM       [('m', 70), ('n', 70), ('k', 2438), ('lda', 2438), ('ldb', 2438), ('ldc', 70)]     840         3.05121  3%
Misc                                                                                                      87.2421   83%

--FFT information--
fft                       count
----------------------  -------
dco135:1:1*218:135:135       58
dco135:1:1*220:135:135       68
dco135:1:1*219:135:135        2
dco135:1:1*266:135:135      114
dco135:1:1*399:135:135       14
dco135:1:1*270:135:135      114
dco135:1:1*405:135:135       14
dco135:1:1*56:135:135        58
dco135:1:1*54:135:135        68
dco135:1:1*53:135:135         2
dco135:1:1*134:135:135      114
dco135:1:1*201:135:135       14
```
