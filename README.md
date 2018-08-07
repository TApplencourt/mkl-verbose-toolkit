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

You can get an application to print this information to a standard output device by enabling Intel MKL Verbose. More information at https://software.intel.com/en-us/articles/verbose-mode-supported-in-intel-mkl-112

We propose 2 script to facilitate the generation and the parsing of MKL Verbose log file:
- To parse the log file and generate summary tables, use `mkl_parse`.
- To restrict the verbosity for one MPI_RANK, use `mkl_hook` wrapper.

# mkl_parse 
Generate a summary for "MKL_verbosed" log files.
For LAPACK, display the cummulative time spend by function, the range of arguments of those function, and the most expensive function calls.

For FTT, display the rank and I/O tensors. Support batched calls.

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


##  Example
```
>> zcat log.out | wc -l
1413113

>> zmore log.out 
...
MKL_VERBOSE DCOPY(64,0x7fadd7d32440,1,0x7fadd7d94268,64) 2.32us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(64,0x7fadd7d32840,1,0x7fadd7d94270,64) 3.33us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(64,0x7fadd7d32c40,1,0x7fadd7d94278,64) 2.85us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DTRSM(R,U,N,N,64,64,0x7fae139802e8,0x7fadd7d94080,64,0x7fadd7d23240,128) 1.59ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DTRSM(R,U,N,N,128,64,0x7f6d0bac42e8,0x7f6ccfd94080,64,0x7f6ccfd23040,128) 1.52ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DTRSM(R,U,N,N,128,64,0x7f8f8ebcd2e8,0x7f8f52d94080,64,0x7f8f52d23040,128) 1.46ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE FFT: MAIN_DESC | dco8192:1:1 | THR_LIMIT = 1 | 0.00s CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:2 WDiv:HOST:+0.000
MKL_VERBOSE FFT: MAIN_DESC | dco8192:1:1 | THR_LIMIT = 1 | 0.00s CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:2 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(128,0x7f3934194080,1,0x7f39341a9080,64) 52.63us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DCOPY(128,0x7f3934194480,1,0x7f39341a9088,64) 1.76us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
...

>> zcat log.out | ./mkl_parse.py
--LAPACK / Accumulation--
Function       N    Time (s)  Time (%)
----------  ----  ----------  ----------
DGEMM        295   4.61994    95%
DTRSM         33   0.15222    3%
ZDSCAL      1025   0.0370106  1%
DAXPY       1024   0.0258006  1%
DDOT           4   0.0140796  0%

--LAPACK / Function arguments--
Function    Arg      Min      Max
----------  -----  -----  -------
DGEMM       m         32     3956
DGEMM       n         32     1024
DGEMM       k          3     3956
DGEMM       lda       64     3956
DGEMM       ldb        3     3956
DGEMM       ldc       32     3956
DTRSM       m         64     3956
DTRSM       n         64      128
DTRSM       lda       64      128
DTRSM       ldb      256     3956
ZDSCAL      n      12032    48384
ZDSCAL      incx       1        1
DAXPY       n       7912     7912
DAXPY       incx       1        1
DAXPY       incy       1        1
DDOT        n      31298  4050944
DDOT        incx       1        1
DDOT        incy       1        1

--LAPACK / Function call by cummulative time--
Function    Args                                                                                Count      Time (s)  Time (%)
----------  ----------------------------------------------------------------------------------  -------  ----------  ----------
DGEMM       [('m', 128), ('n', 1024), ('k', 3886), ('lda', 3886), ('ldb', 3956), ('ldc', 128)]  48          1.49949  31%
DGEMM       [('m', 32), ('n', 1024), ('k', 3886), ('lda', 3886), ('ldb', 3956), ('ldc', 32)]    48          0.61029  13%
DGEMM       [('m', 512), ('n', 1024), ('k', 1024), ('lda', 512), ('ldb', 1024), ('ldc', 3956)]  14          0.51528  11%
DGEMM       [('m', 512), ('n', 1024), ('k', 3956), ('lda', 3956), ('ldb', 3956), ('ldc', 512)]  4           0.47738  10%
DGEMM       [('m', 3886), ('n', 1024), ('k', 128), ('lda', 3886), ('ldb', 128), ('ldc', 3956)]  16          0.38915  8%
Misc                                                                                                        1.36578  28%

--FFT / Summary--
Precision    Domain    Placement    Ranks    I/O tensors                      Count
-----------  --------  -----------  -------  -----------------------------  -------
Double       Complex   OutofPlace   [1, 1]   192:1:1*398:192:192                  1
Double       Complex   InPlace      [2, 1]   192:192:192x192:1:1*3:36864:0        1
Double       Complex   OutofPlace   [1, 1]   192:1:1*100:192:192                  1
```
##  Array Explanations

### 

### FFT 

- An I/O  dimension is  a triple d=(n,i,o),  where n is  a nonnegative integer called the length, i is an integer called the input stride, and o is  an  integer  called  the output  stride. ',' is used as a delimiter between element of the triple.
- The nonnegative integer p=|t| is called the rank of I/O tensor.
- An I/O tensor t = { d1, d2, ..., dp}  is a set of I/O dimensions. Tensor use an "x" as an delimiter between dimension.
- FFT problems can be batched, "\*" is used as a separator between batch. In the 'Ranks' collums, each batch rank are displayed.

# mkl_hook

A little wrapper to source the `MKL_VERBOSE` enviroment by only one MPI_RANK.

# mkl_hook 

A little wrapper to source the `MKL_VERBOSE` enviroment by only one MPI_RANK.


