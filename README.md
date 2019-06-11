# FFFF - FFFF Finds Facebook Friends

Build a relationship graph of a target user Facebook friendships.

Partially reconstruct hidden friendlists by using the "mutual friends" functionality. Requires knowing at least another account having at least one mutual friend with the target.

The auxiliary script fint.py can retrieve users who have interacted with a given target profile and can be used as an input to ffff.py

[Here](https://techblog.mediaservice.net/2019/05/find-hidden-friends-and-community-for-any-facebook-user/?_thumbnail_id=479) is a detailed blog post about the tools, including a practical example.

## Disclaimer

Scraping without written permission is against Facebook [Terms of Services](https://www.facebook.com/apps/site_scraping_tos_terms.php): therefore you should not use any scraping tool without proper written authorization. All the information provided in this and related articles are for educational purposes only. The authors or are in no way responsible for any misuse of the information or the code provided.


## About

Facebook offers a function to list some friends two accounts have in common, called "mutual friends". It works only if at least one of the accounts' lists is visible to the observer.
In order to partially reconstruct a hidden friend list, this function can be applied recursively over all mutual friends found at each step.

It is also possible to keep track of the relationships between users along the way, by connecting them in a graph, assigning weights based on how many times a relationship has been observed during the procedure. In this way it is possible to identify communities within the network.


## Screenshots

![Running the program against a colleague profile](https://i.ibb.co/yQgcc5T/screenshot2.png)

![Displaying the colleagues friendships in Gephi](https://i.ibb.co/3rkpksr/screenshot.png)


## Limitations

The mutual friends functionality only works if at least one of the two users compared have their friendlists public. 
Furthermore, Facebook limits the number of mutual friends that are shown. It seems that using different accounts sometimes lead to different results. It might be worth giving a try - maybe using accounts from different locations.


## Installation

The script requires Python 3 and the libraries `selenium`, `argparse` and  `networkx`. 

You can download the repository as a zip file or clone it:

```git clone https://github.com/sowdust/ffff.git```

Install the requirements:

```pip3 install -r requirements.txt```

As of now the script supports only Firefox webdriver. The [geckodriver executable](https://github.com/mozilla/geckodriver/releases) must be downloaded and stored locally. I suggest you store it inside the ffff folder.
Support for more webdrivers can be easily added if necessary - just ask!


## Usage

### Required information

#### TL;DR:

To run the script ffff the following information is required:

* Valid Facebook credentials (user/password)
* Target account Facebook id
* One or more "pivot" account ids (if target friend list is hidden) - you can use fint.py for this 
* Path to the Geckodriver file

#### Instructions

The script works with Facebook numeric account ids.
There are several ways to find out an account numeric id, including many online services such as [findmyfbid.com](https://findmyfbid.com/) or [graph.tips](http://graph.tips/).

A set of valid credentials (username and password) of a Facebook account to be used for collecting the results is required.

__Warning__: Accounts used for scraping are not allowed without permission, and can therefore be locked by Facebook anti-scraping mechanisms.
If you have a developer account, you could try using a [test account](https://developers.facebook.com/docs/apps/test-users/).

If the target account friend list is hidden, it is also necessary to provide the script at least one "pivot" account, ie.: one account that has their friend list public and at least one mutual friend with the target.
A common way to find a suitable pivot account is to look at users who reacted to content published by the target.
Obviously the more pivots are provided, the better.
If there are many pivots, they can be stored in a file, one per line.
In order to check if mutual friends between two users are visible, visit the url `https://www.facebook.com/browse/mutual_friends/?uid=USER1&node=USER2`, where `USER1` and `USER2` are the two users' numeric ids. 

One way to find pivot accounts is to use the auxiliary script `fint.py`. This script will provide a list of users who have interacted with the target. 
Run `fint.py -h` to have a list of command line options. This script will produce a txt file with a list of potential pivots; this file can later be fed to ffff.py by using the `-P` (`--pivots-file`) option.

If the friend list is public, no pivots are necessary: just provide the target account id also as a pivot.

It is also necessary to know the local path in which you have stored the geckodriver executable. 

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
               [-P PIVOTSFILE] [-I IGNOREFILE] [-r SESSION] [-q] [-w]
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
  -w, --store-weights   Assign weights based on how many times a relationship
                        is observed.
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

#### Other examples

Use fint.py to find potential pivot accounts for target user 111111111, using the most recent 10 stories and 5 photos published, using a maximum of 100 comments and 1000 reactions: 
```
python fint.py -fu fbuser@mediaservice.net -fp fbpassword -d geckodriver.exe -t 111111111 -ls 10 -lp 5 -lc 100 -lr 1000
```

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

The scripts ffff.py produces three output files:

* one .csv file containing the list of friends found, in the form `account id, account name, account url`
* one .gexf file containing the annotated graph that can be opened using [Gephi](https://gephi.org/)
* one session file that can be used to resume the work (e.g.: in case more pivots are found at a later time)


The script fint.py produces two output files:
* one .txt file containing a list of account ids that can be used as a list of pivots for ffff
* one .csv file (optional) containing a list of potential pivots in the form `id,name,url`
It also prints out statistics on who are the users who have interacted the most.

## License

This code is ffffree

