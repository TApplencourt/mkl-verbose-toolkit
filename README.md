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

## Requirement / Installation:
- python3
- tabulate package

```
pip install -r requirements.txt
conda install --file requirements.txt
```
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
>> cat log.out | wc -l
141013

>> more log.out 
MKL_VERBOSE Intel(R) MKL 2019.0 Update 2 Product build 20190118 for Intel(R) 64 architecture Intel(R) Advanced Vector Extensions 2 (Intel(R) AVX2) enabled processors, Lnx 2.40GHz intel_thread
MKL_VERBOSE FFT(dcfi30x30x30,tLim:4,desc:0x1c9c140) 452.82us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcbi30x30x30,tLim:4,desc:0x1cb66c0) 118.36us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcfi30x30x30,tLim:4,desc:0x1cc0240) 165.08us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcbi30x30x30,tLim:4,desc:0x1cc9680) 84.77us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcfi30x30x30,tLim:4,desc:0x1cc0240) 102.58us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcbi30x30x30,tLim:4,desc:0x1cc9680) 83.00us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcfi30x30x30,tLim:4,desc:0x1cc0240) 102.86us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcbi30x30x30,tLim:4,desc:0x1cc9680) 81.79us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcfi30x30x30,tLim:4,desc:0x1cc0240) 99.21us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcbi30x30x30,tLim:4,desc:0x1cc9680) 83.10us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4
MKL_VERBOSE FFT(dcfi30x30x30,tLim:4,desc:0x1cc0240) 99.13us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:4

MKL_VERBOSE DGESVD(S,S,45,45,0x3decc70,45,0x3d4eb30,0x3df0bc0,45,0x3ef4cf0,45,0x3ef8c40,2250,0) 1.39ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
MKL_VERBOSE DGETRF(3072,3072,0x7fddf19e9010,3072,0x333da80,0) 376.01ms CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:1 WDiv:HOST:+0.000
...

>> cat log.out | ./mkl_parse.py
~= BLAS / LAPCK ~=

Top 10 function by execution time
Name    Argv                                                                     Time (s)
------  ---------------------------------------------------------------------  ----------
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.52748
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.52185
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.50612
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.5057
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.50566
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.50537
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.50495
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]     0.50494
DGETRF  [('m', '3072'), ('n', '3072'), ('lda', '3072'), ('info', '0')]            0.38882
DGETRF  [('m', '3072'), ('n', '3072'), ('lda', '3072'), ('info', '0')]            0.3767

Top 10 function by execution time (accumulated by arguments)
Name    Argv                                                                                                                              Count (#)    Time (s)
------  ------------------------------------------------------------------------------------------------------------------------------  -----------  ----------
DGETRI  [('n', '3072'), ('lda', '3072'), ('lwork', '1179648'), ('info', '0')]                                                                     8     4.08207
DGETRF  [('m', '3072'), ('n', '3072'), ('lda', '3072'), ('info', '0')]                                                                            8     3.01759
SGEMM   [('transa', 'T'), ('transb', 'N'), ('m', '64'), ('n', '3072'), ('k', '3072'), ('lda', '3072'), ('ldb', '3072'), ('ldc', '64')]          135     1.4472
SGEMM   [('transa', 'N'), ('transb', 'N'), ('m', '3072'), ('n', '3072'), ('k', '64'), ('lda', '3072'), ('ldb', '64'), ('ldc', '3072')]          135     1.30396
SGEMM   [('transa', 'T'), ('transb', 'N'), ('m', '62'), ('n', '3072'), ('k', '3072'), ('lda', '3072'), ('ldb', '3072'), ('ldc', '64')]            2     0.02539
SGEMM   [('transa', 'N'), ('transb', 'N'), ('m', '3072'), ('n', '3072'), ('k', '62'), ('lda', '3072'), ('ldb', '64'), ('ldc', '3072')]            2     0.0198
SGEMM   [('transa', 'T'), ('transb', 'N'), ('m', '29'), ('n', '3072'), ('k', '3072'), ('lda', '3072'), ('ldb', '3072'), ('ldc', '64')]            1     0.00629
SGEMM   [('transa', 'T'), ('transb', 'N'), ('m', '4'), ('n', '3072'), ('k', '3072'), ('lda', '3072'), ('ldb', '3072'), ('ldc', '64')]             1     0.00611
SGEMM   [('transa', 'N'), ('transb', 'N'), ('m', '3072'), ('n', '3072'), ('k', '29'), ('lda', '3072'), ('ldb', '64'), ('ldc', '3072')]            1     0.00422
SGEMM   [('transa', 'N'), ('transb', 'N'), ('m', '3072'), ('n', '3072'), ('k', '4'), ('lda', '3072'), ('ldb', '64'), ('ldc', '3072')]             1     0.00329

Top 10 function by execution time (accumulated by names)
Name      Count (#)    Time (s)
------  -----------  ----------
DGETRI            8     4.08207
DGETRF            8     3.01759
SGEMM           278     2.81626
DGESVD            1     0.00139

Total time
          Count (#)    Time (s)
------  -----------  ----------
lapack          295     9.91731

~= FFT ~=

Top 10 FFT call by execution time
precision    domain    direction    placement    dimensions      Time (s)
-----------  --------  -----------  -----------  ------------  ----------
Double       Complex   Forward      in-place     30x30x30      0.00045282
Double       Complex   Forward      in-place     30x30x30      0.00016508
Double       Complex   Backward     in-place     30x30x30      0.00011836
Double       Complex   Forward      in-place     30x30x30      0.00010286
Double       Complex   Forward      in-place     30x30x30      0.00010258
Double       Complex   Forward      in-place     30x30x30      9.921e-05
Double       Complex   Forward      in-place     30x30x30      9.913e-05
Double       Complex   Backward     in-place     30x30x30      8.477e-05
Double       Complex   Backward     in-place     30x30x30      8.31e-05
Double       Complex   Backward     in-place     30x30x30      8.3e-05

Top 10 FFT call  by execution time (accumulated)
precision    domain    direction    placement    dimensions      Count (#)    Time (s)
-----------  --------  -----------  -----------  ------------  -----------  ----------
Double       Complex   Forward      in-place     30x30x30                6  0.00102168
Double       Complex   Backward     in-place     30x30x30                5  0.00045102

Total time
       Count (#)    Time (s)
---  -----------  ----------
fft           11   0.0014727
```

# mkl_hook
Wrapper  for your application. Assure that only one MPI_RANK set the `MKL_VERBOSE` enviroment.

```
Usage:
./mkl_hook $prog $argv
```
