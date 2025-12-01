## bloom-service
HOW TO RUN:

code is designed to be run in conjunction with login, could be another use outside of login but re-writing would have to be done. 
This can be run using pip install requirements, will be updating to show how to use with login
followed by python3 bloomFilter.py within the bloom directory. Note that while bloom filter is secure the 
HTTP server hosting this is NOT.

As an example you can add a POST route to check with the bloom filter when registering a new user for login.

```
p.post('/register', async (req, res) => {
  const { username, password } = req.body;

  console.log('[REGISTER] Incoming:', username, password);

  if (!username || !password) {
    return res.render('register', {
      registerMode: true,
      error: 'Username and password are required.'
    });
  }

  const firstname = username;
  const powerLevel = 1;

  try {
    // Ask Bloom service if username probably exists
    try {
      const containsRes = await fetch(
        `${BLOOM_BASE_URL}/bloom/contains?key=${encodeURIComponent(username)}`
      );

      const containsJson = await containsRes.json();
      console.log('[REGISTER] Bloom /bloom/contains response:', containsRes.status, containsJson);

      if (containsRes.ok && containsJson.probablyExists) {
        return res.render('register', {
          registerMode: true,
          error: 'That username probably already exists (Bloom filter).'
        });
      }
```
