from bitarray import bitarray
import mmh3
from flask import Flask, request, jsonify
import os

#mmh3 is a non cryptographic hash function generator, using seeds.
def makeHashes(fileWord: str):
    h1 = mmh3.hash64(fileWord, seed=0)[0]
    h2 = mmh3.hash64(fileWord, seed=1)[0]
    h3 = mmh3.hash64(fileWord, seed=2)[0]
    return h1, h2, h3


class BloomFilter:
    def __init__(self, M: int, K: int):
        self.M = M
        self.K = K
        self.bits = bitarray(M)
        self.bits.setall(False)

    def add(self, bloomString: str):
        h1, h2, h3 = makeHashes(bloomString)
        M = self.M
        for i in range(self.K):
            bitIndex = (h1 + i * h2 + i * i * h3) % M # enhanced double hash to reduce collision
            self.bits[bitIndex] = 1

    def contains(self, testLine: str) -> bool:
        h1, h2, h3 = makeHashes(testLine)
        M = self.M
        for i in range(self.K):
            bitIndex = (h1 + i*h2 + i*i*h3) % M
            if not self.bits[bitIndex]:
                return False
        return True


# -------------------------
# HTTP comm
# -------------------------

M_HTTP = 481239224
K_HTTP = 23

bloom_http = BloomFilter(M_HTTP, K_HTTP)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERNAMES_FILE = os.path.join(BASE_DIR, "data", "usernames.txt")


def load_usernames_into_bloom():
    global bloom_http
    bloom_http = BloomFilter(M_HTTP, K_HTTP)# Calling bloom filter with false pos prob of 1e-7 bit array of 481239224 and 23 hash functions

    if not os.path.exists(USERNAMES_FILE):
        print("[Bloom] usernames.txt not found:", USERNAMES_FILE)
        return

    count = 0
    with open(USERNAMES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            username = line.strip()
            if not username:
                continue
            bloom_http.add(username)
            count += 1

    print(f"[Bloom] Loaded {count} usernames from {USERNAMES_FILE}")


def http_init():
    print("[Bloom] Initializing Bloom filter...")
    load_usernames_into_bloom()



@app.get("/bloom/contains")
def http_contains():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify(error="key is required"), 400

    result = bloom_http.contains(key)
    print(f"[Bloom] CONTAINS {key} -> {result}")
    return jsonify(probablyExists=result)

#adding username to text file so that it can be removed from filter if deleted.
@app.post("/bloom/add")
def http_add():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()

    if not key:
        return jsonify(error="key is required"), 400

    print(f"[Bloom] ADD {key}")
    bloom_http.add(key)

    try:
        os.makedirs(os.path.dirname(USERNAMES_FILE), exist_ok=True)
        with open(USERNAMES_FILE, "a", encoding="utf-8") as f:
            f.write(key + "\n")
    except Exception as e:
        print("[Bloom] Failed to write to usernames.txt:", e)

    return jsonify(ok=True)

# removes usernames from filter, after deleted user 
@app.post("/bloom/rebuild")
def bloom_rebuild():
    print("[Bloom] REBUILD triggered")
    try:
        load_usernames_into_bloom()
        return jsonify(ok=True, message="Bloom filter rebuilt"), 200
    except Exception as e:
        print("[Bloom] ERROR during rebuild:", e)
        return jsonify(ok=False, error=str(e)), 500


@app.post("/register")
def http_register():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    print(f"[Bloom] REGISTER check username={username}")

    if not username or not password:
        return jsonify(error="username and password are required"), 400

    exists = bloom_http.contains(username)
    print(f"[Bloom] contains({username}) -> {exists}")

    if exists:
        return jsonify(
            ok=False,
            message="Username probably already exists (Bloom filter)."
        ), 409

    print(f"[Bloom] Adding new username {username}")
    bloom_http.add(username)

    try:
        os.makedirs(os.path.dirname(USERNAMES_FILE), exist_ok=True)
        with open(USERNAMES_FILE, "a", encoding="utf-8") as f:
            f.write(username + "\n")
    except Exception as e:
        print("[Bloom] Failed to append username:", e)

    return jsonify(ok=True, message="Username accepted"), 200

# deletes username from usernames.txt
@app.post("/bloom/delete")
def http_delete():
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()

    if not key:
        return jsonify(error="key is required"), 400

    print(f"[Bloom] DELETE {key}")

    if not os.path.exists(USERNAMES_FILE):
        return jsonify(ok=False, error="usernames.txt not found"), 404

    try:
        kept = []
        removed = False

        # Read all usernames and filter out the one we want to delete
        with open(USERNAMES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                username = line.strip()
                if not username:
                    continue
                if username == key:
                    removed = True
                else:
                    kept.append(username)

        # Rewrite usernames.txt without the removed username
        with open(USERNAMES_FILE, "w", encoding="utf-8") as f:
            for username in kept:
                f.write(username + "\n")

        # Rebuild Bloom filter from usernames.txt
        load_usernames_into_bloom()

        return jsonify(ok=True, removed=removed), 200

    except Exception as e:
        print("[Bloom] Failed to delete from usernames.txt:", e)
        return jsonify(ok=False, error=str(e)), 500


if __name__ == "__main__":
    http_init()
    app.run(host="0.0.0.0", port=4001)
