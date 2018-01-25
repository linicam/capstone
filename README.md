# capstone

This is a simple worm used for implementing "two-stage reconnaissance worm"[1] and the way to counter it, only the spreadhead part, taking advantages of weak password.

For the network configuration, see Meerah and Mostafa's paper[2].

We found that the host used for redirecting the requests (H in Fig 2 in the paper) is not necessary.

[1] "Honeypot Detection in Advanced Botnet Attacks", Ping Wang, Lei Wu, Ryan Cunningham, and Cliff C. Zou, 2010.
[2] "Avoinding honeypot detection in peer-to-peer botnets", Meerah M. Al-Hakbani and Mostafa H. Dahshan, 2015.
