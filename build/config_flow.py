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
_PAYLOAD = "xC00@mYWPxFC?b_epwF#?9VG`b0N+n^{L{$VEmm2themB%5Vbs|0L^s>A8`}8^0d_w<@9^;rrKGE@lV*ScB1h;Xq(-h>B%@2LGW(DgfsyxzU+Qt?|FK2@(@fjrv$h0pJ4DRceO4k?B}mgbu0ydx{D<l^^X05*n^Nr$lrlUOtqKgox1JKn)v_QO*Xs>us8a<-wAB8A3%r$J_NfL4xiZ-jJ+ORRBF(qw6IG5KPA2{%oE2V+#<K4SvrKH^2bqJ<^mPw-hYS=(}vr-*}apmlgPa<z3i7-)4JzW}GL(eAHf9Oc>G8nxf8{$~Yxlq?*mR>r0<=t~XUI=9vtYi_?t%G#OxWm+pY<4D-N_p~i^=6I1)^PF)H*KQ^JWl{!@V4;rA%o^Mz$P}8gRGbWN;{vr<K?eTNcr4NX2mP7-&Lf=9N?{5m-@U1M!L7wYPFr&eed+XxK=}~f^ibuVL0M9Bs)X)?VLsFz82MKnzP-W;hsxS_(q(!?@*I4aRW3#fu#1JH#LpKV*?pQ?~H!kT3w(mM#8tF@qbaO6bZnT9#FoF8uUAh;wbNhg2_%=0#&^!7~JRxECorR>t0YCOY$2J<0E&>#o>+;eXgV2#Nn)fvefKCjVOpH03Vb`o~pFV%!7Kk*`US&3jWw>arX}S^i;`U&|X01<ZQ45D{Y4LU2U9RL#dlQg=DoVJ|5Kje)0uk_)^l1x+{|Qr6O6gbOM~SHlR@m1t59WQSe!RrQRbo7OsB3_Ktr_gctDos4^hMS7Eg2MB=_959iT9S&x%AWYPGXtn1_w2nFdS>KhKiBUFY5R=V)>y0R!B)APqv$Y$R`r=N^W@)Ub*#gy)5Bq#=!aYdp6AR6Sh!7Q45qI647E(9QyPSmQaRps>=#SDpC?6S3Ifh3SHv65^YZj_Gc8*RS8dnKWPwbn1VADw9}hAc-zDcua4z7>%r8Fr`-i|^fxHrVp!n0y>nILF^SbS`PO+O$(Le{-b@`2^qP4"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
