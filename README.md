```
___  ___ _   __ _       _   _ _________________  _____ _____ _____   _____ _____  _____ _      _   _______ _____ 
|  \/  || | / /| |     | | | |  ___| ___ \ ___ \|  _  /  ___|  ___| |_   _|  _  ||  _  | |    | | / /_   _|_   _|
| .  . || |/ / | |     | | | | |__ | |_/ / |_/ /| | | \ `--.| |__     | | | | | || | | | |    | |/ /  | |   | |  
| |\/| ||    \ | |     | | | |  __||    /| ___ \| | | |`--. \  __|    | | | | | || | | | |    |    \  | |   | |  
| |  | || |\  \| |____ \ \_/ / |___| |\ \| |_/ /\ \_/ /\__/ / |___    | | \ \_/ /\ \_/ / |____| |\  \_| |_  | |  
\_|  |_/\_| \_/\_____/  \___/\____/\_| \_\____/  \___/\____/\____/    \_/  \___/  \___/\_____/\_| \_/\___/  \_/  
                                                                                                                 
```

When building applications that call Intel MKL functions, it may be useful to determine:
 - which computational functions are called,
 - what parameters are passed to them, and
  - how much time is spent to execute the functions.

You can get an application to print this information to a standard output device by enabling Intel MKL Verbose. 

- To restrict the verbosity for one MPI_RANK, use `mkl_hook` wrapper.
- To parse the log file and generate summary table, use `mkl_parse`.

# mkl_parse 
Generate a summary for "MKL_verbosed" log files.

## Requirement:
- python3
- tabulate package

## Usage
```
usage: mkl_parse.py [-h] [filename]

Generate a summary for "MKL_verbosed" log files

positional arguments:
  filename    If filename not provided, std.in will be used

optional arguments:
  -h, --help  show this help message and exit
```


##  Output
```
>> zcat log.out | wc -l
1413113

>> zmore log.out 
MKL_VERBOSE DCOPY(64,0x7fadd7d32440,1,0x7fadd7d94268,64) 2.32us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(64,0x7fadd7d32840,1,0x7fadd7d94270,64) 3.33us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(64,0x7fadd7d32c40,1,0x7fadd7d94278,64) 2.85us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DTRSM(R,U,N,N,64,64,0x7fae139802e8,0x7fadd7d94080,64,0x7fadd7d23240,128) 1.59ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DTRSM(R,U,N,N,128,64,0x7f6d0bac42e8,0x7f6ccfd94080,64,0x7f6ccfd23040,128) 1.52ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DTRSM(R,U,N,N,128,64,0x7f8f8ebcd2e8,0x7f8f52d94080,64,0x7f8f52d23040,128) 1.46ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(128,0x7f3934194080,1,0x7f39341a9080,64) 52.63us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(128,0x7f3934194480,1,0x7f39341a9088,64) 1.76us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000

>> zcat log.out | ./mkl_parse.py
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

# mkl_hook 

A little wrapper to source the `MKL_VERBOSE` enviroment by only one MPI_RANK.


