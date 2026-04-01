"""
x_encode 算法实现 - 用于 Srun4000 认证

从 JavaScript 版本翻译，关键修复：
1. 无符号右移 (>>>): 用 & 0xFFFFFFFF 模拟
2. 运算符优先级差异
3. 字符编码处理
4. 自定义 base64 字母表
"""

import base64


def _js_unsigned_right_shift(x, bits):
    """模拟 JavaScript 的无符号右移 >>>"""
    return (x & 0xFFFFFFFF) >> bits


def _s(a, b):
    """将字符串转换为整数数组（每4个字符一个32位整数）"""
    v = []
    a_len = len(a)
    for i in range(0, a_len, 4):
        c0 = ord(a[i])
        c1 = ord(a[i + 1]) if i + 1 < a_len else 0
        c2 = ord(a[i + 2]) if i + 2 < a_len else 0
        c3 = ord(a[i + 3]) if i + 3 < a_len else 0
        v.append(c0 | (c1 << 8) | (c2 << 16) | (c3 << 24))

    if b:
        v.append(a_len)

    return v


def _l(a, b):
    """将整数数组转换回字符串

    JavaScript 的 String.fromCharCode(a[i] & 0xFF, a[i] >>> 8, ...) 返回 UTF-16 字符串
    每个 16 位值对应一个字符
    """
    v = []
    for i in range(len(a)):
        # 每个 32 位整数被拆成 4 个 8 位值，然后转为 4 个 Latin1 字符
        v.append(chr(a[i] & 0xFF))
        v.append(chr((a[i] >> 8) & 0xFF))
        v.append(chr((a[i] >> 16) & 0xFF))
        v.append(chr((a[i] >> 24) & 0xFF))
    result = ''.join(v)

    if b:
        # JavaScript: c = d - 1 << 2 = (len(a) - 1) * 4 = original string byte length
        # The last element in v was the original string length
        c = a[len(a) - 1]
        return result[:c]
    return result


def x_encode(str_data, key):
    """
    x_encode 加密函数

    Args:
        str_data: 要加密的字符串（JSON格式的登录信息）
        key: 密钥（challenge）

    Returns:
        加密后的字符串
    """
    if not str_data:
        return ""

    v = _s(str_data, True)  # 加密输入
    k = _s(key, False)       # 密钥

    # 密钥长度不足4位则补0
    while len(k) < 4:
        k.append(0)

    n = len(v) - 1
    z = v[n]
    y = v[0]

    c = 0x86014019 | 0x183639A0

    q = 6 + 52 // (n + 1)
    d = 0

    while q > 0:
        d = (d + c) & 0xFFFFFFFF
        e = _js_unsigned_right_shift(d, 2) & 3

        # 前 n 个元素
        for p in range(n):
            y = v[p + 1]
            # JavaScript: m = z >>> 5 ^ y << 2 + (y >>> 3 ^ z << 4) ^ (d ^ y) + k[(p & 3) ^ e] ^ z
            # 注意运算符优先级：+ 和 ^ 的优先级低于 << 和 >>
            # 所以实际是: m = ((z >>> 5) ^ (y << 2)) + (((y >>> 3) ^ (z << 4)) ^ ((d ^ y))) + (k[...] ^ z)
            m = (_js_unsigned_right_shift(z, 5) ^ (y << 2)) + \
                ((_js_unsigned_right_shift(y, 3) ^ (z << 4)) ^ (d ^ y)) + \
                (k[(p & 3) ^ e] ^ z)
            m = m & 0xFFFFFFFF
            v[p] = (v[p] + m) & 0xFFFFFFFF
            z = v[p]

        # 最后一个元素
        y = v[0]
        m = (_js_unsigned_right_shift(z, 5) ^ (y << 2)) + \
            ((_js_unsigned_right_shift(y, 3) ^ (z << 4)) ^ (d ^ y)) + \
            (k[(n & 3) ^ e] ^ z)
        m = m & 0xFFFFFFFF
        v[n] = (v[n] + m) & 0xFFFFFFFF
        z = v[n]

        q -= 1

    return _l(v, False)


# 自定义 base64 编码器（使用与浏览器相同的字母表）
CUSTOM_BASE64_ALPHABET = 'LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA'
STANDARD_BASE64_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'


def custom_base64_encode(data: str) -> str:
    """
    使用自定义字母表的 base64 编码

    Args:
        data: 输入字符串（通常是 x_encode 的二进制输出）

    Returns:
        自定义 base64 编码后的字符串
    """
    # 先用标准 base64 编码
    standard_b64 = base64.b64encode(data.encode('latin1')).decode('latin1')

    # 转换字母表
    translation_table = str.maketrans(STANDARD_BASE64_ALPHABET, CUSTOM_BASE64_ALPHABET)
    return standard_b64.translate(translation_table)


def x_encode_with_custom_base64(str_data: str, key: str) -> str:
    """
    x_encode 加密并使用自定义 base64 编码

    Args:
        str_data: 要加密的字符串
        key: 密钥（challenge）

    Returns:
        {SRBX1} 前缀 + 自定义 base64 编码的密文
    """
    encrypted = x_encode(str_data, key)
    encoded = custom_base64_encode(encrypted)
    return f"{{SRBX1}}{encoded}"
