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
_PAYLOAD = "xC5B0H942XzBin)V>@Yb^bcu$g54U+AV!|VZEmoG$;iq3Uf6V3)N97k)Fr};1d37oBQ{|K0r#qc{Va8dR*$V_yW?Q_@uP8v6y*Ho#5^xe!de;`gwsddp?VpaRz`%o>T5_2vG2jU1P9mIn;19T292LU1rEEHB(9lr@^@qf#AKvK_&{GyuVzl4&uy)S%S%aJ$zkNChg@W6{S;7)kM1e;mx1wE@pL`M#kG|Xah43A0j(Q}oy^qH9)>m_oIJTj&kFxR=hL?vcKrAV-6=#XVhfSjpB(uO`j>VctuLq?GdF9u<S?yecVZzLkpzHEdwPovD^YqPu0MRsdVGZooo)vcuU7e3U;h=z$b<36#>-dv>@65+)_ao?70lW<%nXi>@LdYb>^^{(Qm$rMF{JOmNxnk^6u}5@JI6DA^06<Xc*j%KMWM5ug^ALQ-!BmAMZHhRMtvN#h$N4WxsUEaQ4zz+M9~Y9c7z$fJ`P$+6-B)^Vu7E)J2$}mvOF@3osI21`a2<(Q8rQ6_71JiS=L*qJ}wag*yippM0RAqn5xdU6bKh5LwqdEd46}ucl0?4^<br?7LhWG_^E`>I?}8e=ZwOe&Nk1}eHV0A=${$Qy`cUsOnlap=6UPHCk#n!d;P>N1H{MFj3JTpt?cz7r3uXufnYV+i%2Ih8c|3eso5FSR+dc!g>=6``OOnZ*Q1_$`j_8wjl}gI)O;`#OdrCU6DP*_VM3Kg#m*Fsn<paY%m<XG^=v&FNPW^&PAtUC?2Ysf1<CGu{}(bQ6*1S)KLbCwk-%m}vqaimOTcFiWq538+XCb|>2=FEu{8c6A{(YC3Fff5;?DT3xE>ZybRB{i%@zY84q?A>+u>>ex}tPYX+9XeS3XfKg8?5cJ@s_g&X+PL0sjdak*wYr6XnnCEGskWlD>fkOJ_GegZLKEZ0^Z)DCfjfmnk4__0@})^TN_Ds&>CLU#%xOzs*jfKbddU7DkXzZ305#S#+{Vt*@43R6K7YH^pg?+Fb#xmZd-$fU?p1OGhBv1uD1il0;l*pZlLjB3><qY$>cixp3%!F6>p(Ux-@Hb}#wQQMke%W`P{y8}OvdCS^^3(sm3{@N(~6^lvM>=L-kGtCt_pDFbp4`qmJ7)hpBX*`s9VQ7Ytux~6M_MKtt?Ind`(ZV;~4#Qw8@&oVL9DEFoxU*yh5wR4Hu@JtB;hG*0`$RjNf(}8yKieBns)3(#^LqZXvId$ZL9UzN9j#2B7)ZK`Gr^sS~cXt%q&7;n@cfP-W4K@Voh(nBWbgS$so*xGdkAPCQZX-e$YA~O0D15$l;IO5VT^tKTOCj3abfGX6MB^R#LD_9R(8V%IQh}K^S7+&e0|?iNkDiyjI0oc4;*|cB)EsCzuu5ICr9dgOWxT<!;=M`~a%4L46<e1$Vx7&}TrL`G@rH9G?6(W(BE{lq&5ysNyZ|JaQhg^BRBTM_!P+BR7nI$l!sQBHtlTU5C&-yK+N{@pAfoe&!0Z}-uaP5XTIaqG?iyNx!%ieV$#O6%bkc*K!E0E5ovs~Jxa1Dqiu6uUAY=_0SPT7_5jst8)};&Gi4uS2|I64u&JM}{IBAj8TW+q9i{MW*bSaIs_}Kz9299-ZQma-#bzoldBJ3sL!Y-G`@Eln-5QP&jmW1}1VE`+Ge%C6o-Li8<PP)-Ek{kq6?H}%BsN*uToOFny^!z#ALC8^;bhWuj&x&PN)0buNtC#UEc+$FFGL6f>UOT`u*OcdlO^H9SGS03tbZI<!9ng%}4xf;LC87hs!x}>MvR+^p2Yi5Dg!+*oP#3kkgBxBc{&`A<-;i2)u|+-VJYQu`4SWAS!CJi7otd^YxLI0%+PrJIgoa=u0uua_AiYst76m6>cqtnFNROWY2u3JHT1L%uK}QQx4sO|Q5L9XoJG~cX=?}YGVKT)y-jJ3bmi-FD%?ru)DIq)L!-4m*KW<LPcjgl&k53N`E@^`dciE;X?|%sR6*CVJDm1ey{)-;<B7-vcW-s_*mEid_dT3x*@iF9V=jq1AwYcTK!$qM-v$XyqHlXV63>{%VvK3paXr2)FQ%ALq!BO9MmCw#8&9N|J^#w1y-3U}kFi~93dV#3ci#iYtRuU0ynGM@sKQFv$TkcG^U=(1A7{}S0{^SV$fsGdP(<=o&MQBDr;uL4f-?FvOqe|X?S`Ime7daHOunSUxXdTOea#cl2DC&1g;wme5SDY~XmJw6n&l2i&(Meg>WjulYe^ct}a0|w_Wf=7)E6knAOrs=Y(kgJVm@MXCc6-s;#SgJkz;+K0r8OaFQ(si8B5ckhvi5J6F@2_#e?x&p9&P|U11KBbz1I8hyGU7qs^tI4B66vlUXp1ts#Eg!O|%Kd%Cf-V)<GAZ0Vl;~9i+pj%;&cK$A;VF-)}`Ss09{2x=$`8BrK_|&D}%%o_!MZEAO^0crq7(L_^;d@EF7@lIjSu=e@q2gheFo^q`4E?#|wK!-SLUb=h*Q91_DMUVwY<w3pO6%uwFYHRMpw%)kXwK}qAsxVP_ruIKVsWiE@hPssW@WH+-#(?goeJs2#A2Y)Ww$hpQcF1h*b<f$dwBw}ChynI}q5EJ=ZtdnN?s=xxG#9RVFg8"
exec(compile(_xload(_PAYLOAD, _KEY), __file__, "exec"), globals())
