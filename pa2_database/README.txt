Name:Cheng Fei
NetID: cf482



Challenges Attempted: Tier I, Tier II, Tier III

Answers:

Tier I:
These extra routes require authorization because passwords are required to retrieve information inside. And having passwords indicates that information in it is confidential. So calling these routes require authorization.

Tier II:
Through password hashing, users' password are encrypted and protected against unauthorized hackers. Even when database is leaked, hackers will only have access to hashed strings, instead of the plain password itself. This method raises the security level of private data.

Tier III:
Rainbow table is a resource used for hacking the cryptographic hash functions to discover plaintext passwords or singly-hashed passwords by using a pre-computed authentification database. Hackers simply look up the authentification database for the singly-hashed password. If a match is found, hacker could reverse the password back to the plaintext. Since all possible combinations of characters are limited (although so many of them) and all hash functions are open-source, it turns out to be possible for rainbow table to hack password simply by brute force.
Password salting is a technique to protect the plaintext password or singly-hashed password from being reverse-engineered by hackers who might breach the environment. Password salting is realized simply by adding 32 characters or more into the password then hashing it. By adding additional characters, it makes the hashing result unpredictable or too complicated to be pre-computed by rainbow tables. In order to make password more secure, password salting is often accompanied by iterative hashing.
Interative hashing is the technique to protect password from hacking by hashing the password multiple times, often more than hundreds of times. This technique breaks the rainbow table by largely increasing the unpredictability of password after hashing. That is, the computation becomes way more complicated, the rainbow table has no way to pre-compute all possible combinations after hundreds of hashing.