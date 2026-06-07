import requests
from PIL import Image
from io import BytesIO

url = "https://wowpic.cc/images/40/66432f7a55269.jpg" # This is a random url from the site, let me try it. Actually I don't know a valid url.

# Let's instead try to decode the file directly using Image.open to see the EXACT error
try:
    img = Image.open("downloads/Boruto_ Two Blue Vortex/Chapter_1/004.jpg")
    print(img.size)
except Exception as e:
    print("PIL Error:", e)

