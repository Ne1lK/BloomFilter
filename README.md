## bloom-service
HOW TO RUN:

code is designed to be run in conjunction with login, could be another use outside of login but re-writing would have to be done. 
This can be run using pip install requirements, will be updating to show how to use with login
followed by python3 bloomFilter.py within the bloom directory. Note that while bloom filter is secure the 
HTTP server hosting this is NOT.

As an example you can add a POST route to check with the bloom filter when registering a new user for login. Bloom is well documented but you will need to add routes to reset the filter if you're deleting users since you dont want users that dont exist in login in the bit array.

#response data
```
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
```


#request data
 const containsRes = await fetch(
        `${BLOOM_BASE_URL}/bloom/contains?key=${encodeURIComponent(username)}`
      );

      const containsJson = await containsRes.json();
      console.log('[REGISTER] Bloom /bloom/contains response:', containsRes.status, containsJson);