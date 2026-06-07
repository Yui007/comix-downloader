import os

def analyze(path):
    if not os.path.exists(path):
        print(f"File {path} not found")
        return
        
    with open(path, "rb") as f:
        data = f.read()
        
    print(f"Size: {len(data)}")
    print(f"Hex: {data[:20].hex()}")
    
    # Try brotli
    try:
        import brotli
        dec = brotli.decompress(data)
        print(f"Brotli decompressed! Size: {len(dec)}")
        print(f"Brotli Hex: {dec[:20].hex()}")
    except Exception as e:
        print(f"Brotli failed: {e}")
        
    # Try gzip
    try:
        import gzip
        dec = gzip.decompress(data)
        print(f"Gzip decompressed! Size: {len(dec)}")
        print(f"Gzip Hex: {dec[:20].hex()}")
    except Exception as e:
        print(f"Gzip failed: {e}")
        
    # Try zlib
    try:
        import zlib
        dec = zlib.decompress(data)
        print(f"Zlib decompressed! Size: {len(dec)}")
    except Exception as e:
        print(f"Zlib failed: {e}")

analyze("downloads/Boruto_ Two Blue Vortex/Chapter_1/004.jpg")
