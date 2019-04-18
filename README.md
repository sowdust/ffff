# FFFF - FFFF Finds Facebook Friends

Build a relationship graph of a target user Facebook friendships.

Partially reconstruct hidden friend lists by using the "mutual friends" functionality. Requires knowing at least another account having at least one mutual friend with the target.


## Disclaimer

Scraping without written permission is against Facebook [Terms of Services](https://www.facebook.com/apps/site_scraping_tos_terms.php).


## About

Facebook offers a function to list some friends two accounts have in common, called "mutual friends", if at least one of the accounts' lists is visible to the observer.
This function can be applied recursively over all mutual friends found, possibly yielding a larger set of friends. This way it is possible to partially reconstruct a hidden friend list.

It is also possible to keep track of the relationships between users along the way, by connecting them in a graph, assigning weights based on how many times a relationship has been observed during the procedure. In this way it is possible to attempt at identifying communities within the network.


## Limitations

The mutual friends functionality only works if at least one of the two users compared have their friend list public. 
Furthermore, Facebook limits the number of mutual friends that are shown. It seems that using different accounts sometimes lead to different results. It might be worth giving a try - maybe using accounts from different locations.


### Prerequisites

The script works in Python 3 with the libraries `selenium`, `argparse` and  `networkx`.

```pip3 install -r requirements.txt```

As of now it supports only Firefox webdriver. The [geckodriver executable](https://github.com/mozilla/geckodriver/releases) must be downloaded and stored locally.
Support for more webdrivers can be easily added if necessary - just ask!



## Usage

### Required information

##### TL;DR:

* Facebook user
* Facebook password
* Target account Facebook id
* One or more "pivot" account Facebook id (if target friend list is hidden)
* Path to the Geckodriver file


The script works with Facebook numeric account ids.
There are several ways to find out an account numeric id, including many online services such as [findmyfbid.com](https://findmyfbid.com/) or [graph.tips](http://graph.tips/).

A set of valid credentials (username and password) of a Facebook account to be used for collecting the results is required.

__Warning__: Accounts used for scraping are not allowed without permission, and can therefore be locked by Facebook anti-scraping mechanisms.
If you have a developer account, you could try using a [test account](https://developers.facebook.com/docs/apps/test-users/).

If the target account friend list is hidden, it is also necessary to provide the script at least one "pivot" account, ie.: one account that has their friend list public and at least one mutual friend with the target. A common way to find one is to look at users who reacted to content published by the target. Obviously the more pivots are provided, the better. If there are many pivots, they can be stored in a file, one per line. In order to see mutual friends between two users, visit the url `https://www.facebook.com/browse/mutual_friends/?uid=USER1&node=USER2`, where `USER1` and `USER2` are the two users' numeric ids. 

If the friend list is public, no pivots are necessary. Just provide the target account id also as a pivot.

It is also necessary to know the local path in which you have stored the geckodriver executable was placed. 

Some options (the facebook credentials and the the driver executables) can be hardcoded inside the script source code:
```
FB_USR = 'username@facebook.com'
FB_PWD = 'password'
GECKO_PATH = 'C:\geckodriver.exe'  
```
Otherwise, they can be provided as a command line option.

Pivot accounts can be provided either as a list of integers separated by a space via command line (with the option `--pivots`), or one per row in a file (`--pivots-file`).
A list of accounts to ignore as pivots can be provided as well (`--ignore-file`).

The session can be interrupted (Ctrl+C) and resumed at a later time. This is also possible in case an exception occurs during the program run (e.g.: a request timeout).

### Available options

```
usage: ffff.py [-h] [-fu USERNAME] [-fp PASSWORD] [-t TARGET]
               [-p PIVOT [PIVOT ...]] [-o OUTPUTFILE] [-g GRAPHFILE]
               [-P PIVOTSFILE] [-I IGNOREFILE] [-r SESSION] [-q]
               [-d EXECUTABLE]

Recursively build friends list of Facebook users by exploiting the "mutual
friends" utility.

optional arguments:
  -h, --help            show this help message and exit
  -fu USERNAME, --user USERNAME
                        Username of the Facebook account that will be used for
                        scraping
  -fp PASSWORD, --password PASSWORD
                        Username of the Facebook account that will be used for
                        scraping
  -t TARGET, --target TARGET
                        Numeric id of the target Facebook account
  -p PIVOT [PIVOT ...], --pivots PIVOT [PIVOT ...]
                        Numeric id(s) of the Facebook accounts known to have
                        mutual friends with the target. Their friends list
                        must be public. Can be a single value or a list of
                        values separated by a space.
  -o OUTPUTFILE, --output OUTPUTFILE
                        Specify where to store list of friends found in CSV
                        format
  -g GRAPHFILE, --graph-output GRAPHFILE
                        Specify where to store graph in GEXF (Graph Exchange
                        XML Format) format
  -P PIVOTSFILE, --pivots-file PIVOTSFILE
                        Load a list of Facebook ids to use as pivot accounts
                        from file PIVOTSFILE. Numeric ids must be one per
                        line. This option can be used together or in place of
                        --pivots.
  -I IGNOREFILE, --ignore-file IGNOREFILE
                        Load a list of Facebook ids NOT to use as pivot
                        accounts from file IGNOREFILE. Numeric ids must be one
                        per line.
  -r SESSION, --resume SESSION
                        Resume a previous session from file SESSION
  -q, --headless        Run browser in headless mode. No browser window will
                        be shown.
  -d EXECUTABLE, --driver-path EXECUTABLE
                        Path to geckodriver executable
```

### Examples

The following example usage tries to build a subset of the friends list of target account id "00000000", pivoting on account "00000001", and finally storing the results in CSV file "results.csv" and the Gephi graph file in "graph.gexf".

The account used for scraping is "myaccount@facebook.com", protected by the password "Passw0rd"

Adding the `-q` option makes the webdriver run in headless mode: no browser window should be shown.

In the example, the Windows geckodriver executable is stored in the current directory. Geckodriver executables can be downloaded from [Mozilla repository](https://github.com/mozilla/geckodriver/releases). If you are using Linux or Mac and have downloaded the geckodriver file in the current directory, use `--driver-path ./geckodriver`.

```
python3 ffff.py -fu myaccount@facebook.com -fp Passw0rd -t 00000000 -p 00000001 -o results.csv -g graph.gexf -q --driver-path geckodriver.exe 
```
The session can be stopped (Ctrl+C) and resumed at a later time:

```
^CSession stored to file session-00000000-20190221232552. Use "--resume session-00000000-20190221232552" to resume from here
```
The result, a list of friends of the target, is provided as a csv file in the form `account id, account name, account url`).

#### Other examples

Build the community graph of target user 111111111 with public friend list, showing the browser window (without using option `-q`). Geckodriver file is stored in `C:`:
```
python3 ffff.py -fu myaccount@facebook.com -fp Passw0rd -t 111111111 -p 111111111 --driver-path C:\geckodriver.exe 
```

Provide a file with a list of pivot accounts as well as a a file with a list of accounts not to be used as pivots if found among the target's friend. Files pivots.txt and ignore.txt must contain one Facebook id per line. Operating system is linux and the geckodriver executable is in the user's Desktop:
```
python3 ffff.py -fu myaccount@facebook.com -fp Passw0rd -t 12345678 -P pivots.txt -I ignore.txt -d /home/user/Desktop/geckodriver
```

Resume an old session (either terminated or interrupted), adding three new pivots to be processed:
```
python3 ffff.py -fu myaccount@facebook.com -fp Passw0rd --resume session-00000000-20190418122352 -p 111111111 222222222 333333333
```

## Output

The scripts produces three output files:

* one .csv file containing the list of friends found, in the form `account id, account name, account url`
* one .gexf file containing the annotated graph that can be opened using [Gephi](https://gephi.org/)
* one session file that can be used to resume the work (e.g.: in case more pivots are found at a later time)


## License

This code is ffffree


