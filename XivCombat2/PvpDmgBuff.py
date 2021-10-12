mubiaozhiyebuzheng = {  # 目标职业增伤补正
    0: 1,  # 好像是木桩
    19: 0.7,  # 'Paladin',  # 骑士PLD
    20: 0.7,  # 'Monk',  # 武僧MNK
    21: 0.7,  # 'Warrior',  # 战士WAR
    22: 0.75,  # 'Dragoon',  # 龙骑士DRG
    23: 1,  # 'Bard',  # 吟游诗人BRD
    24: 1,  # 'WhiteMage',  # 白魔法师WHM
    25: 1,  # 'BlackMage',  # 黑魔法师BLM
    # 26: #'Arcanist',  # 秘术师ACN
    27: 1,  # 'Summoner',  # 召唤师SMN
    28: 1,  # 'Scholar',  # 学者SCH
    30: 0.75,  # 'Ninja',  # 忍者NIN
    31: 1,  # 'Machinist',  # 机工士MCH
    32: 0.7,  # 'DarkKnight',  # 暗黑骑士DRK
    33: 1,  # 'Astrologian',  # 占星术士AST
    34: 0.7,  # 'Samurai',  # 武士SAM
    35: 0.8,  # 'RedMage',  # 赤魔法师RDM
    # 36: #'BlueMage',  # 青魔BLM
    37: 0.7,  # 'Gunbreaker',  # 绝枪战士GNB
    38: 1,  # 'Dancer',  # 舞者DNC
}
zijizhiyebuzheng = {  # 自己职业增伤补正
    19: 1.15,  # 'Paladin',  # 骑士PLD
    20: 1.15,  # 'Monk',  # 武僧MNK
    21: 1.15,  # 'Warrior',  # 战士WAR
    22: 1.15,  # 'Dragoon',  # 龙骑士DRG
    23: 1,  # 'Bard',  # 吟游诗人BRD
    24: 1,  # 'WhiteMage',  # 白魔法师WHM
    25: 1,  # 'BlackMage',  # 黑魔法师BLM
    # 26: #'Arcanist',  # 秘术师ACN
    27: 1,  # 'Summoner',  # 召唤师SMN
    28: 1,  # 'Scholar',  # 学者SCH
    30: 1.15,  # 'Ninja',  # 忍者NIN
    31: 1,  # 'Machinist',  # 机工士MCH
    32: 1.15,  # 'DarkKnight',  # 暗黑骑士DRK
    33: 1,  # 'Astrologian',  # 占星术士AST
    34: 1.15,  # 'Samurai',  # 武士SAM
    35: 1,  # 'RedMage',  # 赤魔法师RDM
    # 36: #'BlueMage',  # 青魔BLM
    37: 1.15,  # 'Gunbreaker',  # 绝枪战士GNB
    38: 1,  # 'Dancer',  # 舞者DNC
}

# 目标的易伤buff
mubiaozengshang10 = [
    2035,  # 天辉
    2014,  # 攻其不备
    2077,  # 狂魂
    2078,  # 混沌旋风
    2019,  # 毒菌冲击
    2066,  # 近战被枪刃抽取
]
mubiaozengshang20 = [
    1896,  # 幻影弹
]
mubiaozengshang25 = [
    1408,  # 法系LB
]
# 目标的减伤buff
mubiaojianshang10 = [
    2178,  # 大地神的抒情恋歌
    2038,  # 节制群体buff
    2034,  # 占卜
    2172,  # 亲疏自行自身buff
    2061,  # 原初的勇猛
    2062,  # 原初的武猛
    2052,  # 扇舞·急
    2177,  # 策动
    2006,  # 金刚体势
    2171,  # 暗黑布道
    2063,  # 枪刃抽近融合
]
mubiaojianshang20 = [
    1452,  # 王冠之贵妇
    2053,  # 护盾
    1978,  # 铁壁
]
mubiaojianshang25 = [
    655,  # TLB
]
mubiaojianshang30 = [
    2020,  # 干预 没有铁壁附加效果只有20 但是两个buff是一样的 按高的算
]
mubiaojianshang50 = [
    1240,  # 必杀剑·地天
    # 抵消伤害的盾，我不会查盾值，先全当作50%减伤算
    # 1308,  # 至黑之夜
    # 1997,  # 残暴弹
    # 2179,  # 掩护盾
    # 2011,  # 缩地
    # 1993,  # 摆脱
    # 2071,  # 天星冲日
    # 2043,  # 中间学派状态下奶出的盾
    # 2033,  # 交剑
    # 1989,  # 魔罩
    # 1331,  # 鼓舞
    # 2008,  # 金刚极意
]
# 自身的加伤害buff
zijizengshang5 = [
    2215,  # 放浪神的小步舞曲
]
zijizengshang10 = [
    2034,  # 占卜
    2022,  # 剑舞
    2005,  # 红莲体势
    1183,  # 巨龙右眼 自身
    1184,  # 巨龙左眼 目标
    2064,  # 枪刃抽远融合
]
zijizengshang20 = [
    1451,  # 王冠之领主
    2037,  # 节制自己的buff
]
# 自身受到的减少伤害buff
zijijianshang10 = [
    2076,  # 悔罪
    2181,  # 亲疏自行反弹buff
    2067,  # 远程被枪刃抽取
]
zijijianshang20 = [
    2101,  # 雪仇
]
zijijianshang40 = [
    1988,  # 昏乱
]


# 2282 鼓励 随时间衰减的10% 2173 2174 武僧义结金兰的两个buff不知道哪个是5%增伤 同时出现结束 而且只有物理增伤 这两个比较怪而且少见 先不管
# 2185 牵制 不会查buff是不是自己上的 自己上没有增伤 先不管
# 获取buff持续时间是
# teffects[effect_id].timer
# 获取buff来源是
# teffects[effect_id].actorId

def get_buff(actor):
    # info(f"{target.job.name")
    # info(f"{target.job.raw_value}")
    # info(f"{target.job.value()")
    # info(f"{data.effects}")
    # info(f"{target.effects.get_dict()}")
    b = 1
    effect = actor.effects.get_dict()
    for i in range(2131, 2136):
        if i in effect:
            b += 0.1 * (i - 2130)
            break
    for i in zijizengshang5:
        if i in effect:
            b *= 1.05
    for i in zijizengshang10:
        if i in effect:
            b *= 1.1
    for i in zijizengshang20:
        if i in effect:
            b *= 1.2
    for i in zijijianshang10:
        if i in effect:
            b *= 0.9
    for i in zijijianshang20:
        if i in effect:
            b *= 0.8
    for i in zijijianshang40:
        if i in effect:
            b *= 0.6
    return b * 0.95


def get_tbuff(target):  # 目标的有效生命
    c = 1
    c /= mubiaozhiyebuzheng[target.job.raw_value]
    teffects = target.effects.get_dict()
    if 1302 in teffects:
        return 0
    for i in mubiaozengshang10:
        if i in teffects:
            c /= 1.1
    for i in mubiaozengshang20:
        if i in teffects:
            c /= 1.2
    for i in mubiaozengshang25:
        if i in teffects:
            c /= 1.25
    for i in mubiaojianshang10:
        if i in teffects:
            c /= 0.9
    for i in mubiaojianshang20:
        if i in teffects:
            c /= 0.8
    for i in mubiaojianshang30:
        if i in teffects:
            c /= 0.7
    for i in mubiaojianshang50:
        if i in teffects:
            c /= 0.5

    return c
