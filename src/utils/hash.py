"""
Utility to generate Comix.to API hashes.
Ported from TypeScript implementation.
"""

import base64
import urllib.parse

class ComixHash:
    # [RC4 key, mutKey, prefKey] × 5 rounds
    KEYS = [
        "JxTcdyiA5GZxnbrmthXBQfU2IMTKcY1+3nNhbq98Sgo=",  # 0  RC4 key  round 1
        "3PordjODbhqla382Cxapmo/1JiABJQcjiJj1+48gTJ4=",  # 1  mutKey   round 1
        "OaKvnI5ARA==",                                   # 2  prefKey  round 1
        "MHNBHYWA7lvy867fXgvGcJwWDk79KqUJUVFsh3RwnnI=",  # 3  RC4 key  round 2
        "8i0Cru/VJBSVB2Y1GcMDVpzx2WepOcfnWdd81yxICl4=",  # 4  mutKey   round 2
        "Fyskubz8VvA=",                                   # 5  prefKey  round 2
        "B46L1x+UeWP+19cRpQ+OZvdLAK9EHID8g3mSgn57tew=",  # 6  RC4 key  round 3
        "DTSTmUt6LpDUw9r1lSQqyb3YlFTzruT8tk8wUGkwehQ=",  # 7  mutKey   round 3
        "vY/meeI=",                                       # 8  prefKey  round 3
        "7xWfIF5THL5LAnRgAARg+4mjWHPU9n3PQwvzbaMNi+Q=",  # 9  RC4 key  round 4
        "bewtiTuV+HJk56xxkf2iCljLgruCpBmN9BgE8i6gc9M=",  # 10 mutKey   round 4
        "/Xcb2zAu8AU=",                                   # 11 prefKey  round 4
        "WgeCQ3T8R51uTwVSiVa7Zy0dN6JOg6Z5JleMS+HV8Aw=",  # 12 RC4 key  round 5
        "yXayUVFrrcW56jQCEfZzuCidjpnWKjTDUNT7XeX9i7k=",  # 13 mutKey   round 5
        "tSLco2w=",                                       # 14 prefKey  round 5
    ]

    @classmethod
    def get_key_bytes(cls, index):
        b64 = cls.KEYS[index] if index < len(cls.KEYS) else None
        if b64 is None:
            return []
        try:
            return [b & 0xFF for b in base64.b64decode(b64)]
        except Exception:
            return []

    @staticmethod
    def rc4(key, data):
        if not key:
            return data
        s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + key[i % len(key)]) % 256
            s[i], s[j] = s[j], s[i]
        i = j = 0
        out = []
        for k in data:
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            out.append(k ^ s[(s[i] + s[j]) % 256])
        return out

    @staticmethod
    def get_mut_key(mk, idx):
        return mk[idx % 32] if mk and (idx % 32) < len(mk) else 0

    @staticmethod
    def op_shift_right7_left1(e):
        return ((e >> 7) | (e << 1)) & 255

    @staticmethod
    def op_shift_left1_right7(e):
        return ((e << 1) | (e >> 7)) & 255

    @staticmethod
    def op_shift_right2_left6(e):
        return ((e >> 2) | (e << 6)) & 255

    @staticmethod
    def op_shift_left4_right4(e):
        return ((e << 4) | (e >> 4)) & 255

    @staticmethod
    def op_shift_right4_left4(e):
        return ((e >> 4) | (e << 4)) & 255

    @classmethod
    def mutate(cls, data, mut_key, pref_key, pref_key_limit, round_num):
        out = []
        for o in range(len(data)):
            if o < pref_key_limit and o < len(pref_key):
                out.append(pref_key[o])
            n = data[o] ^ cls.get_mut_key(mut_key, o)
            if round_num == 1:
                if o % 10 == 0:
                    n = cls.op_shift_right7_left1(n)
                elif o % 10 == 1:
                    n ^= 37
                elif o % 10 == 2:
                    n ^= 81
                elif o % 10 == 3:
                    n ^= 147
                elif o % 10 == 4:
                    n = cls.op_shift_right2_left6(n)
                elif o % 10 in (5, 8):
                    n = cls.op_shift_right4_left4(n)
                elif o % 10 == 6:
                    n ^= 218
                elif o % 10 == 7:
                    n = (n + 159) & 255
                elif o % 10 == 9:
                    n ^= 180
            elif round_num == 2:
                if o % 10 in (0, 9):
                    n ^= 180
                elif o % 10 == 1:
                    n = cls.op_shift_left1_right7(n)
                elif o % 10 == 2:
                    n ^= 147
                elif o % 10 == 3:
                    n = cls.op_shift_right7_left1(n)
                elif o % 10 == 4:
                    n = cls.op_shift_right2_left6(n)
                elif o % 10 == 5:
                    n = cls.op_shift_right4_left4(n)
                elif o % 10 in (6, 8):
                    n = (n + 159) & 255
                elif o % 10 == 7:
                    n = (n + 34) & 255
            elif round_num == 3:
                if o % 10 == 0:
                    n ^= 81
                elif o % 10 == 1:
                    n = cls.op_shift_right4_left4(n)
                elif o % 10 in (2, 9):
                    n = cls.op_shift_left4_right4(n)
                elif o % 10 == 3:
                    n ^= 37
                elif o % 10 == 4:
                    n = (n + 159) & 255
                elif o % 10 == 5:
                    n = cls.op_shift_left1_right7(n)
                elif o % 10 == 6:
                    n ^= 180
                elif o % 10 == 7:
                    n = (n + 34) & 255
                elif o % 10 == 8:
                    n = cls.op_shift_right2_left6(n)
            elif round_num == 4:
                if o % 10 in (0, 7):
                    n ^= 218
                elif o % 10 in (1, 4):
                    n = cls.op_shift_left1_right7(n)
                elif o % 10 == 2:
                    n = cls.op_shift_right7_left1(n)
                elif o % 10 == 3:
                    n = (n + 159) & 255
                elif o % 10 in (5, 8):
                    n ^= 180
                elif o % 10 == 6:
                    n ^= 147
                elif o % 10 == 9:
                    n ^= 37
            elif round_num == 5:
                if o % 10 == 0:
                    n = cls.op_shift_left4_right4(n)
                elif o % 10 in (1, 3):
                    n ^= 147
                elif o % 10 == 2:
                    n = (n + 34) & 255
                elif o % 10 in (4, 9):
                    n ^= 218
                elif o % 10 in (5, 7):
                    n = cls.op_shift_left1_right7(n)
                elif o % 10 == 6:
                    n ^= 180
                elif o % 10 == 8:
                    n = cls.op_shift_right2_left6(n)
            out.append(n & 255)
        return out

    @classmethod
    def round1(cls, data):
        mut = cls.mutate(data, cls.get_key_bytes(1), cls.get_key_bytes(2), 7, 1)
        return cls.rc4(cls.get_key_bytes(0), mut)

    @classmethod
    def round2(cls, data):
        mut = cls.mutate(data, cls.get_key_bytes(4), cls.get_key_bytes(5), 8, 2)
        return cls.rc4(cls.get_key_bytes(3), mut)

    @classmethod
    def round3(cls, data):
        mut = cls.mutate(data, cls.get_key_bytes(7), cls.get_key_bytes(8), 5, 3)
        return cls.rc4(cls.get_key_bytes(6), mut)

    @classmethod
    def round4(cls, data):
        mut = cls.mutate(data, cls.get_key_bytes(10), cls.get_key_bytes(11), 8, 4)
        return cls.rc4(cls.get_key_bytes(9), mut)

    @classmethod
    def round5(cls, data):
        mut = cls.mutate(data, cls.get_key_bytes(13), cls.get_key_bytes(14), 5, 5)
        return cls.rc4(cls.get_key_bytes(12), mut)

    @classmethod
    def generate_hash(cls, path):
        encoded = urllib.parse.quote(path, safe='') \
            .replace("+", "%20") \
            .replace("*", "%2A") \
            .replace("%7E", "~")

        initial_bytes = [b & 0xFF for b in encoded.encode('ascii')]
        r1 = cls.round1(initial_bytes)
        r2 = cls.round2(r1)
        r3 = cls.round3(r2)
        r4 = cls.round4(r3)
        r5 = cls.round5(r4)
        
        # JS GetURLBase64FromBytes equivalent
        return base64.urlsafe_b64encode(bytes(r5)).decode('ascii').rstrip('=')

def generate_comix_hash(path: str) -> str:
    """Convenience function to generate the Comix Hash."""
    return ComixHash.generate_hash(path)
