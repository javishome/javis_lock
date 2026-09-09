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
_PAYLOAD = "xB~z>h@}ctDdTk#`*Yrt6y>cA#O+RkNWLrI4&g|mCJtH6;R9Fz;r2qcAT8G*j(451<mcwl(oBNyAOxYEPE83IFhRw}$3-I@BtY8{F76!Un@ea<I^mjP`+^<LA|uDO>%Pq)vt9t&f{rLxZ3<ffeS)dpqx81YPbSQTc&HfwXrmR{#x`zivvy-}u^VMu&z~`j6iPLV)1brEHN~h6n9N2j)2Q=Um>>jiVz}HC{KlJK&szS}{sVN(<~_j_>yJ`#MKtp*Kcqq#fGhdATZBB&5<joX(E?+;7eAqZvr7;UE#M>F5emGuR}DjAw$e*0`mgy-rT;nm<Vt97>^<9ZuC|N#<S&~^<e(Yit^?oGoSJthipwU=Ns$;>%*AX&O_*oM#v02hv_ngWaV%Kri`qV$aw#a-4qZ~wRbZ4C5w-8}OHkuaq}b{=&wsE5c<5Q8B_F1Oo^~7fK<L8G>|NrQnMdDTCWQo4fi?O0(C#D1JC`9=Akd@OFQ+Fh2W!JqlZvz~<c-^a9iD#l;9^J$q~5;^4Vy%%gXVUcDG|#F4wO?+=1^DABQyya@!0f-ktC(VQx`?Hn;@3LXBQTJkxA%I?lmvonpsw30c5nR=}w##L71&o?VY77{Xbk-Wp40I@jgTNA?vXr5-z$sicSLKNzB-Guwe2yV3>N(-fH3RJHqfh2w5htmKeg+Lx}y>t_*%MubUpt^Ilg1IvNC($_g4gR(97#>_}|6(dr6Ny}&wXd|wz#>rUD+s530ctf4SRr+QVP`Va)i!i=I~15uUTF@3U|"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
