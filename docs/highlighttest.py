#!/usr/bin/env python

names = ["apl", "arduino", "basemake", "bash", "sh", "ksh", "zsh", "csh", "fish", "shell", "coffeescript", "cu", "ecl", "elixir", "fancy", "felix", "flo", "fortran", "freefem", "gsql", "icon", "idl", "pan"]

HF = r"""

    # a single (process) node graph pattern
    proc1 = GET process FROM stixshifter://edp1
            WHERE name = "powershell.exe" AND pid = 1234
              AND binary_ref.name = "powershell.exe"
            LAST 5 MIN

    # a single (network-traffic) node graph pattern
    # this pattern is equivalent to `dst_port IN (80, 443)`
    netflow1 = GET network-traffic FROM stixshifter://gateway1
               WHERE dst_port = 80 OR dst_port = 443
                 AND dst_ref.value = "192.168.1.1"
               START 2022-01-01T00:00:00Z STOP 2022-01-02T00:00:00Z

    # a single (file) node graph pattern
    minikatz = GET file FROM stixshifter://edp1
               WHERE name = "C:\ProgramData\p.exe"
                  OR hashes.MD5 IN ( "1a4fe4413a92d478625d97b7df1bd0cf"
                                   , "b6ff8f31007a3629a3c4be8999001ec9"
                                   , "e8994399f1656e58f72443b8861ce5d1"
                                   , "9ae602fddb5d2f9b63c5eb6aad0a2612"
                                   )
               START "2022-01-01T00:00:00Z" STOP t"2022-01-02T00:00:00Z"

    # a single (user-account) node graph pattern
    users = GET user-account FROM stixshifter://authlogs
            WHERE (user_id = 1001 AND account_login = "Tracy")
               OR  user_id = 0
               OR (user_id = 1003 AND is_privileged = true)
               OR (account_login = "JJ" AND is_privileged = true)

    APPLY python://sef ON users

    u = users WHERE name = "asdf"


"""

with open("highlighttest.rst", "w") as ht:
    ht.write("""==============
Highlight Test
==============

""")
    for name in names:
        header = f"{name}\n\n.. code-block:: {name}"
        ht.write(header)
        ht.write(HF)
