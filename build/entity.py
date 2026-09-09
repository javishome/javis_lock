# -*- coding: utf-8 -*-
# Protected by Javis Universal Dynamic Encrypted Loader
import base64 as _b85, zlib as _zl
def _xload(_s, _k):
    _e = _b85.b85decode(_s)
    _o = bytearray()
    _p = 0xAA
    _kl = len(_k)
    for _i, _b in enumerate(_e):
        _o.append(_b ^ (_k[_i % _kl] ^ _p))
        _p = _b
    return _zl.decompress(bytes(_o))

_KEY = b'javis_universal_dynamic_loader_2026_'
_PAYLOAD = "xC8jYU{Sx}oR<|$6QA<d_&xR1FVcs!HLUw;qMs{&c7m9ZbB`b|5$0*=I>?D$0I<63j005iSk~*K8QQC?j2mxuUoLW(#B(O$Cy5|suY_^PxoIj5S8hvKByAQSaYTk2sF6ubl!5IKxPe1!5^EQ<cs}A(M#3eV+rDr?(Q40Hrp@gtT=2lO7qR2XwFmhw_70e0n-@Uyb?IYpq7)ME&fxaF0)gr&ctCwXN~^BpopD$XYcu5((#xnSwrk>lv}stOaNLssCOf@N+x5}OnN(qW;WF650J8-~ON4jRae9lV><m)%eqBu+)?%=`K$UbXvwi(H{GbK^HAdXT?}W3_Dp|wdY{_m3v{%%;V$#TUFI&lSwc_kIWSaaRzsV5@$bcg0QGnq`GZi?p=QC*151}oi2=3=gN|eUHra8>-Ok<Fcbd+4{Hk#fK1MUt?wW$|;)9IMTg#+Y`+ILSHTy5P6&AwbsuvWA0kW0-d?h5g)p>5l14fN(BQo;RL5q~pwBK40@h{M%OhX`kT4@2Vq`E)Zb<}yC^JV2YmBp=%in*YS%$5Au&*JW8nAtAC#{<-Vkmsa*%CStmBA?y4wo|Vuo+pv4ZQXkBGqk4EudhTz2K<*>w5p2y4TbKRZ<2ff^$FO1Oby15IRrIX=4T<_v^V)<&Lks"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
